// Maya Workflow Kit site: the shelf (tabs swap the viewport clip, caption and Channel Box facts), the clip's
// play / pause button, the Maya | Blender switch and the scroll-fade hints of the menu bar and the shelf.
// Without JavaScript the first tab's poster, clip sources and markup stay readable; the Channel Box facts are
// filled from the JSON here.
(() => {
  const data = JSON.parse(document.getElementById("workflows-data").textContent);
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const small = window.matchMedia("(max-width: 760px)");
  const coarse = window.matchMedia("(pointer: coarse)");
  const saveData = !!(navigator.connection && navigator.connection.saveData);
  const tabs = [...document.querySelectorAll(".shelf__tab")];
  const panel = document.getElementById("panel");
  const viewport = panel.querySelector(".viewport");
  const video = panel.querySelector("[data-video]");
  const still = panel.querySelector("[data-still]");
  const caption = panel.querySelector("[data-caption]");
  const node = panel.querySelector("[data-node]");
  const facts = panel.querySelector("[data-facts]");
  const credit = panel.querySelector("[data-credit]");
  const playBtn = panel.querySelector("[data-play]");

  // ---------------------------------------------------------------- the clip: what shows, what is attached, intent
  let clip = video.dataset.clip;                       // the clip the viewport shows (at least its poster)
  let loaded = small.matches ? null : clip;            // the clip whose sources are attached (phones get the 960 px file)
  let wantsPlay = !reduceMotion.matches && !saveData;  // the visitor's intent: play unless they asked for less motion / data
  let shelfVisible = false;
  let armed = false;                                   // autoplay may start: desktops once idle, phones after a first gesture

  const posterOf = (name) => `media/${name}${small.matches ? "-640" : ""}.webp`;
  const sourcesOf = (name) => [[`media/${name}${small.matches ? "-540" : ""}.webm`, "video/webm"],
                               [`media/${name}.mp4`, "video/mp4"]];

  function attach(name) {
    if (loaded === name) return;
    video.replaceChildren(...sourcesOf(name).map(([src, type]) => Object.assign(document.createElement("source"), { src, type })));
    video.load();
    loaded = name;
  }
  function detach() {               // poster only, nothing on the wire
    if (loaded === null) return;
    video.replaceChildren();
    video.load();
    loaded = null;
  }
  function play() {
    attach(clip);
    const p = video.play();
    if (p) p.catch(() => {});
  }
  function maybePlay() {
    if (wantsPlay && armed && shelfVisible && !video.hidden) play();
  }
  function syncButton() {
    const playing = !video.paused && !video.ended;
    viewport.classList.toggle("is-playing", playing);
    playBtn.setAttribute("aria-label", playing ? "Pause the clip" : "Play the clip");
  }
  video.addEventListener("play", syncButton);
  video.addEventListener("pause", syncButton);
  playBtn.addEventListener("click", () => {
    wantsPlay = video.paused;
    if (wantsPlay) play(); else video.pause();
  });

  // autoplay waits for the page to be idle on a desktop, and for the first scroll / touch / key on a phone
  if (small.matches || coarse.matches) {
    const events = ["scroll", "pointerdown", "touchstart", "keydown"];
    const arm = () => { armed = true; events.forEach((t) => removeEventListener(t, arm)); maybePlay(); };
    events.forEach((t) => addEventListener(t, arm, { passive: true }));
  } else if ("requestIdleCallback" in window) {
    requestIdleCallback(() => { armed = true; maybePlay(); }, { timeout: 2000 });
  } else {
    setTimeout(() => { armed = true; maybePlay(); }, 800);
  }
  // play only while the viewport is on screen; coming back resumes the visitor's choice
  new IntersectionObserver(([entry]) => {
    shelfVisible = entry.isIntersecting;
    if (shelfVisible) maybePlay(); else video.pause();
  }, { threshold: 0.35 }).observe(viewport);

  // ---------------------------------------------------------------- the shelf
  function fillFacts(wf) {
    facts.replaceChildren(...wf.facts.flatMap(([k, v]) => {
      const dt = document.createElement("dt"); dt.textContent = k;
      const dd = document.createElement("dd"); dd.textContent = v;
      return [dt, dd];
    }));
    node.textContent = wf.node;
    credit.textContent = wf.credit;
    caption.textContent = wf.caption;
  }

  function setMedia(wf, label) {
    if (wf.video) {
      still.hidden = true;
      video.hidden = false;
      viewport.classList.remove("is-still");
      video.pause();
      clip = wf.video;
      detach();                                   // back to the poster; sources arrive when the clip plays
      video.poster = posterOf(clip);
      video.setAttribute("aria-label", `${label} demo clip`);
      maybePlay();
    } else {
      video.pause();
      video.hidden = true;
      still.hidden = false;
      viewport.classList.add("is-still");
      still.srcset = `media/shot-${wf.still}-800.webp 800w, media/shot-${wf.still}.webp 1600w`;
      still.sizes = "(min-width: 1100px) 50vw, 100vw";
      still.src = `media/shot-${wf.still}.jpg`;
      still.alt = wf.alt || "";
    }
  }

  function select(tab, focus) {
    const wf = data[tab.dataset.wf];
    tabs.forEach((t) => {
      const on = t === tab;
      t.setAttribute("aria-selected", String(on));
      t.tabIndex = on ? 0 : -1;
    });
    panel.setAttribute("aria-labelledby", tab.id);
    if (focus) tab.focus();
    tab.scrollIntoView({ block: "nearest", inline: "nearest", behavior: reduceMotion.matches ? "auto" : "smooth" });
    const swap = () => { fillFacts(wf); setMedia(wf, tab.textContent.trim()); viewport.classList.remove("is-swapping"); };
    if (reduceMotion.matches) { swap(); return; }
    viewport.classList.add("is-swapping");
    setTimeout(swap, 180);
  }

  tabs.forEach((tab, i) => {
    tab.addEventListener("click", () => select(tab, false));
    // arrow keys move the focus along the shelf; Enter / Space (the button's click) picks the tab
    tab.addEventListener("keydown", (e) => {
      const k = e.key;
      let j = null;
      if (k === "ArrowRight") j = (i + 1) % tabs.length;
      else if (k === "ArrowLeft") j = (i - 1 + tabs.length) % tabs.length;
      else if (k === "Home") j = 0;
      else if (k === "End") j = tabs.length - 1;
      if (j !== null) { e.preventDefault(); tabs[j].focus(); }
    });
  });
  // 1 – 6 pick a shelf tab while the shelf is on screen (not while typing)
  document.addEventListener("keydown", (e) => {
    if (e.altKey || e.ctrlKey || e.metaKey || /input|textarea|select/i.test(e.target.tagName)) return;
    const n = Number(e.key);
    if (n >= 1 && n <= tabs.length && shelfVisible) select(tabs[n - 1], true);
  });

  fillFacts(data.hotbox);

  // ---------------------------------------------------------------- the tour: its poster loads when the band comes near
  const tour = document.querySelector(".tour video[data-poster]");
  if (tour) {
    new IntersectionObserver(([entry], io) => {
      if (entry.isIntersecting) { tour.poster = tour.dataset.poster; io.disconnect(); }
    }, { rootMargin: "400px 0px" }).observe(tour);
  }

  // ---------------------------------------------------------------- the two horizontal scrollers fade the hidden edge
  function fades(el) {
    const max = el.scrollWidth - el.clientWidth;
    const x = el.scrollLeft;
    el.dataset.fade = max <= 1 ? "" : x <= 1 ? "r" : x >= max - 1 ? "l" : "lr";
  }
  document.querySelectorAll(".menubar nav, .shelf").forEach((el) => {
    el.addEventListener("scroll", () => fades(el), { passive: true });
    new ResizeObserver(() => requestAnimationFrame(() => fades(el))).observe(el);
  });

  // ---------------------------------------------------------------- Maya | Blender switch
  const opts = [...document.querySelectorAll(".switcher__opt")];
  const shots = [...document.querySelectorAll("[data-mode-shot]")];
  const note = document.querySelector("[data-mode-note]");
  const notes = {
    maya: "Maya mode — same file, Maya layout and keys.",
    blender: "Plain Blender — what you have after one click on Blender, or before you choose Maya.",
  };
  opts.forEach((b) => b.addEventListener("click", () => {
    const mode = b.dataset.mode;
    opts.forEach((o) => o.setAttribute("aria-pressed", String(o === b)));
    shots.forEach((s) => { s.hidden = s.dataset.modeShot !== mode; });
    note.textContent = notes[mode];
  }));
})();
