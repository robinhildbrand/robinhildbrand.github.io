---
title: "Exploring Degrees in the Marvel Dataset"
date: "2026-09-04"
author: "Robin, Giosué, Sébastien"
readTime: "4 min read"
tags: ["marvel", "network-analysis", "degree-distribution", "complex-networks"]
summary: "An empirical analysis of node degrees, in/out-degree asymmetries, power-law distributions, and central superhero hubs across the Wikipedia Marvel Comics network."
wikilinks: ["network-models-marvel-comparison"]
---

Every character in the Marvel Universe is connected to every other character through stories, teams, and cameos. In Wikipedia, those connections are concrete: **hyperlink citations**. If two pages link to each other, the characters are connected.

Count those links and you reveal the hidden social structure of Marvel — who is a *star*, who is a *glue character*, and who sits at the edge of the universe.

> [!NOTE]
> We built the **Marvel Superhero Network** from the Wikipedia category *Category:Marvel Comics superheroes*. It contains 303 heroes and 1,784 directed links — a link from character **A** to character **B** means A's Wikipedia page references B.

---

## What is a degree?

A character's **degree** is simply the number of connections they have. In a directed network like this one, it splits in two:

- **In-degree** — arrows pointing **at** you. How many other characters name you. A measure of *popularity*.
- **Out-degree** — arrows leaving **you**. How many other characters you name. A measure of *cross-referencing*.

Here is Spider-Man's own slice of the network. The arrows tell the whole story:

```network
[Wolverine] -> [Spider-Man] : in
[Hulk] -> [Spider-Man] : in
[Venom] -> [Spider-Man] : in
[Spider-Man] -> [Hulk] : out
[Spider-Man] -> [Doctor Strange] : out
```

So Spider-Man has an **in-degree of 3** (three heroes point at him) and an **out-degree of 2** (he points at two heroes). Simple, right? Now scale that up to 303 characters.

---

## 1. The Big Picture

The whole network in one table:

| Metric | Value | What it means |
| :--- | :---: | :--- |
| **Characters ($N$)** | 303 | Nodes in the network |
| **Connections ($M$)** | 1,784 | Directed hyperlinks between pages |
| **Average degree** | 5.89 | Average links into/out of a page |
| **Median in-degree** | 3 | Half of all heroes get ≤ 3 incoming links |
| **Median out-degree** | 4 | Half of all heroes link to ≤ 4 others |
| **Reciprocity** | 39.2% | Share of links that go both ways |
| **Components** | 2 clusters + 17 | One giant cluster of 277 heroes, one small island of 9, and 17 fully isolated heroes |

The average degree is simply the total number of links divided by the number of characters:

$$\langle k \rangle = \frac{M}{N} = \frac{1784}{303} \approx 5.89$$

> [!TIP]
> A reciprocity of **39.2%** is unusually high for a web network (most of the web sits below 20%). It makes sense: Marvel's shared continuity means if Spider-Man shows up in Wolverine's story, Wolverine usually shows up in Spider-Man's too.

---

## 2. Who is the most connected?

### The icons: by in-degree (popularity)

These are the characters the rest of the universe can't stop mentioning.

| Rank | Hero | In-Degree | % of heroes linking to them |
| :---: | :--- | :---: | :---: |
| 1 | **Spider-Man** | **106** | **35%** |
| 2 | **Hulk** | 64 | 21% |
| 3 | **Wolverine** | 60 | 20% |
| 4 | **Doctor Strange** | 50 | 17% |
| 5 | **Deadpool** | 33 | 11% |
| 6 | **She-Hulk** | 29 | 10% |
| 7 | **Scarlet Witch** | 28 | 9% |
| 8 | **Black Panther** | 27 | 9% |
| 9 | **Cyclops** | 26 | 9% |
| 10 | **Luke Cage** | 25 | 8% |

**More than 1 in 3 heroes mention Spider-Man on their page.** Hulk and Wolverine complete the top three — together they account for over a fifth of all incoming links.

<figure class="hero-figure">
  <img src="assets/images/heroes/spider-man.png" alt="Spider-Man — the top hub of the Marvel network">
  <img src="assets/images/heroes/hulk.png" alt="Hulk — the second-biggest hub">
  <img src="assets/images/heroes/wolverine.jpg" alt="Wolverine — the third-biggest hub">
  <figcaption>Spider-Man, Hulk, and Wolverine — the Marvel network's top three hubs.</figcaption>
</figure>

### The connectors: by out-degree (cross-referencing)

Different characters are the *mentioners* rather than the mentioned:

