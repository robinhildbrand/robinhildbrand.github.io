---
title: "Exploring Degrees in the Marvel Dataset"
date: "2026-09-04"
author: "Robin, Giosué, Sébastien"
readTime: "8 min read"
tags: ["marvel", "network-analysis", "degree-distribution", "complex-networks"]
summary: "An empirical analysis of node degrees, in/out-degree asymmetries, power-law distributions, and central superhero hubs across the Wikipedia Marvel Comics network."
wikilinks: []
---

This week we are going to analyze the network of Marvel Comics with respect to Wikipedia.

In order to accomplish this analysis we use Marvel characters and their links as nodes and edges respectively. We finally extract data from this network, such as in- and out-degree.

---

## What is the difference between in-degree and out-degree?

**In-degree** of a node represents the number of edges that arrive to that node. Conversely **out-degree** represents the number of edges that start from a node.

Let's try to see why these to values can differ by looking at Marvel characters.

<iframe src="assets/applets/degree-radii.html" width="100%" height="560" frameborder="0" style="border: 1px solid var(--border-subtle); border-radius: 12px; overflow: hidden; background: var(--bg-surface); margin: 1.5rem 0;" title="Marvel Network: Node Radii by In-Degree and Out-Degree"></iframe>

As we can clearly see a lot of characters link to Spiderman but Spiderman has very few outside links. 

---

## Statistics

Using `networkx` and `pandas`, we can load the dataset and compute the degree metrics and connected components with a concise snippet:

```python
import pandas as pd
import networkx as nx

# 1. Load nodes and directed edges
nodes_df = pd.read_csv('week1_nodes.tsv', sep='\t', comment='#')
edges_df = pd.read_csv('week1_edges.tsv', sep='\t', comment='#', names=['source', 'target'])

# 2. Build directed graph
G = nx.DiGraph()
for _, row in nodes_df.iterrows():
    G.add_node(row['node_id'], name=row['name'])

for _, row in edges_df.iterrows():
    G.add_edge(row['source'], row['target'])

# 3. Top 5 characters by in-degree and out-degree
top_in = sorted(G.in_degree(), key=lambda x: x[1], reverse=True)[:5]
top_out = sorted(G.out_degree(), key=lambda x: x[1], reverse=True)[:5]

print("Top 5 In-Degree:")
for node, deg in top_in:
    print(f"  - {G.nodes[node]['name']}: {deg}")

print("\nTop 5 Out-Degree:")
for node, deg in top_out:
    print(f"  - {G.nodes[node]['name']}: {deg}")

# 4. Connected components
wcc = list(nx.weakly_connected_components(G))

print(f"\nWeakly Connected Components: {len(wcc)}")
print(f"  - Giant component: {len(max(wcc, key=len))} nodes")
print(f"  - Isolates (size 1): {sum(1 for c in wcc if len(c) == 1)}")
print(f"  - Lengths of components > 1 : {[len(c) for c in wcc if len(c) > 1]}")
```

### Extracted Results

#### Degree Centrality

| Rank | Top 5 In-Degree | In-Degree | Top 5 Out-Degree | Out-Degree |
| :---: | :--- | :---: | :--- | :---: |
| 1 | **Spider-Man** | 106 | **Betsy Braddock** | 28 |
| 2 | **Hulk** | 64 | **Cloak and Dagger** | 24 |
| 3 | **Wolverine** | 60 | **Adam Warlock** | 22 |
| 4 | **Doctor Strange** | 50 | **Venom** | 21 |
| 5 | **Deadpool** | 33 | **She-Hulk** | 20 |

- **In-Degree Hubs**: Spider-Man is by far the character with the biggest in-degree which is nearly twice as big as Hulk.
- **Out-Degree Leaders**: Betsy Braddock has way more competition for the title of number one suggesting that the laws of In-degree and Out-degree distribution might be different.

#### Islands

- **Two Islands and the rest**: Two non-isolated components are present in the dataset:
  - **Biggest Island** : 277 nodes 
  - **The Other Island** : 9 nodes
  - **Isolates** : 17 nodes

---

## Power Laws

One can easily see that even for relatively large in-degrees there exists nodes that have such a high degree. Most of the nodes have a small in-degree but some have ten times, even hundred times more.
To get a better glance at this phenomon that seems to follow a **power law** we can plot our degrees against the number of the nodes that have that degree. A straight line on the log-log plot indicates that the phenomenon we observe is indeed a **power law**.

<iframe src="assets/applets/powerlaw-distribution.html" width="100%" height="580" frameborder="0" style="border: 1px solid var(--border-subtle); border-radius: 12px; overflow: hidden; background: var(--bg-surface); margin: 1.5rem 0;" title="Marvel Network: Degree Distribution Log-Log Plot"></iframe>

---

Next week we will continue to explore the Marvel network with the lenses of **models**.