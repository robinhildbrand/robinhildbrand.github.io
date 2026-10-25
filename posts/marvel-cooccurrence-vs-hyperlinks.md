---
title: "Citations vs. Co-occurrences: The Marvel Canon Gap"
date: "2026-10-15"
author: "Robin, Giosué, Sébastien"
readTime: "7 min read"
tags: ["marvel", "co-occurrence", "nlp", "text-mining", "network-analysis", "complex-networks"]
summary: "We extract character co-occurrences across 303 Marvel Wikipedia articles, compare the narrative network to the hyperlink citation graph, uncover the 'Canon Gap', and turn the structural divergence into an interactive detective game."
layout: full
wikilinks: ["exploring-degrees-marvel-dataset", "typing-marvel-relationships-with-concordances", "spot-the-intruder"]
---

In our [[exploring-degrees-marvel-dataset|first article]], we mapped the Marvel Universe through **hyperlink citations** — whenever a Wikipedia editor typed an internal link from Character A's page to Character B's page, we drew an arrow. That gave us 303 characters, 1,784 directed links, and a heavy-tailed degree distribution dominated by Spider-Man.

In [[typing-marvel-relationships-with-concordances|our concordance study]], we added a semantic layer to classify those existing hyperlinks as allies, foes, or family. But one fundamental question remained unexplored:

> **What happens if we stop asking what Wikipedia editors *hyperlink*, and start measuring who actually shares the *story prose*?**

When two characters appear in the same sentence or paragraph, they are co-present in narrative space. They fight together, converse in the same room, or join the same mission. A hyperlink, by contrast, is bibliographic: an editorial choice to cite a related entry.

By mining the full Wikipedia text for all 303 characters from `marvel_pages.zip`, we build the complete **Marvel Entity Co-occurrence Network** and place it side-by-side against the hyperlink graph. The result is what we call the **Canon Gap** — hundreds of deep comic relationships that live entirely in the prose without a single hyperlink, and hundreds of bibliographic citations between heroes who never share a scene.

---

## 1. From Prose to Structured Edges: Modeling Choices in NLP

