#!/usr/bin/env python3
"""
CLI Helper to scaffold a new blog post with frontmatter and an interactive network graph template.
Usage:
  python3 tools/new_post.py "My New Post Title"
"""

import sys
import datetime
from pathlib import Path
from build_index import build

POSTS_DIR = Path(__file__).resolve().parent.parent / "posts"

TEMPLATE = """---
title: "{title}"
date: "{date}"
author: "Robin Hildbrand"
readTime: "6 min read"
tags: ["graph-theory", "machine-learning"]
summary: "A concise executive summary of this post."
wikilinks: ["spectral-graph-theory"]
---

Write your introductory thoughts here. You can use math like $E = mc^2$ or display formulas:

$$\mathbf{{L}} = \mathbf{{D}} - \mathbf{{A}}$$

> [!NOTE]
> Add notes, tips, or warnings to highlight crucial concepts.

---

## 1. Conceptual Model

Below is an interactive network diagram of the architecture:

```network
[Source Entity] -> [Intermediate Layer] : processes
[Intermediate Layer] -> [Output Representation] : predicts
[Output Representation] -> [Decision Engine] : evaluates
```

---

## 2. Quantitative Formulation

You can also embed custom JSON graphs with custom colors and weights:

```graph
{{
  "nodes": [
    {{ "id": "A", "label": "Node A", "group": "theory", "size": 18, "color": "#6366f1" }},
    {{ "id": "B", "label": "Node B", "group": "algorithms", "size": 14, "color": "#38bdf8" }}
  ],
  "links": [
    {{ "source": "A", "target": "B", "label": "interacts", "directed": true, "weight": 2 }}
  ]
}}
```

Connect to other articles with wikilinks like [[spectral-graph-theory]].
"""

def main():
    if len(sys.argv) > 1:
        title = " ".join(sys.argv[1:])
    else:
        title = input("Enter post title: ").strip()
        
    if not title:
        print("Error: Title cannot be empty.")
        sys.exit(1)
        
    slug = title.lower()
    for char in " :/'\"?,.!@#$%^&*()+=[]{}|;":
        slug = slug.replace(char, "-")
    slug = "-".join([s for s in slug.split("-") if s])
    
    today = datetime.date.today().isoformat()
    filepath = POSTS_DIR / f"{slug}.md"
    
    if filepath.exists():
        print(f"Error: File {filepath} already exists.")
        sys.exit(1)
        
    content = TEMPLATE.format(title=title, date=today)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"Created new post at {filepath}")
    
    # Rebuild index
    build()
    print(f"Index updated! You can start editing {filepath}")

if __name__ == "__main__":
    main()
