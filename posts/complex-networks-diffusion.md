---
title: "Information Diffusion and Epidemics on Scale-Free Networks"
date: "2026-08-14"
author: "Robin Hildbrand"
readTime: "9 min read"
tags: ["complex-systems", "graph-theory", "diffusion"]
summary: "Simulating SIR epidemic models and information cascades on Barabási-Albert and Watts-Strogatz network topologies."
wikilinks: ["spectral-graph-theory"]
---

Real-world systems—such as social networks, the Internet, financial transaction webs, and biological interactomes—rarely exhibit random Erdős-Rényi Poisson degree distributions.

Instead, they manifest **scale-free power-law degree distributions**:

$$P(k) \sim k^{-\gamma}, \quad 2 < \gamma < 3$$

Because a tiny fraction of **hub nodes** possess an immense number of connections, scale-free networks exhibit extraordinary resilience to random failures, yet extreme vulnerability to targeted attacks or epidemics.

> [!WARNING]
> In an infinite scale-free network with $\gamma \le 3$, the epidemic threshold drops to zero ($	au_c = 0$): any contagious pathogen or viral meme will spread with non-zero probability regardless of transmission rate!

---

## 1. The Barabási-Albert Preferential Attachment Model

Under the Barabási-Albert (BA) generative mechanism, new nodes enter the network and attach to $m$ existing nodes with probability proportional to their degree:

$$\Pi(i) = rac{k_i}{\sum_j k_j}$$

Below is an interactive scale-free topology highlighting a central hub surrounded by multi-tier peripheral clusters:

```graph
{
  "nodes": [
    { "id": "Hub1", "label": "Super Hub Alpha", "group": "theory", "size": 26, "color": "#ec4899" },
    { "id": "Hub2", "label": "Hub Beta", "group": "theory", "size": 20, "color": "#6366f1" },
    { "id": "Hub3", "label": "Hub Gamma", "group": "theory", "size": 18, "color": "#38bdf8" },
    { "id": "P1", "label": "Peripheral 1", "group": "concept", "size": 9, "color": "#94a3b8" },
    { "id": "P2", "label": "Peripheral 2", "group": "concept", "size": 9, "color": "#94a3b8" },
    { "id": "P3", "label": "Peripheral 3", "group": "concept", "size": 9, "color": "#94a3b8" },
    { "id": "P4", "label": "Peripheral 4", "group": "concept", "size": 9, "color": "#94a3b8" },
    { "id": "P5", "label": "Peripheral 5", "group": "concept", "size": 9, "color": "#94a3b8" },
    { "id": "P6", "label": "Peripheral 6", "group": "concept", "size": 9, "color": "#94a3b8" },
    { "id": "P7", "label": "Peripheral 7", "group": "concept", "size": 9, "color": "#94a3b8" },
    { "id": "P8", "label": "Peripheral 8", "group": "concept", "size": 9, "color": "#94a3b8" }
  ],
  "links": [
    { "source": "Hub1", "target": "Hub2", "weight": 3, "color": "#ec4899" },
    { "source": "Hub1", "target": "Hub3", "weight": 3, "color": "#ec4899" },
    { "source": "Hub2", "target": "Hub3", "weight": 2 },
    { "source": "Hub1", "target": "P1", "weight": 1 },
    { "source": "Hub1", "target": "P2", "weight": 1 },
    { "source": "Hub1", "target": "P3", "weight": 1 },
    { "source": "Hub1", "target": "P4", "weight": 1 },
    { "source": "Hub2", "target": "P5", "weight": 1 },
    { "source": "Hub2", "target": "P6", "weight": 1 },
    { "source": "Hub3", "target": "P7", "weight": 1 },
    { "source": "Hub3", "target": "P8", "weight": 1 }
  ]
}
```

---

## 2. Susceptible-Infectious-Recovered (SIR) Dynamics

On a graph $G = (V, E)$, the stochastic SIR process models:
1. **$S 	o I$:** An infected node transmits the infection to a susceptible neighbor with rate $eta$.
2. **$I 	o R$:** An infected node recovers with rate $\gamma$ and attains permanent immunity.

In mean-field approximation, the individual probability of infection satisfies:

$$rac{d ho_k(t)}{dt} = eta k \left(1 - ho_k(t)ight) \Theta(t) - \gamma ho_k(t)$$

where the effective field is:

$$\Theta(t) = rac{\sum_k (k-1) P(k) ho_k(t)}{\langle k angle}$$

Because $\langle k^2 angle 	o \infty$ as the network size $N 	o \infty$ for $\gamma \le 3$, the critical basic reproduction threshold $R_0 = rac{eta}{\gamma} rac{\langle k^2 angle}{\langle k angle}$ diverges, meaning epidemics spread effortlessly through hub nodes.

For continuous diffusion analysis via Graph Laplacians, see [[spectral-graph-theory]].