Turning raw text into a network is not a passive mechanical scan; it is an active modeling process full of critical choices. As introduced in [Week 7 of Social Graphs and Interactions](https://sunelehmann.com/socialgraphs2026-web/weeks/week7.html), Named Entity Recognition (NER) and entity resolution require answering three foundational questions before a single edge can be drawn:

```
[Raw Wikipedia Text] 
       │
       ▼
 [Span Extraction] ────► Recognizes token spans ("Tony Stark", "Iron Man")
       │
       ▼
[Entity Resolution] ───► Maps aliases & alter egos to canonical node ID
       │
       ▼
 [Co-occurrence] ──────► Connects pairs sharing a unit (Sentence vs. Paragraph)
```

### The Alias and Entity Resolution Trap
Off-the-shelf NER pipelines often stumble on superhero text:
- Spans like *Iron Man* are frequently misclassified or missed entirely in general news-trained models.
- Spans like *Black Widow* can be tagged as an organization rather than a person.
- A character like Wolverine is referred to as *Logan*, *James Howlett*, *Wolverine*, or *Weapon X*. Failing to resolve these aliases splits a major superhero hub into four disconnected fragments.
- Conversely, careless matching creates runaway mega-hubs: over half of Wikipedia's article titles contain parenthetical disambiguations like `Wolverine_(character)` or `Storm_(Marvel_Comics)`. Searching for raw title strings misses the character in natural sentences, while naively treating terms like `"character"` or `"comics"` as aliases connects every superhero on Earth to each other!

By compiling a curated alias resolver across all 303 character pages (linking civilian alter egos such as Peter Parker, Bruce Banner, and Steve Rogers to their canonical superhero nodes while stripping generic metadata), we resolved each character accurately.

### The Unit of Co-occurrence: Sentence vs. Paragraph
What does it mean for two characters to "co-occur"?
- **Sentence-level ($w_{sent}$)**: The strictest definition of interaction. Two characters must be mentioned within the same sentence boundary. This captures direct tactical team-ups, battles, dialogues, and immediate family ties.
- **Paragraph-level ($w_{para}$)**: A broader narrative window. Two characters appear within the same thematic paragraph block or storyline recap.

---

## 2. Interactive Explorable: Network Detective & Dual Graph

Test your intuition in the interactive lab below. 

In **Detective Game Mode**, examine 15 real Marvel mystery pairings with authentic comic story excerpts and deduce whether their connection is **Both** (documented hyperlink and narrative co-occurrence), **Citation Only** (hyperlinked, but zero story sentences), **Ghost Link** (frequent story co-occurrence, but zero Wikipedia hyperlinks), or a **Decoy**.

In **Graph Explorer Mode**, toggle between the shared, citation-only, and ghost-link layers, adjust co-occurrence thresholds, and inspect real concordance excerpts for any pair.

<iframe src="assets/applets/marvel-cooccurrence-game.html" width="100%" height="860" frameborder="0" style="border: 1px solid var(--border-subtle); border-radius: 12px; overflow: hidden; background: var(--bg-surface); margin: 1.5rem 0;" title="Interactive: Marvel Co-occurrence vs Hyperlink Network and Detective Game"></iframe>

---

## 3. Structural Comparison: How the Networks Differ

Comparing the undirected Wikipedia hyperlink graph ($G_{link}$) with the sentence co-occurrence graph ($G_{sent}$) and paragraph co-occurrence graph ($G_{para}$) reveals striking structural shifts:

| Structural Metric | Wikipedia Links ($G_{link}$) | Sentence Co-occ ($w \ge 1$) | Sentence Co-occ ($w \ge 2$) | Paragraph Co-occ ($w \ge 1$) |
| :--- | :---: | :---: | :---: | :---: |
| **Nodes ($N$)** | 303 | 303 | 232 | 303 |
| **Edges ($M$)** | 1,434 | 1,504 | 724 | 3,576 |
| **Average Degree $\langle k \rangle$** | 9.47 | 9.93 | 6.24 | 23.60 |
| **Network Density $\rho$** | 0.0313 | 0.0329 | 0.0270 | 0.0782 |
| **Clustering Coefficient $C$** | 0.307 | **0.404** | 0.394 | **0.579** |
| **Giant Component Size** | 277 (91.4%) | 260 (85.8%) | 225 (74.3%) | 280 (92.4%) |
| **Isolated Characters** | 17 | 43 | 71 | 23 |
| **Modularity $Q$ (Louvain)** | 0.385 | **0.495** | **0.543** | 0.336 |

### Observation 1: Almost Identical Edge Counts, Completely Different Topology
Notice that at $w \ge 1$, the sentence co-occurrence network has **1,504 edges** — remarkably close to the **1,434 undirected links** of the Wikipedia citation graph. Yet their **Jaccard edge overlap is only 0.296**:
- **762 edges** exist in **both** networks (*Canonical Anchors*).
- **672 edges** exist **only as hyperlinks** (*Bibliographic Citations*).
- **728 edges** exist **only in sentences** (*Narrative Ghost Links*).

Only ~53% of Wikipedia's hyperlinks are reflected in sentence co-occurrences, and nearly half of the characters' narrative interactions never received a Wikipedia hyperlink!

### Observation 2: Why Co-occurrence Graphs Cluster More Tightly
The average clustering coefficient jumps from **0.307** in the hyperlink graph to **0.404** in sentence co-occurrence and **0.579** in paragraph co-occurrence.

Why? In prose, characters rarely appear in isolated pairwise vacuums. Comic arcs depict superhero squads fighting a villain together or attending a team meeting. When an author writes:
> *"Cyclops, Jean Grey, and Wolverine confronted Magneto on Asteroid M..."*

that single sentence simultaneously generates a complete **3-clique** (triangle) between the heroes. Narrative co-occurrence naturally produces high local clustering and dense triad closure.

### Observation 3: High Modularity and Story Silos
Sentence co-occurrence increases Louvain modularity from $Q = 0.385$ to $Q = 0.495$ (and $Q = 0.543$ at $w \ge 2$). In the hyperlink graph, cross-references between different parts of the Marvel Universe are common (e.g. an article referencing Doctor Strange's sorcery or Spider-Man's popularity). But narrative sentences remain firmly locked inside thematic story silos: X-Men mutants co-occur with mutants, street-level vigilantes with street heroes, and cosmic heroes in deep space.

---

## 4. The Degree Distribution: Heavy Tails Across Both Worlds

Does the co-occurrence network change who rules the Marvel Universe?

Both networks exhibit **heavy-tailed degree distributions**: the vast majority of characters have very few connections (median degree $\le 4$), while an elite handful of iconic hubs possess degrees stretching past 60 to 120. 

> [!NOTE]
> As established in our project conventions, we describe the observed degree distribution as **heavy-tailed**, not scale-free. A scale-free power law is an idealized model property, whereas real-world comic networks with 303 nodes show empirical heavy-tail decay shaped by narrative prominence and publication longevity.

```
Degree Rank | Character             | Hyperlink Degree | Sentence Co-occ Degree | Divergence
---------------------------------------------------------------------------------------------
1           | Spider-Man            | 106              | 122                    | +16
2           | Hulk                  | 65               | 79                     | +14
3           | Wolverine             | 63               | 78                     | +15
4           | Doctor Strange        | 57               | 44                     | -13
5           | Deadpool              | 41               | 50                     | +9
6           | She-Hulk              | 37               | 48                     | +11
7           | Ghost Rider (Blaze)   | 15               | 46                     | +31
8           | Phoenix Force         | 32               | 45                     | +13
9           | Venom                 | 29               | 44                     | +15
10          | Black Panther         | 31               | 38                     | +7
```

### The Top Titans
**Spider-Man**, **Hulk**, and **Wolverine** remain the unchallenged triumvirate of Marvel across both networks. In fact, their dominance is even stronger in text: Spider-Man's degree climbs from 106 to **122**, appearing in narrative scenes with over 40% of all superheroes in the dataset.

### The "Doctor Strange Asymmetry"
Doctor Strange is one of the rare characters whose **hyperlink degree (57) significantly exceeds his co-occurrence degree (44)**. As the Sorcerer Supreme, numerous Wikipedia pages link to Doctor Strange's entry bibliographically — noting his role in cosmic events, artifacts, or mystic realms — without him sharing direct dialogue or action in the character's narrative prose.

### The "Ghost Rider Surge"
Ghost Rider (Johnny Blaze) has only **15 category hyperlinks**, yet commands **46 sentence co-occurrences**! As an occult nomad and Midnight Son, Blaze appears frequently in crossing battle sequences and anthology team-ups, yet editors seldom linked his specific Category page in character sidebars.

---

## 5. Anatomy of the Canon Gap: Concrete Excerpts

What actually produces a Ghost Link or a Link-Only connection? Reading the underlying concordance sentences reveals the editorial and narrative mechanisms at work:

### The Top Ghost Links: Deep Lore Without Hyperlinks

1. **Mockingbird & Hawkeye (44 sentence co-occurrences, 0 links)**:
   > *"The series was a crossover between Black Widow and the ongoing Hawkeye & Mockingbird series."*
   
   Clint Barton and Bobbi Morse were famously married and led the West Coast Avengers together for years. Why was the edge missing from the Week 1 network? Because Wikipedia's category scraper recorded links pointing to *Hawkeye (character)* rather than the specific category redirect, leaving their extensive shared prose completely unlinked in the graph!

2. **Human Torch & Toro (16 sentence co-occurrences, 0 links)**:
   > *"However, word of Basil Frankenstein's activities leaked out to the Allied Forces and the Human Torch and Toro went out to investigate."*
   
   During World War II, the original android Human Torch and his young partner Toro fought side-by-side in Marvel's Invaders. Their relationship is a historic cornerstone of 1940s Marvel lore, vividly described in narrative recaps, but neglected by modern hyperlinking editors.

3. **Luke Cage & White Tiger (16 sentence co-occurrences, 0 links)**:
   > *"Iron Fist starred in his own solo series in the 1970s, and shared the title Power Man and Iron Fist with Luke Cage before incorporating White Tiger into Heroes for Hire."*

### The Link-Only Pairs: Bibliographic Footnotes

In contrast, why do pairs like **U.S. Agent & War Machine**, **Noh-Varr & Rocket Raccoon**, or **Sentry & Fin Fang Foom** have Wikipedia links but zero shared sentences?
- **Roster & Category Listings**: An article lists former West Coast Avengers members in a bulleted section or table without them interacting in a sentence.
- **Creator Footnotes**: Star Brand and Starr the Slayer are hyperlinked because both were created or edited by writer Roy Thomas, not because the prehistoric warrior met the modern wielder of the planetary glyph.
- **Universe Lore & "See Also"**: Encyclopedic pages link to famous dragons (Fin Fang Foom) or cosmic races as background world-building context.

---

## 6. Conclusion: Which Network is "Real"?

When we ask *who is connected in the Marvel Universe?*, the answer depends entirely on what we choose to measure:

- If you measure **bibliographic relevance**, the Wikipedia hyperlink network measures the encyclopedic architecture built by human curators.
- If you measure **narrative proximity**, the co-occurrence network reconstructs the actual dramatic encounters, team formations, and comic book battles.

Neither network is the single "true" Marvel Universe. The hyperlink network reflects how editors organize knowledge, while the co-occurrence network reflects how storytellers craft character drama. By contrasting the two, the **Canon Gap** transforms what might have looked like noise into a rich map of storytelling and curation.
