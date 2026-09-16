---
title: "Spot the Intruder"
date: "2026-09-18"
author: "Robin, Giosué, Sébastien"
readTime: "2 min read"
tags: ["marvel", "cliques", "centrality", "paths", "mixing", "complex-networks"]
summary: "A minigame on real Marvel cliques: ten squads, each hiding one hero who is not friends with the whole room. Spot them, then see who bridges, who drifts, and who is unreachable."
layout: full
wikilinks: ["exploring-degrees-marvel-dataset", "network-models-marvel-comparison"]
---

In [[exploring-degrees-marvel-dataset|the Marvel network]], a **clique** is a group where everyone knows everyone. Real cliques are rare — 917 in all, but only eight reach seven heroes or more. The ten squads on this page are some of the biggest. Each hides one hero who is *not* friends with the whole room. Spot the intruder.

<iframe src="assets/applets/spot-the-intruder.html" width="100%" height="640" frameborder="0" style="border: 1px solid var(--border-subtle); border-radius: 12px; overflow: hidden; background: var(--bg-surface); margin: 1.5rem 0;" title="Interactive: find the hero who is not a clique member"></iframe>

Every squad you meet is a real clique — and the biggest ones are all **teams**: the X-Men, the Midnight Sons, the monster squad, the Spider-Verse. Teamwork is homophily: heroes who already share a team keep linking to each other, far more than a random network would produce.

Three numbers behind the game:

- **Paths:** from Spider-Man, 106 heroes are 1 hop, 152 take 2, 18 take 3 — and 26 heroes cannot reach him at all.
- **Centrality:** remove Spider-Man and 5 heroes are cut off; the quiet bridge is **Black Widow**, who strands 3.
- **Mixing:** Ms. Marvel is named 11 times but links out once; Shamrock links out 8 times and is never named. Assortativity is r = -0.10.