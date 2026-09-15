---
title: "Marvel vs. Random, Small-World and Scale-Free Networks"
date: "2026-09-11"
author: "Robin, Giosué, Sébastien"
readTime: "3 min read"
tags: ["marvel", "network-models", "small-world", "heavy-tail", "complex-networks"]
summary: "We compare the Marvel character network edge-by-edge with an Erdős–Rényi random graph, a Watts–Strogatz small-world network, and a Barabási–Albert scale-free network built with identical node and edge counts."
wikilinks: ["exploring-degrees-marvel-dataset"]
---

In [[exploring-degrees-marvel-dataset|the first article]] we looked at the **degrees** of the Marvel character network: a heavy-tailed in-degree distribution, a dominant Spider-Man hub, and a small world of islands. But a degree distribution alone does not tell us whether the network is *special*. To know what is exotic about a real network, we need **null models** — synthetic networks built to be "normal" under some rule, so we can ask: *does the Marvel network look like one of them?*

## The phase transition: when a random network wakes up

Drag the slider below and watch a random network come alive. At low average degree everything is tiny fragments. Then — suddenly — a **giant connected component** swallows most of the nodes. This is the Erdos–Renyi phase transition, and it defines what "pure randomness" looks like.

<iframe src="assets/applets/phase-transition.html" width="100%" height="550" frameborder="0" style="border: 1px solid var(--border-subtle); border-radius: 12px; overflow: hidden; background: var(--bg-surface); margin: 1.5rem 0;" title="Interactive: the birth of the giant component"></iframe>

Set N = 303 (the number of Marvel characters) and drag the average degree to **9.47** — Marvel's actual value. At that density a random graph is *fully connected*: every character reaches every other in a few hops. Marvel, with its 19 disconnected components, does not behave like pure randomness.

---

## From directed to undirected

The Marvel dataset is directed (303 nodes, 1784 edges). The null models below work on the **undirected projection**: an edge exists if *at least one* article links to the other. This collapses the 1784 directed links into **1434 unique undirected edges**.

- **Nodes:** N = 303 | **Edges:** M = 1434 | **Mean degree:** k = 2M/N = 9.47

---

## Three null models and a control

**Erdos–Renyi G(303, 1434)** — pick 1434 edges uniformly at random among all possible pairs. No structure whatsoever.

**Watts–Strogatz WS(303, k=10, p=0.2)** — a ring where each node connects to its 10 nearest neighbours, then each edge is rewired with probability 0.2. High clustering plus long-range shortcuts.

**Barabasi–Albert BA(303, m=5)** — grow the graph node by node; each newcomer attaches to 5 existing nodes chosen proportionally to their current degree. Produces hubs and a heavy-tailed distribution.

**Degree-preserved swap** — shuffle the endpoints of two edges at a time, keeping every node's degree exactly as in Marvel:

A-B, C-D --> A-D, C-B

This isolates the question we care about: *does Marvel's clustering survive when we scramble who links to whom, keeping only the hub structure?*

---

## Head-to-head comparison

<iframe src="assets/applets/network-models-comparison.html" width="100%" height="640" frameborder="0" style="border: 1px solid var(--border-subtle); border-radius: 12px; overflow: hidden; background: var(--bg-surface); margin: 1.5rem 0;" title="Marvel network vs Erdos-Renyi, Watts-Strogatz and Barabasi-Albert null models"></iframe>

The table summarises the key metrics:

| Metric | Marvel | Erdos-Renyi | Watts-Strogatz | Barabasi-Albert | Degree-preserved |
| :--- | ---: | ---: | ---: | ---: | ---: |
| Nodes N | 303 | 303 | 303 | 303 | 303 |
| Edges M | 1434 | 1434 | 1434 | 1434 | 1434 |
| **Avg. clustering C** | **0.308** | 0.030 | 0.343 | 0.106 | 0.175 |
| **Avg. path length L** | **2.67** | 2.77 | 3.21 | 2.60 | 2.59 |
| Diameter | 6 | 5 | 5 | 4 | 5 |
| Components | 19 | 1 | 1 | 1 | 19 |
| Giant component | 277 (91%) | 303 (100%) | 303 (100%) | 303 (100%) | 277 (91%) |
| Max degree | 106 | 21 | 16 | 76 | 106 |

Three things stand out:

- **Marvel is small-world.** Clustering is 10x higher than Erdos-Renyi (C = 0.31 vs 0.03) and nearly identical to Watts-Strogatz (C = 0.34), while average path length is actually *shorter* (L = 2.67 vs 2.77).

- **Hubs erase distances.** Spider-Man alone connects to 106 characters. Only the Barabasi-Albert model comes close (k_max = 76), and it achieves the shortest average path (L = 2.60).

- **Marvel is fragmented.** 19 connected components, including 17 isolated characters. No classical null model reproduces this — they all stay fully connected at this density.

The degree distribution is heavy-tailed, not Poisson. We deliberately say *heavy-tailed* rather than *scale-free*: a power law is only one particular kind of heavy tail, and proving a strict power law from 303 nodes would require far more data.

---

## What makes the Marvel network model-resistant?

Marvel combines the **short paths of a random graph**, the **clustering of a small-world ring**, and the **heavy-tailed, hub-dominated degrees** that scale-free models were designed to explain. No single classical model captures all three features at once. Add thematic silos (X-Men cluster with X-Men) and disconnected islands, and it becomes clear: *the real network borrows the best of all three models — plus things none of them can produce.*
