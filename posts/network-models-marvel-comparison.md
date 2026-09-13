---
title: "Marvel vs. Random, Small-World and Scale-Free Networks"
date: "2026-09-11"
author: "Robin, Giosué, Sébastien"
readTime: "7 min read"
tags: ["marvel", "network-models", "small-world", "scale-free", "complex-networks"]
summary: "We compare the Marvel character network edge-by-edge with an Erdős–Rényi random graph, a Watts–Strogatz small-world network, and a Barabási–Albert scale-free network built with identical node and edge counts."
wikilinks: ["exploring-degrees-marvel-dataset"]
---

In [[exploring-degrees-marvel-dataset|the first article]] we dissected the **degrees** of the Marvel character network: a heavy-tailed in-degree distribution, a dominant Spider-Man hub, and a small world of islands. But a degree distribution alone does not tell us whether the network is *special*. To know what is exotic about a real network, we need **null models** — synthetic networks that are built to be "normal" under some rule, so we can ask: *does the Marvel network look like one of them?*

This week we generate three classical null models with the **same number of nodes and edges** as the Marvel network and compare average clustering, path lengths, connectivity, and the degree distributions:

- 🎲 **Erdős–Rényi** `G(N, M)` — a purely random graph,
- 🌀 **Watts–Strogatz** — a small-world ring with shortcuts,
- 📈 **Barabási–Albert** — a scale-free graph grown by preferential attachment.

---

## From directed to undirected

The Marvel dataset is a **directed** graph (303 nodes, 1784 edges). The three null models above are classically defined on **undirected** graphs. We therefore compare all networks on their **undirected projection**, where an edge exists between two characters if *at least one* article links to the other. This collapses the 1784 directed links into **1434 unique undirected edges**.

- **Nodes:** $N = 303$
- **Edges:** $M = 1434$
- **Mean degree:** $\langle k \rangle = 2M/N \approx 9.47$

Every synthetic network below is generated with exactly these $N$ and $M$, using a fixed random seed so the results are reproducible.

---

## The three null models

### 1. Erdős–Rényi random graph, $G(303, 1434)$

Pick $M$ distinct edges uniformly at random among the $\binom{N}{2}$ possible pairs. Nothing else. This is the statistical baseline: **no structure whatsoever**. If Marvel deviates strongly from this random baseline, it must have *organised* structure.

### 2. Watts–Strogatz small-world, $\text{WS}(303, k{=}10, p{=}0.2)$

Start from a **ring** where each node attaches to its 10 nearest neighbours ($k = 10$), then **rewire** each edge with probability $p = 0.2$. For moderate $p$ the graph keeps the ring's high clustering but gains long-range shortcuts that collapse distances — the celebrated *small-world* signature. We trim a few random edges afterwards to hit exactly $M = 1434$.

### 3. Barabási–Albert scale-free, $\text{BA}(303, m{=}5)$

Grow the graph node by node; each newcomer attaches to $m = 5$ existing nodes chosen **proportionally to their current degree** (rich-get-richer). This produces hubs and a degree distribution that follows a power law, $P(k) \propto k^{-\gamma}$ with $\gamma \approx 3$. The raw output has $5 \cdot (303-5) = 1490$ edges, so we remove a few random edges to match $M = 1434$.

---

## Head-to-head comparison

<iframe src="assets/applets/network-models-comparison.html" width="100%" height="640" frameborder="0" style="border: 1px solid var(--border-subtle); border-radius: 12px; overflow: hidden; background: var(--bg-surface); margin: 1.5rem 0;" title="Marvel network vs Erdős–Rényi, Watts–Strogatz and Barabási–Albert null models"></iframe>

The applet shows the four degree distributions on a log–log scale and lets you toggle networks on and off (the **Legend** toggle in the toolbar hides the color legend). Switch to the **Topology Metrics** tab for the average clustering and path-length comparison.

---

## Interpretation of the metrics

| Metric | Marvel | Erdős–Rényi | Watts–Strogatz | Barabási–Albert |
| :--- | ---: | ---: | ---: | ---: |
| Nodes $N$ | 303 | 303 | 303 | 303 |
| Edges $M$ | 1434 | 1434 | 1434 | 1434 |
| Mean degree $\langle k \rangle$ | 9.47 | 9.47 | 9.47 | 9.47 |
| **Average clustering $C$** | **0.308** | 0.030 | 0.343 | 0.106 |
| **Avg. path length $L$** | **2.67** | 2.77 | 3.21 | 2.60 |
| Diameter | 6 | 5 | 5 | 4 |
| Connected components | 19 | 1 | 1 | 1 |
| Giant component size | 277 (91.4%) | 303 (100%) | 303 (100%) | 303 (100%) |
| Max degree $k_{max}$ | 106 | 21 | 16 | 76 |
| Degree assortativity | −0.10 | −0.02 | −0.02 | −0.12 |

The story is sharp:

- **High clustering, random distances — Marvel is small-world.** Its clustering $C \approx 0.31$ is **ten times larger** than the purely random Erdős–Rényi graph ($C \approx 0.03$) and almost identical to the Watts–Strogatz network ($C \approx 0.34$). Yet its average shortest path $L \approx 2.67$ is *shorter* than the random graph ($L \approx 2.77$). Marvel behaves like a Watts–Strogatz small-world with even better shortcuts.

