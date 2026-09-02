---
title: "Foundations of Spectral Graph Theory: Graph Laplacians & Diffusion"
date: "2026-09-02"
author: "Robin Hildbrand"
readTime: "8 min read"
tags: ["graph-theory", "linear-algebra", "spectral-methods"]
summary: "An exploration of graph Laplacians, eigenvalue spectra, Rayleigh quotients, and continuous heat diffusion across complex networks."
wikilinks: ["graph-neural-networks", "complex-networks-diffusion"]
---

Spectral graph theory studies the properties of graphs via the eigenvalues and eigenvectors of matrices associated with them, most notably the **Graph Laplacian**.

By mapping discrete combinatorial structures into continuous linear algebra, spectral methods give us profound insights into graph connectivity, community bottlenecks (Cheeger bounds), and continuous diffusion processes.

> [!NOTE]
> For a connected undirected graph $G = (V, E)$, the spectrum of the Laplacian encodes its algebraic connectivity, spanning tree counts, and topological symmetries.

---

## 1. The Graph Laplacian Matrix

Given an undirected graph $G = (V, E)$ with vertex set $V = \{1, \dots, n\}$ and edge set $E$, let:
- $\mathbf{A} \in \mathbb{R}^{n 	imes n}$ be the **Adjacency Matrix**, where $A_{ij} = 1$ if $(i,j) \in E$, and $0$ otherwise.
- $\mathbf{D} \in \mathbb{R}^{n 	imes n}$ be the **Degree Matrix**, a diagonal matrix with $D_{ii} = d_i = \sum_{j} A_{ij}$.

The unnormalized **Graph Laplacian** $\mathbf{L}$ is defined as:

$$\mathbf{L} = \mathbf{D} - \mathbf{A}$$

For any signal vector $\mathbf{x} \in \mathbb{R}^n$ defined on the vertices:

$$\mathbf{x}^T \mathbf{L} \mathbf{x} = \sum_{(i,j) \in E} (x_i - x_j)^2$$

This quadratic form immediately demonstrates that $\mathbf{L}$ is **symmetric positive semi-definite** ($L \succeq 0$). Its eigenvalues are non-negative and real:

$$0 = \lambda_1 \le \lambda_2 \le \dots \le \lambda_n$$

```graph
{
  "nodes": [
    { "id": "v1", "label": "Node 1 (d=3)", "group": "theory", "size": 18, "color": "#6366f1" },
    { "id": "v2", "label": "Node 2 (d=2)", "group": "theory", "size": 15, "color": "#6366f1" },
    { "id": "v3", "label": "Node 3 (d=3)", "group": "theory", "size": 18, "color": "#6366f1" },
    { "id": "v4", "label": "Node 4 (d=2)", "group": "theory", "size": 15, "color": "#6366f1" },
    { "id": "v5", "label": "Bridge Node 5", "group": "algorithms", "size": 20, "color": "#ec4899" },
    { "id": "v6", "label": "Cluster B1", "group": "math", "size": 14, "color": "#38bdf8" },
    { "id": "v7", "label": "Cluster B2", "group": "math", "size": 14, "color": "#38bdf8" },
    { "id": "v8", "label": "Cluster B3", "group": "math", "size": 14, "color": "#38bdf8" }
  ],
  "links": [
    { "source": "v1", "target": "v2", "weight": 2 },
    { "source": "v2", "target": "v3", "weight": 2 },
    { "source": "v3", "target": "v4", "weight": 2 },
    { "source": "v4", "target": "v1", "weight": 2 },
    { "source": "v1", "target": "v3", "weight": 2 },
    { "source": "v3", "target": "v5", "weight": 3, "color": "#ec4899" },
    { "source": "v5", "target": "v6", "weight": 3, "color": "#ec4899" },
    { "source": "v6", "target": "v7", "weight": 2 },
    { "source": "v7", "target": "v8", "weight": 2 },
    { "source": "v8", "target": "v6", "weight": 2 }
  ]
}
```

---

## 2. The Fiedler Vector and Spectral Bisection

The second smallest eigenvalue $\lambda_2$ is termed the **algebraic connectivity** of the graph (Fiedler value). 

$$\lambda_2 = \min_{\mathbf{x} \perp \mathbf{1}, \mathbf{x} 
e 0} rac{\mathbf{x}^T \mathbf{L} \mathbf{x}}{\mathbf{x}^T \mathbf{x}}$$

The corresponding eigenvector $\mathbf{v}_2$ is called the **Fiedler vector**. The signs of the entries of $\mathbf{v}_2$ partition the graph into two weakly coupled subgraphs, minimizing the cut boundary!

```python
import numpy as np
import scipy.linalg as la

def spectral_bisection(adj_matrix):
    # Compute Degree Matrix
    deg = np.diag(adj_matrix.sum(axis=1))
    # Unnormalized Laplacian
    L = deg - adj_matrix
    # Eigenvalue decomposition
    eigenvals, eigenvecs = la.eigh(L)
    # Fiedler vector is the eigenvector for the 2nd smallest eigenvalue
    fiedler_vec = eigenvecs[:, 1]
    # Partition by sign
    cluster_a = np.where(fiedler_vec >= 0)[0]
    cluster_b = np.where(fiedler_vec < 0)[0]
    return cluster_a, cluster_b, eigenvals[1]
```

---

## 3. Heat Diffusion on Networks

Heat diffusion across the network vertices satisfies the continuous differential equation:

$$rac{\partial \mathbf{u}(t)}{\partial t} = - \mathbf{L} \mathbf{u}(t)$$

Given an initial heat distribution $\mathbf{u}(0) = \mathbf{u}_0$, the exact solution is governed by the **matrix exponential** (heat kernel):

$$\mathbf{u}(t) = \exp(-t \mathbf{L}) \mathbf{u}_0 = \sum_{k=1}^n e^{-\lambda_k t} (\mathbf{v}_k^T \mathbf{u}_0) \mathbf{v}_k$$

As $t 	o \infty$, all modes with $\lambda_k > 0$ decay exponentially, and the heat converges uniformly to the steady-state average across the connected component.

> [!TIP]
> Spectral graph theory serves as the theoretical bedrock for [[graph-neural-networks]] and modeling epidemic propagation in [[complex-networks-diffusion]].
