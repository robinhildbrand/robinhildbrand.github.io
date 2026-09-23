---
title: "Clique Percolation Lab: Finding the Hidden Merge Path"
date: "2026-09-23"
author: "Robin, Giosué, Sébastien"
readTime: "3 min read"
tags: ["cliques", "community-detection", "percolation", "network-science"]
summary: "An interactive clique-percolation puzzle with adjustable k, decoy links, and increasingly difficult bridge networks."
layout: full
---

# Clique Percolation Lab

Clique percolation turns tightly connected groups into communities. For a chosen clique size $k$, two $k$-cliques belong to the same community when they share at least $k-1$ nodes.

This version is a puzzle rather than a single prescribed animation. Choose $k=3$ to search for triangle bridges, or raise it to $k=4$ where a bridge may need several missing links before a tetrad appears. Switch between the bridge chain and decoy maze, then add only the dashed edges that complete new cliques. Wrong links are deliberately plausible but do not advance the percolation.

<iframe src="assets/applets/clique-percolation.html" width="100%" height="820" frameborder="0" style="border: 1px solid var(--border-subtle); border-radius: 12px; overflow: hidden; background: var(--bg-surface); margin: 1.5rem 0;" title="Interactive: adjustable clique percolation challenge"></iframe>

## The rule behind the cascade

The rule stays simple while the search gets harder: a candidate edge counts only if it completes a new $k$-clique, and that clique must overlap a neighboring clique in $k-1$ nodes. At $k=4$, the intermediate tetrad needs two added links, making the hidden path less obvious than the triangle case. The final unified color marks the giant overlapping community.
