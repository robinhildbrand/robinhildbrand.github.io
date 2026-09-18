---
title: "Marvel Network Games"
date: "2026-09-18"
author: "Robin, Giosué, Sébastien"
readTime: "2 min read"
tags: ["marvel", "cliques", "centrality", "paths", "mixing", "complex-networks"]
summary: "Two explorable games on the real Marvel network: spot the intruder in a clique, then choose an infection source and compare centrality rankings."
layout: full
wikilinks: ["exploring-degrees-marvel-dataset", "network-models-marvel-comparison"]
---

In [[exploring-degrees-marvel-dataset|the Marvel network]], characters form cliques, bridges, and long paths. These two small games turn those structures into something you can test yourself.

### Spot the intruder

In every squad, one hero is not friends with everyone. Find them. Tap a tile to accuse.

<iframe src="assets/applets/spot-the-intruder.html" width="100%" height="640" frameborder="0" style="border: 1px solid var(--border-subtle); border-radius: 12px; overflow: hidden; background: var(--bg-surface); margin: 1.5rem 0;" title="Interactive: find the hero who is not a clique member"></iframe>

### Choose the infection source

A spreading disease moves across one edge per round: every infected character passes it to all of their neighbors at the same time. Choose the source that reaches every character in the giant component as fast as possible.

<iframe src="assets/applets/infection-source.html" width="100%" height="760" frameborder="0" style="border: 1px solid var(--border-subtle); border-radius: 12px; overflow: hidden; background: var(--bg-surface); margin: 1.5rem 0;" title="Interactive: choose the best infection source in the Marvel network"></iframe>

Set the transmission probability **p** and run the same source more than once. At **p = 1**, every exposed edge transmits and the result is the graph distance from the source to the furthest character. At lower **p**, each attempted transmission can fail, so the same source can produce a different result on each run. A stalled spread is part of the experiment, not a bug.

The ranking panel gives you three different clues:

- **Closeness** is the best first clue when transmission is reliable. It rewards short average paths to the rest of the component.
- **Betweenness** matters when the network has bottlenecks. A bridge can connect regions that a high-degree hub cannot reach efficiently once one route fails.
- **Eigenvector centrality** matters when influence tends to flow through already important neighborhoods. It favors well-connected characters, not necessarily the best all-network starting point.

The main conclusion is probabilistic: centrality rankings suggest good sources, but they do not guarantee the fastest outbreak. At low **p**, repeated trials and the chance of reaching everyone matter more than one lucky run. This simulation shows how a structural notion of importance changes when spreading is uncertain; it does not model recovery, repeated exposure, or time-varying contacts.

Three questions to keep in mind:

- Does the fastest source top all three rankings?
- Does a high-degree hub always beat a quieter bridge?
- How much does the answer change when “importance” means reach, brokerage, or prestige?