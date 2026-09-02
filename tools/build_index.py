#!/usr/bin/env python3
"""
Post Index Builder for Static Network Graph Blog.
Scans markdown files in posts/, extracts frontmatter and wikilinks,
and outputs posts/index.json for client-side loading.
"""

import os
import re
import json
from pathlib import Path

POSTS_DIR = Path(__file__).resolve().parent.parent / "posts"
OUTPUT_FILE = POSTS_DIR / "index.json"

def parse_frontmatter(content):
    if not content.startswith("---"):
        return {}, content
    
    end_idx = content.find("\n---", 3)
    if end_idx == -1:
        return {}, content
    
    yaml_block = content[3:end_idx].strip()
    body = content[end_idx + 4:].strip()
    
    meta = {}
    for line in yaml_block.split("\n"):
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            
            # Quoted string
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            # List [a, b, c]
            elif val.startswith("[") and val.endswith("]"):
                items = val[1:-1].split(",")
                val = [i.strip().strip("'\"") for i in items if i.strip()]
            
            meta[key] = val
            
    return meta, body

def extract_wikilinks(body):
    pattern = r'\[\[([^\]\|]+)(?:\|([^\]]+))?\]\]'
    matches = re.findall(pattern, body)
    return list(set([m[0].strip() for m in matches if m[0]]))

def estimate_read_time(body):
    words = len(body.split())
    minutes = max(1, round(words / 180))
    return f"{minutes} min read"

def build():
    posts = []
    
    if not POSTS_DIR.exists():
        print(f"Directory {POSTS_DIR} does not exist.")
        return
    
    md_files = sorted(list(POSTS_DIR.glob("*.md")), reverse=True)
    
    for file_path in md_files:
        slug = file_path.stem
        with open(file_path, "r", encoding="utf-8") as f:
            raw = f.read()
            
        meta, body = parse_frontmatter(raw)
        
        # Merge frontmatter wikilinks with inline wikilinks
        explicit_links = meta.get("wikilinks", [])
        if isinstance(explicit_links, str):
            explicit_links = [explicit_links]
        body_links = extract_wikilinks(body)
        all_wikilinks = sorted(list(set(explicit_links + body_links)))
        
        # Tags formatting
        tags = meta.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]
            
        post_data = {
            "slug": slug,
            "title": meta.get("title", slug.replace("-", " ").title()),
            "date": meta.get("date", "2026-09-01"),
            "author": meta.get("author", "Robin Hildbrand"),
            "readTime": meta.get("readTime", estimate_read_time(body)),
            "tags": tags,
            "summary": meta.get("summary", body[:160].replace("\n", " ").strip() + "..."),
            "wikilinks": all_wikilinks,
            "file": f"posts/{slug}.md"
        }
        posts.append(post_data)
        
    # Sort posts by date descending
    posts.sort(key=lambda p: p.get("date", ""), reverse=True)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully indexed {len(posts)} posts into {OUTPUT_FILE}")

if __name__ == "__main__":
    build()
