// Maya Workflow Kit site: the shelf (tabs swap the viewport clip, caption and Channel Box facts) and the Maya | Blender
// switch. Content stays readable without JavaScript: the first tab's facts are filled from the JSON on load.
(() => {
  const data = JSON.parse(document.getElementById("workflows-data").textContent);
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const tabs = [...document.querySelectorAll(".shelf__tab")];
  const panel = document.getElementById("panel");
  const viewport = panel.querySelector(".viewport");
  const video = panel.querySelector("[data-video]");
  const still = panel.querySelector("[data-still]");
  const caption = panel.querySelector("[data-caption]");
  const node = panel.querySelector("[data-node]");
  const facts = panel.querySelector("[data-facts]");
  const credit = panel.querySelector("[data-credit]");

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

  function setMedia(wf) {
    if (wf.video) {
      still.hidden = true;
      video.hidden = false;
      video.poster = `media/${wf.video}.jpg`;
      video.replaceChildren(...["webm", "mp4"].map((ext) => {
        const s = document.createElement("source");
        s.src = `media/${wf.video}.${ext}`; s.type = `video/${ext}`;
        return s;
      }));
      video.load();
      playIfVisible();
    } else {
      video.pause();
      video.hidden = true;
      still.hidden = false;
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
    const swap = () => { fillFacts(wf); setMedia(wf); viewport.classList.remove("is-swapping"); };
    if (reduceMotion.matches) { swap(); return; }
    viewport.classList.add("is-swapping");
    setTimeout(swap, 180);
  }

  tabs.forEach((tab, i) => {
    tab.addEventListener("click", () => select(tab, false));
    tab.addEventListener("keydown", (e) => {
      const k = e.key;
      let j = null;
      if (k === "ArrowRight") j = (i + 1) % tabs.length;
      else if (k === "ArrowLeft") j = (i - 1 + tabs.length) % tabs.length;
      else if (k === "Home") j = 0;
      else if (k === "End") j = tabs.length - 1;
      if (j !== null) { e.preventDefault(); select(tabs[j], true); }
    });
  });
  // 1 – 6 pick a shelf tab while the shelf is on screen (not while typing)
  document.addEventListener("keydown", (e) => {
    if (e.altKey || e.ctrlKey || e.metaKey || /input|textarea|select/i.test(e.target.tagName)) return;
    const n = Number(e.key);
    if (n >= 1 && n <= tabs.length && shelfVisible) select(tabs[n - 1], true);
  });

  // play the viewport clip only while it is on screen (preload none until then)
  let shelfVisible = false;
  function playIfVisible() {
    if (!shelfVisible || video.hidden || reduceMotion.matches) return;
    const p = video.play();
    if (p) p.catch(() => {});
  }
  new IntersectionObserver(([entry]) => {
    shelfVisible = entry.isIntersecting;
    if (shelfVisible) playIfVisible(); else video.pause();
  }, { threshold: 0.35 }).observe(viewport);

  fillFacts(data.hotbox);

  // Maya | Blender switch
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
