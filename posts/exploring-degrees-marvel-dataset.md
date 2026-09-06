---
title: "Exploring Degrees in the Marvel Dataset"
date: "2026-09-04"
author: "Robin, Giosué, Sébastien"
readTime: "8 min read"
tags: ["marvel", "network-analysis", "degree-distribution", "complex-networks"]
summary: "An empirical analysis of node degrees, in/out-degree asymmetries, power-law distributions, and central superhero hubs across the Wikipedia Marvel Comics network."
wikilinks: []
---

In complex network analysis, the most fundamental property of any node is its **degree**—the number of connections it maintains with other elements in the system. When dealing with directed real-world systems, such as hyperlink graphs between Wikipedia articles, this metric splits into two distinct structural signals: **in-degree** (how many other entities cite you) and **out-degree** (how many other entities you cite).

In this article, we explore the **Marvel Universe Superhero Network**, constructed from the Wikipedia category *Category:Marvel Comics superheroes*. By examining the connectivity patterns among 303 characters, we reveal structural asymmetries, power-law scaling behavior, and the characters who function as structural anchors of the comic universe.

> [!NOTE]
> The dataset is sourced from Wikipedia page links among characters listed in `Category:Marvel Comics superheroes`. A directed edge $(u, v)$ signifies that the Wikipedia page of character $u$ links directly to character $v$.

---

## 1. Network Topology & Global Summary Statistics

Let the Marvel network be represented as a directed graph $G = (V, E)$, where $V$ is the set of $N = 303$ superhero nodes and $E$ is the set of $M = 1,784$ directed edges.

The adjacency matrix $\mathbf{A} \in \{0, 1\}^{N \times N}$ satisfies:

$$A_{ij} = \begin{cases} 1 & \text{if } (i, j) \in E \\ 0 & \text{otherwise} \end{cases}$$

For any node $i \in V$, we define its **in-degree** $k_i^{\text{in}}$, **out-degree** $k_i^{\text{out}}$, and **total degree** $k_i$ as:

$$k_i^{\text{in}} = \sum_{j=1}^N A_{ji}, \quad k_i^{\text{out}} = \sum_{j=1}^N A_{ij}, \quad k_i = k_i^{\text{in}} + k_i^{\text{out}}$$

Since each directed edge contributes exactly one unit to the total in-degree sum and one unit to the total out-degree sum, the average in-degree and average out-degree are strictly identical:

$$\langle k^{\text{in}} \rangle = \langle k^{\text{out}} \rangle = \frac{M}{N} = \frac{1,784}{303} \approx 5.888$$

| Metric | Value | Interpretation |
| :--- | :--- | :--- |
| **Total Superheroes ($N$)** | 303 | Resolved character entities |
| **Directed Connections ($M$)** | 1,784 | Hyperlink citations between character articles |
| **Average In / Out Degree** | 5.89 | Average links into or out of a superhero page |
| **Median In-Degree** | 3 | Half the characters receive $\le 3$ incoming links |
| **Median Out-Degree** | 4 | Half the characters link to $\le 4$ other characters |
| **Reciprocity ($r$)** | 39.2% | Fraction of mutual edges ($u \to v$ and $v \to u$) |
| **Isolates** | 17 | Superheroes with 0 incoming and 0 outgoing edges |
| **Source Nodes ($k^{\text{in}} = 0$)** | 58 | Characters never referenced by any other character |
| **Sink Nodes ($k^{\text{out}} = 0$)** | 20 | Characters that cite no other superhero in the dataset |

> [!TIP]
> A reciprocity of **39.2%** is remarkably high for a web hyperlink network (the general web graph typically exhibits reciprocity below 15–20%). This reflects the deeply collaborative, crossover-heavy nature of Marvel editorial continuity: if Spider-Man appears prominently in Wolverine's story, Wolverine almost invariably appears in Spider-Man's lore.

---

## 2. In-Degree vs. Out-Degree: Prestige vs. Cross-Referencing

In information and social networks, **in-degree** corresponds to *authority, prominence, and cultural canon*, whereas **out-degree** reflects *reference density, encyclopedic detail, and team affiliations*.

### The Apex In-Degree Superheroes (Canonical Hubs)

The table below lists the top 10 superheroes ranked by incoming citations:

| Rank | Superhero | In-Degree ($k^{\text{in}}$) | % of All Characters Linking In |
| :---: | :--- | :---: | :---: |
| 1 | **Spider-Man** | **106** | **34.98%** |
| 2 | **Hulk** | 64 | 21.12% |
| 3 | **Wolverine** | 60 | 19.80% |
| 4 | **Doctor Strange** | 50 | 16.50% |
| 5 | **Deadpool** | 33 | 10.89% |
| 6 | **She-Hulk** | 29 | 9.57% |
| 7 | **Scarlet Witch** | 28 | 9.24% |
| 8 | **Black Panther** | 27 | 8.91% |
| 9 | **Cyclops** | 26 | 8.58% |
| 10 | **Luke Cage** | 25 | 8.25% |

**Spider-Man** is the undisputed gravitational center of the Marvel Universe. More than **one in every three superheroes** in the dataset explicitly cites Peter Parker on their Wikipedia page!

Following Spider-Man are Hulk ($k^{\text{in}} = 64$) and Wolverine ($k^{\text{in}} = 60$), forming the core triumvirate of Marvel's most ubiquitous heroes.

### The Apex Out-Degree Superheroes (Cross-Reference Hubs)

Conversely, out-degree highlights characters whose articles cross-reference many other heroes:

| Rank | Superhero | Out-Degree ($k^{\text{out}}$) | Primary Affiliation / Context |
| :---: | :--- | :---: | :--- |
| 1 | **Betsy Braddock (Psylocke)** | **28** | X-Men / Captain Britain Corps / Excalibur |
| 2 | **Cloak and Dagger** | 24 | Duo crossovers (Runaways, Spider-Man, X-Men) |
| 3 | **Adam Warlock** | 22 | Cosmic Marvel / Infinity Watch / Guardians |
| 4 | **Venom** | 21 | Symbiote crossovers & Spider-Man mythos |
| 5 | **She-Hulk** | 20 | Avengers / Fantastic Four / Legal lore |
| 6 | **U.S. Agent** | 20 | West Coast Avengers / Force Works |
| 7 | **Deadpool** | 19 | Merc with a Mouth (Fourth-wall crossovers) |
| 8 | **Rachel Summers** | 19 | Complex alternate future X-Men lineages |

Characters with high out-degree often sit at the intersection of sprawling sub-franchises (e.g., Betsy Braddock bridging the British Marvel lore and mutant teams, or Adam Warlock linking cosmic cosmic sagas with Earth-based heroes).

---

## 3. Interactive Superhero Core Subgraph

Below is an interactive force-directed graph illustrating the mutual interaction network between the **top 12 most connected superhero hubs**. 

You can drag nodes, zoom in/out, toggle physical forces, and cycle layouts using the controls in the top toolbar:

