# Robin Hildbrand — Graph Blog & Network Garden 🕸️

A modern, high-performance static website and digital garden built specifically for **GitHub Pages (No Jekyll)** that publishes technical blog posts with **interactive network graphs**, bi-directional wikilinks, and mathematical rigor.

[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Live-success?style=flat-square&logo=github)](https://robinhildbrand.github.io)
[![Zero Build](https://img.shields.io/badge/Build-Zero%20Dependencies-blue?style=flat-square)](https://github.com/robinhildbrand/robinhildbrand.github.io)
[![D3.js](https://img.shields.io/badge/D3.js-Force%20Simulation-orange?style=flat-square&logo=d3.js)](https://d3js.org)

---

## ✨ Features

- **No Jekyll / Zero Build Pipeline**: Pure static HTML5, CSS3, and modern JavaScript. Works immediately on GitHub Pages without needing Ruby, Bundler, or GitHub Actions.
- **Interactive Force-Directed Graph Engine (D3.js)**:
  - Physics simulations with real-time charge repulsion, link distance, and collision forces.
  - Multi-layout support: Force-directed, alphabetical circular, and degree-based circular layouts.
  - Edge particle flow animations representing continuous diffusion and signal propagation.
  - Ego-network neighborhood highlighting on hover / selection.
  - Pan, zoom, drag-and-drop, full-screen mode, and high-resolution PNG image export.
- **In-Post Graph Visualizations**:
  - Direct markdown code block support for both full JSON (```graph) and intuitive text DSL (```network).
- **Obsidian / Roam-style Bi-directional Wikilinks**:
  - Link between posts using `[[post-slug]]` or `[[post-slug|Custom Label]]`.
  - Automatically builds a **Global Knowledge Graph** and per-article **Connections Ego-Network**.
- **LaTeX Math Formulas**: Fast client-side rendering via KaTeX for inline `$E = mc^2$` and block matrices `$$\mathbf{L} = \mathbf{D} - \mathbf{A}$$`.
- **Global Command Palette Search**: Press <kbd>Cmd</kbd> + <kbd>K</kbd> (or <kbd>Ctrl</kbd> + <kbd>K</kbd>) to instantly search articles, topics, and graph nodes.
- **Dark & Light Mode**: Seamless theme switcher with persistent local storage preferences.
- **Responsive Typography & Design**: Optimized for desktops, tablets, and mobile devices.

---

## 📁 Repository Structure

```
├── .nojekyll                   # Instructs GitHub Pages to serve files without Jekyll
├── index.html                  # Single-page application shell & layout
├── 404.html                    # GitHub Pages SPA deep-link routing fallback
├── README.md                   # Project documentation
├── assets/
│   ├── css/
│   │   ├── style.css           # Core typography, dark/light theme tokens, UI components
│   │   └── graph.css           # Graph canvas, toolbar, tooltips, and inspector drawer styles
│   ├── js/
│   │   ├── app.js              # Client-side router, view controllers, theme and search modals
│   │   ├── graph-engine.js     # D3-based canvas & SVG force-directed physics engine
│   │   ├── graph-parser.js     # Parser for ```graph JSON and ```network DSL blocks
│   │   ├── markdown.js         # Frontmatter, KaTeX, Marked.js parser, and wikilink transformer
│   │   └── posts-store.js      # Post index loader and knowledge graph synthesizer
│   └── images/
│       ├── avatar.svg          # Author profile image
│       └── favicon.svg         # SVG vector network graph favicon
├── posts/
│   ├── index.json              # Post metadata catalog (auto-generated)
│   └── exploring-degrees-marvel-dataset.md
└── tools/
    ├── build_index.py          # Auto-generates posts/index.json from markdown files
    └── new_post.py             # CLI scaffold tool for creating new posts
```

---

## 🚀 Quick Start (Local Development)

Because this blog is a zero-build static site, you can run a local development server with any standard static file server:

```bash
# Using Python 3 (built-in):
python3 -m http.server 8000

# Open in your browser:
# http://localhost:8000
```

---

## ✍️ How to Publish a New Blog Post

### Method 1: Using the CLI Tool (Recommended)

Run the interactive CLI helper:

```bash
python3 tools/new_post.py "My New Article Title"
```

This creates `posts/my-new-article-title.md` with pre-filled frontmatter and rebuilds `posts/index.json`.

### Method 2: Manual Creation

1. Create a markdown file inside `posts/`, e.g. `posts/topological-data-analysis.md`:

```markdown
---
title: "Topological Data Analysis and Persistent Homology"
date: "2026-09-10"
author: "Robin Hildbrand"
readTime: "7 min read"
tags: ["topology", "graph-theory", "data-science"]
summary: "Extracting persistent topological invariants from point clouds and high-dimensional graphs."
wikilinks: ["exploring-degrees-marvel-dataset"]
---

Write your article here in standard Markdown.

### 1. Embedded Network DSL Example

```network
[Point Cloud] -> [Vietoris-Rips Complex] : filtration epsilon
[Vietoris-Rips Complex] -> [Simplicial Homology] : boundary operator
[Simplicial Homology] -> [Persistence Diagram] : birth-death pairs
```

### 2. Embedded JSON Graph Example

```graph
{
  "nodes": [
    { "id": "A", "label": "Filtration 1", "group": "theory", "size": 18, "color": "#6366f1" },
    { "id": "B", "label": "Filtration 2", "group": "algorithms", "size": 16, "color": "#38bdf8" }
  ],
  "links": [
    { "source": "A", "target": "B", "label": "epsilon expansion", "directed": true, "weight": 2 }
  ]
}
```

Link to other posts using wikilinks: [[exploring-degrees-marvel-dataset]].
```

2. Rebuild the post manifest:

```bash
python3 tools/build_index.py
```

3. Commit and push to GitHub:

```bash
git add .
git commit -m "Publish topological data analysis post"
git push origin main
```

---

## 🌐 Publishing to GitHub Pages

1. Push this repository to `https://github.com/robinhildbrand/robinhildbrand.github.io`.
2. In GitHub repository settings:
   - Go to **Settings** > **Pages**.
   - Under **Build and deployment**:
     - **Source**: Select **Deploy from a branch**.
     - **Branch**: Select `main` / `root`.
3. Save. GitHub Pages will serve your site directly at `https://robinhildbrand.github.io`.

---

## 📄 License

MIT License © 2026 Robin Hildbrand.
