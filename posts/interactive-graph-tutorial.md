---
title: "How to Publish Posts with Interactive Network Graphs on GitHub Pages"
date: "2026-08-05"
author: "Robin Hildbrand"
readTime: "5 min read"
tags: ["tutorial", "github-pages", "data-viz"]
summary: "A complete step-by-step guide to writing blog posts with embedded force-directed graphs, network DSL syntax, and bi-directional wikilinks."
wikilinks: ["spectral-graph-theory", "knowledge-graphs-and-llms"]
---

This static website gives you a frictionless publishing platform for technical writing, academic research, and interactive data visualization on **GitHub Pages without Jekyll**.

Every markdown file placed in `posts/` is automatically indexed and rendered into a high-performance interactive article with interactive network graphs.

---

## 1. Quick Syntax: Embedding Network Graphs

You can embed graphs inside your markdown posts in two easy formats:

### Method A: Human-Friendly Network DSL (\`\`\`network)
For quick, intuitive conceptual diagrams:

```network
[Idea] -> [Hypothesis] : formulate
[Hypothesis] -> [Experiment] : test in lab
[Experiment] -> [Data Analysis] : collect metrics
[Data Analysis] -> [Publication] : write paper
[Publication] -> [Peer Review] : review
```

### Method B: Full JSON Format (\`\`\`graph)
For complete control over colors, node sizes, weights, and groups:

```graph
{
  "nodes": [
    { "id": "A", "label": "Origin", "group": "theory", "size": 20, "color": "#6366f1" },
    { "id": "B", "label": "Destination 1", "group": "algorithms", "size": 15, "color": "#38bdf8" },
    { "id": "C", "label": "Destination 2", "group": "math", "size": 15, "color": "#ec4899" }
  ],
  "links": [
    { "source": "A", "target": "B", "label": "flow A", "directed": true, "weight": 2.5 },
    { "source": "A", "target": "C", "label": "flow B", "directed": true, "weight": 2.5 },
    { "source": "B", "target": "C", "label": "feedback", "directed": true, "weight": 1.5, "dashed": true }
  ]
}
```

---

## 2. Linking Articles with Wikilinks

Use double brackets `[[slug]]` or `[[slug|Custom Label]]` to link to any other post in your blog:

- `[[spectral-graph-theory]]` -> links directly to the spectral graph theory post.
- `[[knowledge-graphs-and-llms|Knowledge Graphs in AI]]` -> custom display text.

Whenever you add a wikilink, the engine automatically registers a directed edge between the two posts in both the **Global Knowledge Graph** and the **Local Article Connections Widget**!

---

## 3. How to Create and Publish a New Post

### Step 1: Create a Markdown File
Create a new file in the `posts/` directory, for example `posts/my-new-discovery.md`:

```markdown
---
title: "My New Discovery in Graph Learning"
date: "2026-09-05"
author: "Robin Hildbrand"
readTime: "6 min read"
tags: ["graph-theory", "machine-learning"]
summary: "A brief summary of your key insights."
wikilinks: ["spectral-graph-theory"]
---

Your content goes here...
```

### Step 2: Regenerate the Post Index (Optional / Automated)
Run the indexer tool:

```bash
python3 tools/build_index.py
```

### Step 3: Push to GitHub Pages
Commit and push to your GitHub repository:

```bash
git add .
git commit -m "Add my new discovery post"
git push origin main
```

Your post is immediately live on GitHub Pages with interactive graphs, search indexing, and graph network connections!