- **Hubs that erase small-world distances.** The distance collapse comes from extreme hubs: Spider-Man alone connects to 106 other characters. The Barabási–Albert model is the only one that reproduces such hubs ($k_{max} = 76$) together with the shortest mean path ($L \approx 2.60$). Marvel's $k_{max} = 106$ dwarfs even the scale-free model's.

- **Marvel is not a single giant component.** Uniquely among the four, Marvel **fragments into 19 components** — the two real "islands" (277 and 9 nodes) from last week plus 17 isolates. Random graphs, Watts–Strogatz rings and even BA networks stay connected at this density. This is a genuine *modelling failure*: real networks can have disconnected, thematically isolated clusters.

- **The degree distribution is scale-free, not Poisson.** On the log–log plot the Marvel distribution tails off like a power law — the signature of a Barabási–Albert network — while the Erdős–Rényi distribution collapses like a narrow Poisson bell around $\langle k \rangle$.

In short: **Marvel is a small-world, scale-free network with a random-graph-like distance backbone** — but with disconnected islands that no classical null model produces.

---

## Reproducing the analysis

```python
import networkx as nx
import random

random.seed(42)

# Undirected projection of the directed Marvel network. Nodes come from the
# nodes file (17 of them are isolates with no edges and must be added by hand).
G_marvel = nx.Graph()
with open("week1_nodes.tsv") as f:
    for line in f:
        if line.startswith("#") or not line.strip():
            continue
        node = line.split("\t")[0]
        if node != "node_id":               # skip header
            G_marvel.add_node(node)
G_marvel.add_edges_from(
    (u, v)
    for u, v in nx.read_edgelist("week1_edges.tsv", comments="#", nodetype=str).edges()
    if u != v
)

N = G_marvel.number_of_nodes()   # 303
M = G_marvel.number_of_edges()   # 1434

# 1. Erdős–Rényi G(N, M): exactly M random edges
G_er = nx.gnm_random_graph(N, M, seed=42)

# 2. Watts–Strogatz ring, k=10, rewiring p=0.2 — trim to M edges
G_ws = nx.watts_strogatz_graph(N, k=10, p=0.2, seed=42)
G_ws.remove_edges_from(random.sample(list(G_ws.edges()), G_ws.number_of_edges() - M))

# 3. Barabási–Albert, m=5 — trim to M edges
G_ba = nx.barabasi_albert_graph(N, m=5, seed=42)
G_ba.remove_edges_from(random.sample(list(G_ba.edges()), G_ba.number_of_edges() - M))

def metrics(G):
    gc = G.subgraph(max(nx.connected_components(G), key=len))
    return {
        "N": G.number_of_nodes(),
        "M": G.number_of_edges(),
        "clustering": round(nx.average_clustering(G), 3),
        "avg_path": round(nx.average_shortest_path_length(gc), 3),
        "diameter": nx.diameter(gc),
        "components": nx.number_connected_components(G),
        "giant_frac": round(len(gc) / G.number_of_nodes(), 3),
        "max_degree": max(dict(G.degree()).values()),
    }

for name, net in [("Marvel", G_marvel), ("Erdős–Rényi", G_er),
                  ("Watts–Strogatz", G_ws), ("Barabási–Albert", G_ba)]:
    print(f"{name:>14}: {metrics(net)}")
```

```
        Marvel: {'N': 303, 'M': 1434, 'clustering': 0.307, 'avg_path': 2.674, 'diameter': 6, 'components': 19, 'giant_frac': 0.914, 'max_degree': 106}
   Erdős–Rényi: {'N': 303, 'M': 1434, 'clustering': 0.03, 'avg_path': 2.771, 'diameter': 5, 'components': 1, 'giant_frac': 1.0, 'max_degree': 21}
Watts–Strogatz: {'N': 303, 'M': 1434, 'clustering': 0.343, 'avg_path': 3.206, 'diameter': 5, 'components': 1, 'giant_frac': 1.0, 'max_degree': 16}
Barabási–Albert: {'N': 303, 'M': 1434, 'clustering': 0.106, 'avg_path': 2.598, 'diameter': 4, 'components': 1, 'giant_frac': 1.0, 'max_degree': 76}
```

---

## What makes the Marvel network model-resistant?

Classical null models assume a **single generative rule**. The Marvel universe violates that assumption in three ways:

1. **Canon and editorial revisits** — characters reappear across decades of storylines, so their articles are written *and rewritten* to link to many others. No single random process reproduces that accumulated popularity.
2. **Theme silos** — X-Men characters cluster with X-Men characters, the Avengers with the Avengers. This community structure elevates clustering far above random expectations (and occasionally produces entirely disconnected islands).
3. **One dominant protagonist** — Spider-Man is codified in *hundreds* of articles through "appearances in" typologies, a mechanism closer to preferential attachment than to uniform randomness.

Because Marvel combines the **short paths of a random graph**, the **clustering of a small-world ring**, and the **heavy tails of a scale-free network**, no single one of the classical models wins — *the real network borrows the best of all three*.

---

Next week we will turn to **spectral properties** — eigenvalues of the adjacency and Laplacian matrices — which will let us separate communities and quantify exactly *how far* Marvel sits from each null model.