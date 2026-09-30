---
title: "Typing Marvel Relationships with Wikipedia Concordances"
date: "2026-09-30"
author: "Robin, Giosué, Sébastien"
readTime: "6 min read"
tags: ["marvel", "community-detection", "text-mining", "network-analysis"]
summary: "The Marvel giant component becomes a typed graph when Wikipedia concordances supply evidence for family, foe, and ally labels inside and between Louvain communities."
wikilinks: ["exploring-degrees-marvel-dataset", "clique-percolation-k3"]
layout: full
---

A hyperlink tells us that two Marvel character pages are connected. It does not tell us *what kind* of connection it is. A link between Wolverine and Hulk could describe a rivalry, a team-up, or simply a passing mention.

This article adds a thin semantic layer to the Week 1 network: keep the graph edge, retain the sentence that justified it, and let a small keyword vocabulary propose a relationship label. The result is deliberately modest. It is a transparent reading aid, not a claim that a few keywords understand Marvel canon.

> [!NOTE]
> The supplied `marvel_pages.zip` contains all 303 pages. The applet uses the 277-node giant component of the Week 1 network: 1,421 undirected links, with 1,762 directed page references retained as evidence rows. Concordances are extracted from the archived source pages.

## The interactive question

Choose two characters or click an edge. The inspector shows:

1. the directed network link;
2. the sentence containing the other character;
3. the trigger word found by the classifier; and
4. the resulting edge color.

The graph below contains the full giant component. Use the two search fields to find a pair, click a visible relationship, or switch on the filters to isolate foes and between-community links.

<iframe src="assets/applets/marvel-relationship-concordance-giant.html" width="100%" height="850" frameborder="0" style="border: 1px solid var(--border-subtle); border-radius: 12px; overflow: hidden; background: var(--bg-surface); margin: 1.5rem 0;" title="Interactive: Marvel giant component with Wikipedia concordances and Louvain communities"></iframe>

## From page text to an edge label

For each directed Week 1 link, I looked up the source character's text in `marvel_pages.zip`, split it into sentences, and kept sentences containing the target character's page name. The classifier then searched the combined concordance for a small ordered vocabulary: family words such as `cousin` and `brother`, foe words such as `rival` and `fought`, and ally words such as `friend`, `partner`, and `crossover`. The first matching category becomes the displayed label; links with no match remain `unknown`.

The applet displays one representative evidence sentence for each undirected link and keeps the direction count, so a reader can distinguish a one-way reference from a mutual pair. Red edges are foes, green edges are allies, purple edges are family, and gray edges are unresolved. The label is evidence from the selected excerpt, not a ground-truth annotation.

## A graph edge is not a social relationship

The original graph has 303 characters and 1,784 directed hyperlinks. Its edge semantics are bibliographic: page A references page B. A text classifier changes the question from “who is mentioned?” to “what language appears near the mention?” Those are different measurements, and neither should be mistaken for a complete social graph.

This is also why the concordance matters. Without the sentence, a colored edge looks authoritative even when the trigger came from an incidental phrase. Showing the evidence lets a reader disagree with the label, replace the keyword dictionary, or add a better NLP model.

## Louvain communities and relationship location

I projected the directed Week 1 links to an undirected graph, kept its giant component, and ran NetworkX's Louvain modularity algorithm with seed 42. It found 8 communities among the 277 characters. Nodes are colored by community, and the inspector identifies whether a selected relationship stays inside one community or crosses between two.

The final toggles probe the question:

> **Do enemies sit in different communities?**

In this giant component, the 1,421 undirected links break down as follows:

| Relationship | Inside communities | Between communities |
| :--- | ---: | ---: |
| Family | 124 | 77 |
| Foe | 39 | 51 |
| Ally | 48 | 51 |
| Unknown | 524 | 507 |

Foe links are therefore more often between communities than inside them in this typed subset (51 versus 39). That is a descriptive result, not a general law: community assignments depend on the algorithm, graph projection, and resolution parameter. A degree-preserving null model would be the next test of whether this separation is stronger than the network's structure alone predicts.

That comparison is the important scientific move: the picture suggests a pattern, while a null model tests whether the pattern is more than the network's hubs and density already predict.

## Takeaways

- A hyperlink edge records reference structure; a concordance gives it inspectable textual evidence.
- Keyword labels are useful for a first interactive prototype, but ambiguous matches need review and confidence scores.
- Community coloring makes a hypothesis visible. A null-model comparison is still needed before claiming that enemies separate into narrative bubbles.

The result is a typed graph that can explain itself one sentence at a time, while remaining honest about what its classifier can and cannot see.
