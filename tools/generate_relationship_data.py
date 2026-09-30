"""Build the giant-component relationship data for the concordance applet."""

import json
import re
import urllib.parse
import zipfile
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parent.parent
NODES_FILE = ROOT / "week1_nodes.tsv"
EDGES_FILE = ROOT / "week1_edges.tsv"
PAGES_FILE = ROOT / "marvel_pages.zip"
OUTPUT_FILE = ROOT / "assets" / "marvel_relationships_giant.json"

RELATION_KEYWORDS = {
    "family": ["brother", "father", "son", "married", "wife", "sister", "mother", "cousin"],
    "foe": ["enemy", "rival", "killed", "fought", "villain", "nemesis", "attacked"],
    "ally": ["teammate", "ally", "friend", "partner", "team-up", "crossover", "admiration"],
}


def load_nodes():
    nodes = {}
    with NODES_FILE.open(encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.rstrip("\n").split("\t")
            if parts[0] == "node_id":
                continue
            nodes[parts[0]] = {"id": parts[0], "label": parts[1]}
    return nodes


def load_edges():
    with EDGES_FILE.open(encoding="utf-8") as handle:
        return [tuple(line.rstrip("\n").split("\t")) for line in handle if line.strip() and not line.startswith("#")]


def load_pages():
    with zipfile.ZipFile(PAGES_FILE) as archive:
        return {
            urllib.parse.unquote(name.rsplit("/", 1)[-1][:-4]): archive.read(name).decode("utf-8")
            for name in archive.namelist()
            if name.endswith(".txt") and "README" not in name
        }


def sentences(text):
    clean = " ".join(text.replace("\n", " ").split())
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", clean) if part.strip()]


def classify(excerpts):
    text = " ".join(excerpts).casefold()
    for relation, keywords in RELATION_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                return relation, keyword
    return "unknown", None


def evidence(source, target, pages):
    target_label = target.replace("_", " ").casefold()
    matches = [sentence for sentence in sentences(pages.get(source, "")) if target_label in sentence.casefold()]
    relation, trigger = classify(matches)
    excerpt = next((sentence for sentence in matches if trigger and trigger in sentence.casefold()), matches[0] if matches else "No sentence-level concordance was found in the archived source page.")
    return {
        "source": source,
        "target": target,
        "excerpt": excerpt,
        "relation": relation,
        "trigger": trigger,
        "sourceUrl": f"https://en.wikipedia.org/wiki/{urllib.parse.quote(source, safe='()_')}",
    }


def main():
    nodes = load_nodes()
    directed_edges = load_edges()
    graph = nx.Graph()
    graph.add_nodes_from(nodes)
    graph.add_edges_from((source, target) for source, target in directed_edges if source != target)
    giant_nodes = max(nx.connected_components(graph), key=len)
    giant = graph.subgraph(giant_nodes).copy()
    communities = nx.community.louvain_communities(giant, seed=42)
    community_by_node = {node: index for index, group in enumerate(communities) for node in group}
    pages = load_pages()

    typed_edges = []
    directed_by_pair = {}
    for source, target in directed_edges:
        if source in giant_nodes and target in giant_nodes and source != target:
            row = evidence(source, target, pages)
            typed_edges.append(row)
            directed_by_pair.setdefault(frozenset((source, target)), []).append(row)

    undirected_edges = []
    relation_summary = {"inside": {key: 0 for key in (*RELATION_KEYWORDS, "unknown")}, "between": {key: 0 for key in (*RELATION_KEYWORDS, "unknown")}}
    for pair, rows in directed_by_pair.items():
        relation = next((row["relation"] for row in rows if row["relation"] != "unknown"), "unknown")
        source_row = next((row for row in rows if row["relation"] == relation), rows[0])
        source, target = tuple(pair)
        scope = "inside" if community_by_node[source] == community_by_node[target] else "between"
        relation_summary[scope][relation] += 1
        undirected_edges.append({
            "source": source,
            "target": target,
            "relation": relation,
            "trigger": source_row["trigger"],
            "excerpt": source_row["excerpt"],
            "sourceUrl": source_row["sourceUrl"],
            "directions": len(rows),
            "insideCommunity": scope == "inside",
        })

    output = {
        "nodes": [{**nodes[node], "community": community_by_node[node]} for node in sorted(giant_nodes)],
        "edges": undirected_edges,
        "directedEvidence": typed_edges,
        "communities": len(communities),
        "relationSummary": relation_summary,
        "stats": {
            "nodes": giant.number_of_nodes(),
            "edges": giant.number_of_edges(),
            "directedEdges": len(typed_edges),
            "communitySizes": sorted((len(group) for group in communities), reverse=True),
        },
    }
    OUTPUT_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT_FILE} ({giant.number_of_nodes()} nodes, {giant.number_of_edges()} links, {len(communities)} communities)")
    print(json.dumps(relation_summary, indent=2))


if __name__ == "__main__":
    main()