| Rank | Hero | Out-Degree | Why |
| :---: | :--- | :---: | :--- |
| 1 | **Betsy Braddock (Psylocke)** | 28 | X-Men, Captain Britain, Excalibur — a bridge character |
| 2 | **Cloak and Dagger** | 24 | Duo that crosses into many storylines |
| 3 | **Adam Warlock** | 22 | Links cosmic Marvel with Earth-based teams |
| 4 | **Venom** | 21 | Symbiote lore + Spider-Man mythos |
| 5 | **She-Hulk** | 20 | Avengers, Fantastic Four, legal crossovers |
| 6 | **Deadpool** | 19 | Fourth-wall breaking cameos everywhere |

High out-degree characters live at the *intersection* of franchises. Psylocke, for example, ties together British Marvel heroes, mutants, and multiple teams.

---

## 3. Explore the core hubs

Below is the **mutual interaction network** of the 12 most-connected hubs — Spider-Man sits in the middle, and smaller clusters (the X-Men, the symbiotes) orbit around him.

```network
[Spider-Man] { size: 26 }
[Wolverine] { size: 22 }
[Hulk] { size: 21 }
[Doctor Strange] { size: 20 }
[Deadpool] { size: 18 }
[She-Hulk] { size: 17 }
[Scarlet Witch] { size: 16 }
[Phoenix] { size: 16 }
[Black Panther] { size: 15 }
[Emma Frost] { size: 15 }
[Venom] { size: 15 }
[Cyclops] { size: 15 }
[Spider-Man] -> [Hulk]
[Spider-Man] -> [Venom]
[Wolverine] -> [Spider-Man]
[Wolverine] -> [Hulk]
[Wolverine] -> [Cyclops]
[Wolverine] -> [Deadpool]
[Wolverine] -> [Phoenix]
[Hulk] -> [Spider-Man]
[Hulk] -> [Wolverine]
[Hulk] -> [She-Hulk]
[Doctor Strange] -> [Spider-Man]
[Doctor Strange] -> [Hulk]
[Doctor Strange] -> [Scarlet Witch]
[She-Hulk] -> [Hulk]
[She-Hulk] -> [Spider-Man]
[She-Hulk] -> [Wolverine]
[Deadpool] -> [Spider-Man]
[Deadpool] -> [Wolverine]
[Deadpool] -> [Venom]
[Cyclops] -> [Wolverine]
[Cyclops] -> [Phoenix]
[Cyclops] -> [Emma Frost]
[Emma Frost] -> [Cyclops]
[Emma Frost] -> [Phoenix]
[Phoenix] -> [Cyclops]
[Phoenix] -> [Emma Frost]
[Black Panther] -> [Doctor Strange]
[Venom] -> [Spider-Man]
```

---

## 4. A few mega-hubs, many minor heroes

If connections were random, links would spread **evenly** and most heroes would have similar degrees. The real Marvel network looks nothing like that:

```network
[Spider-Man] { size: 26 }
[Cannonball] { size: 6 }
[Dum Dum Dugan] { size: 6 }
[Karma] { size: 6 }
[Forge] { size: 6 }
[Lockheed] { size: 6 }
[Spider-Man] -> [Cannonball]
[Spider-Man] -> [Dum Dum Dugan]
[Spider-Man] -> [Karma]
[Spider-Man] -> [Forge]
[Spider-Man] -> [Lockheed]
```

One giant node, surrounded by tiny ones. That is the **shape** of the whole dataset:

- **62% of heroes** are mentioned by **3 or fewer** others.
- The **top 3 heroes alone** hold **230 incoming links** — about 13% of the entire network's connections.
- The **top 10** hold over a quarter of everything.

This is called a **heavy-tailed, scale-free distribution**, and it follows a simple power law:

$$P(k) \propto k^{-\gamma}, \quad 2 < \gamma < 3$$

Real networks get this way through **preferential attachment**: writers naturally link new characters to the famous ones. The rich get richer — Spider-Man gets mentioned *because* he's already been mentioned. Random networks (the *Erdős–Rényi* model) cannot produce hubs this extreme; the chance of a node with 106 links in a purely random version of this network is less than 1 in 10⁶⁰.

---

## How the numbers were computed

No code needed here — the pipeline was: load the node/edge spreadsheet (`week1_nodes.tsv`, `week1_edges.tsv`), build a **directed graph**, and count in-degree, out-degree, and reciprocity for every character using standard Python libraries (`pandas` + `networkx`).

---

## Key Takeaways

1. **Popularity is extremely concentrated.** Spider-Man, Hulk, and Wolverine dominate — most heroes are barely connected.
2. **Who writes matters as much as who is written about.** In-degree reveals icons; out-degree reveals the cross-franchise glue characters.
3. **Marvel is a scale-free network.** Robust to random failures, fragile to the loss of its top hubs.

Next up: we take these degree insights and dig into **community structure**, **centrality**, and the **spectral** properties of the Marvel graph.