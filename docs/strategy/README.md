# Product strategy (2026-10-26)

Why this folder exists: until step 217 the kit was built by matching Maya menus one to one. On 2026-10-26 the
maintainer asked to define first **who the kit is for, what Maya users actually want, and in what order to build**.
These documents are the research and the decisions from that day. They are working notes, mostly in Korean.

Read in this order (each summary is one page):

| Round | Question | Summary | Details |
|---|---|---|---|
| 1 | Who reacts to the kit, who is it for? | `SUMMARY_KO.md` | `STRATEGY.md`, `RESEARCH.md`, `UNKNOWNS.md`, `SURVEY.md` |
| – | Goals after the first decisions | `GOALS.md` | |
| 2 | Which Maya workflow area first (demand × gap × cost)? | `SUMMARY2_KO.md` | `IDENTITY.md`, `IDENTITY_RESEARCH.md` |
| 3 | Stress-test of round 2 (know-your-unknowns) + maintainer interview | `SUMMARY3_KO.md` | `VERIFY.md`, `INTERVIEW_QUESTIONS.md`, `DIRECTION.md` |
| 4 | Which Maya features do people use most, and what is the kit's state? | `SUMMARY4_KO.md` | `FEATURES.md`, `TOP40.md` |
| 5 | Is "animation-focused first (rigging, deform, NURBS curves)" right? Feature chains end to end | `SUMMARY5_KO.md` | `CHAINS.md`, `ANIM_FOCUS_VERDICT.md` |
| 6 | Maya 2026 reverse engineering of the animation chains, and how to attach each to Blender | `SUMMARY6_KO.md` | `ATTACH_PLAN.md` (specs stay in the private `research/`) |
| 7 | Seven design decisions (know-your-unknowns, with experiments) | `SUMMARY7_KO.md` | `DECISIONS7.md` |

## Decided so far (maintainer)
- Target users: Maya veterans doing personal / freelance work in Blender (P1), and people who use Maya at work and Blender at home (P2).
- English only. Tagline kept: "The whole Maya workflow in Blender, in one install".
- No more adding Maya menus / editors for their own sake; bugs first.
- The build order is decided by us, not by a survey (the survey is reference only).
- Survey gets the four order-check questions.

## Decided 2026-10-26 (round 7)
- Reference is Maya 2026 (no 2022 comparison). Controls = bone Custom Shapes; Z-up kept; rig FBX post-processing allowed; quaternion bones shown as Euler; one skinCluster per mesh; pick walk via controller tags then hidden bone collections; numeric weights capped at 2,000 on screen.

## Earlier open item
- Round 5 verdict: animation-focused first is right **on the condition** that the work joins the broken links between existing rigging / deform / animation features so one chain works end to end in Maya hands (confidence 70 %). Proposed order in `SUMMARY5_KO.md`.

Some sources were collected with search tools that were rate-limited on the day; each document marks facts vs. estimates.
