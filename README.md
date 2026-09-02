# Robin Hildbrand — Academic GitHub Pages Blog

An academic research blog and computational notes website hosted on GitHub Pages. Features native LaTeX mathematics (KaTeX), interactive network graph visualizations (Vis.js), 2D mathematical function plots (FunctionPlot), 3D surfaces (Plotly), and Mermaid/Graphviz diagrams.

## Key Features

- **Academic Aesthetics:** Clean Latin Modern / EB Garamond typography, paper-like layout, numbered Theorem/Lemma/Definition/Proof environments with tombstone, author affiliation card (EPFL), and BibTeX citation exporter.
- **Interactive Network Graphs:** Embed physics-simulated, draggable network graphs directly in Markdown via ````network```` code blocks.
- **Mathematical Function Plotting:** Interactive 2D function curves with derivative tangents and zoom via ````function-plot```` code blocks.
- **3D Scientific Surfaces:** Interactive 3D surfaces and heatmaps via ````plotly```` code blocks.
- **Fast LaTeX Math:** Ultra-fast client-side KaTeX rendering for inline `$ ... $` and display `$$ ... $$` formulas.
- **Responsive Dark/Light Mode:** Automatic system preference detection with manual toggle.
- **Zero-Build Deployment:** Natively supported by GitHub Pages out-of-the-box.

## Quickstart: Plotting Graphs in Blog Posts

### 1. Plotting an Interactive Network Graph
In any `.md` file in `_posts/`, add:

````markdown
```network
{
  "title": "My Network Graph",
  "height": "400px",
  "physics": true,
  "nodes": [
    {"id": 1, "label": "Node A", "group": "cluster1", "size": 24},
    {"id": 2, "label": "Node B", "group": "cluster2", "size": 20}
  ],
  "edges": [
    {"from": 1, "to": 2, "width": 2, "label": "weight: 0.8"}
  ]
}
```
````

### 2. Plotting Mathematical Functions
````markdown
```function-plot
{
  "title": "Damped Sine Wave",
  "xDomain": [-1, 10],
  "yDomain": [-1.5, 1.5],
  "grid": true,
  "data": [
    {
      "fn": "exp(-0.2*x) * sin(2*x)",
      "color": "#2563eb",
      "derivative": {
        "fn": "-0.2*exp(-0.2*x)*sin(2*x) + 2*exp(-0.2*x)*cos(2*x)",
        "updateOnMouseMove": true
      }
    }
  ]
}
```
````

## Testing & Deployment

### Testing Locally
```bash
python3 -m http.server 4000
```
Navigate to `http://localhost:4000`.

### Deploying to GitHub Pages
1. Commit and push your changes:
   ```bash
   git add .
   git commit -m "Create academic blog site"
   git push origin main
   ```
2. Your site will automatically build and publish at `https://robinhildbrand.github.io/`.