```graph
{
  "nodes": [
    { "id": "Spider-Man", "label": "Spider-Man (k=115)", "group": "superhero", "size": 26, "color": "#ef4444" },
    { "id": "Wolverine_(character)", "label": "Wolverine (k=77)", "group": "superhero", "size": 22, "color": "#eab308" },
    { "id": "Hulk", "label": "Hulk (k=74)", "group": "superhero", "size": 21, "color": "#22c55e" },
    { "id": "Doctor_Strange", "label": "Doctor Strange (k=67)", "group": "superhero", "size": 20, "color": "#a855f7" },
    { "id": "Deadpool", "label": "Deadpool (k=52)", "group": "superhero", "size": 18, "color": "#f43f5e" },
    { "id": "She-Hulk", "label": "She-Hulk (k=49)", "group": "superhero", "size": 17, "color": "#10b981" },
    { "id": "Scarlet_Witch", "label": "Scarlet Witch (k=42)", "group": "superhero", "size": 16, "color": "#f43f5e" },
    { "id": "Phoenix_Force", "label": "Phoenix (k=41)", "group": "superhero", "size": 16, "color": "#f97316" },
    { "id": "Black_Panther_(character)", "label": "Black Panther (k=38)", "group": "superhero", "size": 15, "color": "#6366f1" },
    { "id": "Emma_Frost", "label": "Emma Frost (k=38)", "group": "superhero", "size": 15, "color": "#38bdf8" },
    { "id": "Venom_(character)", "label": "Venom (k=38)", "group": "superhero", "size": 15, "color": "#06b6d4" },
    { "id": "Cyclops_(Marvel_Comics)", "label": "Cyclops (k=37)", "group": "superhero", "size": 15, "color": "#0284c7" }
  ],
  "links": [
    { "source": "Spider-Man", "target": "Hulk", "directed": true, "weight": 2.0 },
    { "source": "Spider-Man", "target": "Venom_(character)", "directed": true, "weight": 2.5 },
    { "source": "Hulk", "target": "Spider-Man", "directed": true, "weight": 2.0 },
    { "source": "Hulk", "target": "She-Hulk", "directed": true, "weight": 2.5 },
    { "source": "Hulk", "target": "Wolverine_(character)", "directed": true, "weight": 2.5 },
    { "source": "Hulk", "target": "Deadpool", "directed": true, "weight": 1.5 },
    { "source": "Wolverine_(character)", "target": "Spider-Man", "directed": true, "weight": 2.5 },
    { "source": "Wolverine_(character)", "target": "Hulk", "directed": true, "weight": 2.5 },
    { "source": "Wolverine_(character)", "target": "Cyclops_(Marvel_Comics)", "directed": true, "weight": 2.5 },
    { "source": "Wolverine_(character)", "target": "Deadpool", "directed": true, "weight": 2.0 },
    { "source": "Wolverine_(character)", "target": "Scarlet_Witch", "directed": true, "weight": 1.5 },
    { "source": "Wolverine_(character)", "target": "Phoenix_Force", "directed": true, "weight": 2.0 },
    { "source": "Wolverine_(character)", "target": "Venom_(character)", "directed": true, "weight": 1.5 },
    { "source": "Doctor_Strange", "target": "Spider-Man", "directed": true, "weight": 2.0 },
    { "source": "Doctor_Strange", "target": "Hulk", "directed": true, "weight": 2.0 },
    { "source": "Doctor_Strange", "target": "Scarlet_Witch", "directed": true, "weight": 2.5 },
    { "source": "Doctor_Strange", "target": "Deadpool", "directed": true, "weight": 1.5 },
    { "source": "She-Hulk", "target": "Hulk", "directed": true, "weight": 2.5 },
    { "source": "She-Hulk", "target": "Spider-Man", "directed": true, "weight": 2.0 },
    { "source": "She-Hulk", "target": "Doctor_Strange", "directed": true, "weight": 1.5 },
    { "source": "She-Hulk", "target": "Scarlet_Witch", "directed": true, "weight": 1.8 },
    { "source": "She-Hulk", "target": "Wolverine_(character)", "directed": true, "weight": 1.8 },
    { "source": "She-Hulk", "target": "Deadpool", "directed": true, "weight": 1.8 },
    { "source": "Deadpool", "target": "Spider-Man", "directed": true, "weight": 2.5 },
    { "source": "Deadpool", "target": "Wolverine_(character)", "directed": true, "weight": 2.5 },
    { "source": "Deadpool", "target": "Hulk", "directed": true, "weight": 1.5 },
    { "source": "Deadpool", "target": "She-Hulk", "directed": true, "weight": 1.8 },
    { "source": "Deadpool", "target": "Venom_(character)", "directed": true, "weight": 1.8 },
    { "source": "Cyclops_(Marvel_Comics)", "target": "Wolverine_(character)", "directed": true, "weight": 2.5 },
    { "source": "Cyclops_(Marvel_Comics)", "target": "Phoenix_Force", "directed": true, "weight": 2.5 },
    { "source": "Cyclops_(Marvel_Comics)", "target": "Emma_Frost", "directed": true, "weight": 2.5 },
    { "source": "Cyclops_(Marvel_Comics)", "target": "Scarlet_Witch", "directed": true, "weight": 1.8 },
    { "source": "Emma_Frost", "target": "Cyclops_(Marvel_Comics)", "directed": true, "weight": 2.5 },
    { "source": "Emma_Frost", "target": "Phoenix_Force", "directed": true, "weight": 2.2 },
    { "source": "Emma_Frost", "target": "Wolverine_(character)", "directed": true, "weight": 2.0 },
    { "source": "Emma_Frost", "target": "Spider-Man", "directed": true, "weight": 1.5 },
    { "source": "Phoenix_Force", "target": "Cyclops_(Marvel_Comics)", "directed": true, "weight": 2.5 },
    { "source": "Phoenix_Force", "target": "Emma_Frost", "directed": true, "weight": 2.2 },
    { "source": "Phoenix_Force", "target": "Wolverine_(character)", "directed": true, "weight": 2.0 },
    { "source": "Phoenix_Force", "target": "Scarlet_Witch", "directed": true, "weight": 2.0 },
    { "source": "Phoenix_Force", "target": "Spider-Man", "directed": true, "weight": 1.5 },
    { "source": "Black_Panther_(character)", "target": "Doctor_Strange", "directed": true, "weight": 2.0 },
    { "source": "Black_Panther_(character)", "target": "Scarlet_Witch", "directed": true, "weight": 1.8 },
    { "source": "Black_Panther_(character)", "target": "Deadpool", "directed": true, "weight": 1.5 },
    { "source": "Venom_(character)", "target": "Spider-Man", "directed": true, "weight": 2.5 },
    { "source": "Venom_(character)", "target": "Wolverine_(character)", "directed": true, "weight": 1.8 },
    { "source": "Venom_(character)", "target": "Deadpool", "directed": true, "weight": 1.8 },
    { "source": "Venom_(character)", "target": "Doctor_Strange", "directed": true, "weight": 1.5 },
    { "source": "Venom_(character)", "target": "Black_Panther_(character)", "directed": true, "weight": 1.5 }
  ]
}
```

