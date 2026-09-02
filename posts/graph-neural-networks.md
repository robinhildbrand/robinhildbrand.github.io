---
title: "Graph Neural Networks: From Spatial Convolutions to Message Passing"
date: "2026-08-28"
author: "Robin Hildbrand"
readTime: "10 min read"
tags: ["machine-learning", "graph-theory", "deep-learning"]
summary: "Understanding spatial message passing schemes, permutation equivariance, spectral GCNs, and attention mechanisms on non-Euclidean domains."
wikilinks: ["spectral-graph-theory", "knowledge-graphs-and-llms"]
---

Unlike standard Convolutional Neural Networks (CNNs) designed for Euclidean grid structured data (images, audio), **Graph Neural Networks (GNNs)** operate on non-Euclidean domains where neighborhoods vary dynamically in size and connectivity.

At the core of modern GNNs lies the **Message Passing Framework** (Gilmer et al., 2017).

> [!NOTE]
> GNNs are designed to satisfy **permutation equivariance**: renaming or re-indexing nodes does not alter the underlying topological representations.

---

## 1. The Message Passing Framework

In layer $l$, each node $v \in V$ aggregates contextual feature messages from its 1-hop neighbors $\mathcal{N}(v)$ and updates its own representation vector:

$$\mathbf{m}_v^{(l+1)} = igoplus_{u \in \mathcal{N}(v)} 	ext{MSG}^{(l)}\left(\mathbf{h}_v^{(l)}, \mathbf{h}_u^{(l)}, \mathbf{e}_{uv}ight)$$

$$\mathbf{h}_v^{(l+1)} = 	ext{UPDATE}^{(l)}\left(\mathbf{h}_v^{(l)}, \mathbf{m}_v^{(l+1)}ight)$$

Where $igoplus$ denotes a permutation-invariant aggregation function such as $\sum$, $	ext{mean}$, or $\max$.

```network
[Raw Node Features X] -> [Layer 1: Message Passing] : linear projection
[Adjacency Matrix A] -> [Layer 1: Message Passing] : graph topology
[Layer 1: Message Passing] -> [ReLU & BatchNorm] : non-linear activation
[ReLU & BatchNorm] -> [Layer 2: Neighborhood Aggregation] : 2-hop receptive field
[Layer 2: Neighborhood Aggregation] -> [Node Embeddings Z] : representation
[Node Embeddings Z] -> [Node Classification] : softmax logits
[Node Embeddings Z] -> [Link Prediction] : dot product
```

---

## 2. Spectral Graph Convolutions vs Spatial GCN

The bridge between [[spectral-graph-theory]] and deep learning occurs in **Spectral Graph Convolutional Networks** (Kipf & Welling, 2016).

In spectral domain, a graph convolution of signal $\mathbf{x}$ with filter $g_	heta$ is defined as:

$$g_	heta \star \mathbf{x} = \mathbf{U} g_	heta(\mathbf{\Lambda}) \mathbf{U}^T \mathbf{x}$$

where $\mathbf{U}$ is the eigenvector matrix of the normalized Graph Laplacian $\mathbf{L}_{sym} = \mathbf{I} - \mathbf{D}^{-1/2} \mathbf{A} \mathbf{D}^{-1/2}$.

Using a 1st-order Chebyshev polynomial truncation with renormalization trick ($\mathbf{	ilde{A}} = \mathbf{A} + \mathbf{I}_n$):

$$\mathbf{H}^{(l+1)} = \sigma\left( \mathbf{	ilde{D}}^{-1/2} \mathbf{	ilde{A}} \mathbf{	ilde{D}}^{-1/2} \mathbf{H}^{(l)} \mathbf{W}^{(l)} ight)$$

```graph
{
  "nodes": [
    { "id": "Target", "label": "Target Node (v)", "group": "theory", "size": 20, "color": "#ec4899" },
    { "id": "N1", "label": "Neighbor 1", "group": "algorithms", "size": 15, "color": "#6366f1" },
    { "id": "N2", "label": "Neighbor 2", "group": "algorithms", "size": 15, "color": "#6366f1" },
    { "id": "N3", "label": "Neighbor 3", "group": "algorithms", "size": 15, "color": "#6366f1" },
    { "id": "Hop2_A", "label": "2-Hop Leaf A", "group": "concept", "size": 11, "color": "#38bdf8" },
    { "id": "Hop2_B", "label": "2-Hop Leaf B", "group": "concept", "size": 11, "color": "#38bdf8" },
    { "id": "Hop2_C", "label": "2-Hop Leaf C", "group": "concept", "size": 11, "color": "#38bdf8" }
  ],
  "links": [
    { "source": "N1", "target": "Target", "directed": true, "label": "W_msg * h_1", "weight": 2.5, "color": "#ec4899" },
    { "source": "N2", "target": "Target", "directed": true, "label": "W_msg * h_2", "weight": 2.5, "color": "#ec4899" },
    { "source": "N3", "target": "Target", "directed": true, "label": "W_msg * h_3", "weight": 2.5, "color": "#ec4899" },
    { "source": "Hop2_A", "target": "N1", "directed": true, "weight": 1.2 },
    { "source": "Hop2_B", "target": "N1", "directed": true, "weight": 1.2 },
    { "source": "Hop2_C", "target": "N2", "directed": true, "weight": 1.2 }
  ]
}
```

---

## 3. Graph Attention Networks (GAT)

Instead of uniform or degree-normalized weighting, **Graph Attention Networks** compute dynamic attention coefficients $lpha_{uv}$ between connected nodes:

$$lpha_{uv} = rac{\exp\left( 	ext{LeakyReLU}\left(\mathbf{a}^T [\mathbf{W}\mathbf{h}_u \,\|\, \mathbf{W}\mathbf{h}_v]ight)ight)}{\sum_{k \in \mathcal{N}(u)} \exp\left( 	ext{LeakyReLU}\left(\mathbf{a}^T [\mathbf{W}\mathbf{h}_u \,\|\, \mathbf{W}\mathbf{h}_k]ight)ight)}$$

This allows the network to selectively focus on crucial topological motifs and relationships, providing a natural connection to multi-relational graphs in [[knowledge-graphs-and-llms]].