---

## 4. Degree Distribution: Heavy Tails & Power Laws

Does the Marvel network resemble a classical random network (Erdős–Rényi model), or does it exhibit scale-free characteristics?

In an **Erdős–Rényi random graph** $G(n, p)$, node degrees follow a **Poisson distribution** for large $N$:

$$P(k) = e^{-\lambda} \frac{\lambda^k}{k!}, \quad \lambda = \langle k \rangle$$

In such a graph, the probability of finding a node with degree $k$ significantly larger than the mean decays exponentially. With $\langle k^{\text{in}} \rangle \approx 5.89$, observing a node with $k^{\text{in}} = 106$ in a Poisson model has an astronomical probability of less than $10^{-60}$!

Instead, real information and social graphs are characterized by **heavy-tailed power-law distributions**:

$$P(k) \propto k^{-\gamma}$$

where $\gamma$ is typically in the range $2 < \gamma < 3$.

```
Fraction of Nodes P(k)
  ^
1 | *
  |  *
  |   * (Long tail of minor characters)
  |     *
  |        *
  |             *
0 |__________________*____*__________*____> Node Degree k
  0     5    10    25    50    75   106 (Spider-Man)
```

### Observations from the Empirical Distribution:
1. **Majority Low Connectivity**: Over **62% of characters** have an in-degree of 3 or fewer.
2. **Extreme Outliers**: The top 3 characters alone account for **230 incoming connections** (~13% of all edges in the network).
3. **Preferential Attachment**: Writers and editors linking characters in Wikipedia articles naturally link to well-known heroes when establishing backstories, an analog of the *Barabási-Albert rich-get-richer* mechanism.

---

## 5. Python Analysis Code

Here is a concise Python implementation demonstrating how to load the dataset with its isolates, compute node degrees, and calculate the network metrics described above:

```python
import pandas as pd
import networkx as nx

# 1. Load nodes and directed edges
nodes_df = pd.read_csv('week1_nodes.tsv', sep='\t', comment='#')
edges_df = pd.read_csv('week1_edges.tsv', sep='\t', comment='#')

# 2. Build directed graph
G = nx.DiGraph()
for _, row in nodes_df.iterrows():
    G.add_node(row['node_id'], name=row['name'])

for _, row in edges_df.iterrows():
    G.add_edge(row['source'], row['target'])

# 3. Compute degree metrics
in_deg = dict(G.in_degree())
out_deg = dict(G.out_degree())

# Print top hubs by in-degree
top_in = sorted(in_deg.items(), key=lambda x: x[1], reverse=True)[:5]
print("Top 5 In-Degree Superheroes:")
for node, deg in top_in:
    print(f"  - {G.nodes[node]['name']}: {deg}")

# Print reciprocity
reciprocity = nx.reciprocity(G)
print(f"\nReciprocity: {reciprocity:.2%}")
```

---

## 6. Key Takeaways

1. **Hierarchy of Fame**: Spider-Man is unequivocally the anchor of the Marvel universe in Wikipedia's representation, followed by Hulk and Wolverine.
2. **Asymmetric Roles**: In-degree identifies cultural recognition and canonical prestige, whereas out-degree reflects editorial narrative breadth and multi-team franchise connections.
3. **Scale-Free Structural Resilience**: The extreme degree heterogeneity shows that the Marvel network is robust to random node removal, but fragile to the targeted removal of its top hubs.

In future analyses, we will build upon these degree fundamentals to explore **models and null models** of the Marvel graph!
