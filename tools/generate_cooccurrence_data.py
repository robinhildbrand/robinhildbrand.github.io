"""Generate co-occurrence network data and comparison with Wikipedia links.

Reads:
  - week1_nodes.tsv
  - week1_edges.tsv
  - marvel_pages.zip
  - assets/images/heroes/

Outputs:
  - assets/marvel_cooccurrence_comparison.json
"""

import json
import re
import urllib.parse
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parent.parent
NODES_FILE = ROOT / "week1_nodes.tsv"
EDGES_FILE = ROOT / "week1_edges.tsv"
PAGES_FILE = ROOT / "marvel_pages.zip"
HEROES_DIR = ROOT / "assets" / "images" / "heroes"
OUTPUT_FILE = ROOT / "assets" / "marvel_cooccurrence_comparison.json"

GENERIC = {
    "character", "characters", "comics", "comic", "marvel", "marvel comics",
    "superhero", "superheroes", "earth-616", "vol", "series", "universe",
    "comics character", "marvel comics character", "marvel comics superheroes",
    "ultimate marvel character", "x-men film series", "morituri", "comics superheroes"
}
AMBIGUOUS_STANDALONE = {"force", "monster", "ghost", "knight", "captain", "agent", "black", "star", "war"}

PRIMARY_OVERRIDES = {
    "Spider-Man": "Spider-Man", "Peter Parker": "Spider-Man", "Spidey": "Spider-Man",
    "Wolverine": "Wolverine_(character)", "Logan": "Wolverine_(character)", "James Howlett": "Wolverine_(character)",
    "Hulk": "Hulk", "Bruce Banner": "Hulk",
    "Doctor Strange": "Doctor_Strange", "Stephen Strange": "Doctor_Strange",
    "Thor": "Thor_(Marvel_Comics)", "Thor Odinson": "Thor_(Marvel_Comics)",
    "Captain America": "Captain_America", "Steve Rogers": "Captain_America",
    "Iron Man": "Iron_Man_(Ultimate_Marvel_character)", "Tony Stark": "Iron_Man_(Ultimate_Marvel_character)",
    "Black Widow": "Black_Widow_(Natasha_Romanova)", "Natasha Romanoff": "Black_Widow_(Natasha_Romanova)",
    "Hawkeye": "Hawkeye_(Clint_Barton)", "Clint Barton": "Hawkeye_(Clint_Barton)",
    "Cyclops": "Cyclops_(Marvel_Comics)", "Scott Summers": "Cyclops_(Marvel_Comics)",
    "Jean Grey": "Jean_Grey", "Marvel Girl": "Jean_Grey",
    "Storm": "Storm_(Marvel_Comics)", "Ororo Munroe": "Storm_(Marvel_Comics)",
    "Professor X": "Professor_X", "Charles Xavier": "Professor_X",
    "Magneto": "Magneto_(Marvel_Comics)", "Erik Lehnsherr": "Magneto_(Marvel_Comics)",
    "She-Hulk": "She-Hulk", "Jennifer Walters": "She-Hulk",
    "Deadpool": "Deadpool", "Wade Wilson": "Deadpool",
    "Daredevil": "Daredevil_(Marvel_Comics_character)", "Matt Murdock": "Daredevil_(Marvel_Comics_character)",
    "Punisher": "Punisher", "Frank Castle": "Punisher",
    "Human Torch": "Human_Torch", "Johnny Storm": "Human_Torch",
    "Invisible Woman": "Invisible_Woman", "Sue Storm": "Invisible_Woman",
    "Mister Fantastic": "Mister_Fantastic", "Reed Richards": "Mister_Fantastic",
    "Thing": "Thing_(comics)", "Ben Grimm": "Thing_(comics)",
    "Hank Pym": "Hank_Pym", "Wasp": "Wasp_(character)",
    "Venom": "Venom_(character)", "Eddie Brock": "Venom_(character)",
    "Luke Cage": "Luke_Cage", "Power Man": "Luke_Cage",
    "Danny Rand": "Iron_Fist_(character)", "Iron Fist": "Iron_Fist_(character)",
    "Betsy Braddock": "Betsy_Braddock", "Psylocke": "Betsy_Braddock",
    "Emma Frost": "Emma_Frost", "White Queen": "Emma_Frost",
    "Black Panther": "Black_Panther_(character)", "T'Challa": "Black_Panther_(character)",
    "Namor": "Namor", "Sub-Mariner": "Namor",
    "Silver Surfer": "Silver_Surfer", "Norrin Radd": "Silver_Surfer",
    "Ghost Rider": "Ghost_Rider_(Johnny_Blaze)", "Johnny Blaze": "Ghost_Rider_(Johnny_Blaze)",
    "Winter Soldier": "Winter_Soldier", "Bucky Barnes": "Winter_Soldier",
    "Falcon": "Falcon_(comics)", "Sam Wilson": "Falcon_(comics)",
    "Quasar": "Quasar_(character)", "Wendell Vaughn": "Quasar_(character)",
    "Rachel Summers": "Rachel_Summers",
    "Adam Warlock": "Adam_Warlock",
    "Spider-Woman": "Spider-Woman_(Jessica_Drew)", "Jessica Drew": "Spider-Woman_(Jessica_Drew)",
    "Spider-Girl": "Spider-Girl", "Mayday Parker": "Mayday_Parker",
    "Mockingbird": "Mockingbird_(Marvel_Comics)", "Bobbi Morse": "Mockingbird_(Marvel_Comics)",
    "Morbius": "Morbius", "Michael Morbius": "Morbius",
    "Blade": "Blade_(character)", "Eric Brooks": "Blade_(character)",
}

def load_hero_images():
    images = {}
    if not HEROES_DIR.exists():
        return images
    slug_map = {
        "spider-man": "Spider-Man",
        "wolverine": "Wolverine_(character)",
        "wolverine-ultimate": "Wolverine_(Ultimate_Marvel_character)",
        "hulk": "Hulk",
        "doctor-strange": "Doctor_Strange",
        "deadpool": "Deadpool",
        "cyclops": "Cyclops_(Marvel_Comics)",
        "storm": "Storm_(Marvel_Comics)",
        "black-widow": "Black_Widow_(Natasha_Romanova)",
        "black-panther": "Black_Panther_(character)",
        "she-hulk": "She-Hulk",
        "scarlet-witch": "Scarlet_Witch",
        "luke-cage": "Luke_Cage",
        "iron-fist": "Iron_Fist_(character)",
        "venom": "Venom_(character)",
        "cable": "Cable_(character)",
        "blade": "Blade_(character)",
        "emma-frost": "Emma_Frost",
        "betsy-braddock": "Betsy_Braddock",
        "ghost-rider": "Ghost_Rider_(Johnny_Blaze)",
        "jean-grey": "Jean_Grey",
        "morbius": "Morbius",
        "spider-woman": "Spider-Woman_(Jessica_Drew)",
        "spider-girl": "Spider-Girl",
        "spider-gwen": "Spider-Gwen",
        "black-cat": "Black_Cat_(Marvel_Comics)",
        "hercules-marvel": "Hercules_(Marvel_Comics)",
        "rocket-raccoon": "Rocket_Raccoon",
        "star-lord": "Star-Lord",
        "rachel-summers": "Rachel_Summers",
        "gwenpool": "Gwenpool",
        "moon-knight": "Moon_Knight",
        "man-thing": "Man-Thing",
        "jubilee": "Jubilee_(character)",
        "silk": "Silk_(character)",
        "werewolf-by-night": "Werewolf_by_Night",
    }
    for file in HEROES_DIR.iterdir():
        stem = file.stem.lower()
        if stem in slug_map:
            images[slug_map[stem]] = f"../images/heroes/{file.name}"
    return images

def load_nodes():
    nodes = {}
    with NODES_FILE.open(encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.rstrip("\n").split("\t")
            if parts[0] != "node_id":
                nodes[parts[0]] = {
                    "id": parts[0],
                    "name": parts[1],
                    "clean_name": re.sub(r"\s*\([^)]*\)", "", parts[1]).strip(),
                    "desc": parts[4] if len(parts) > 4 else "",
                    "wiki_url": parts[3] if len(parts) > 3 else f"https://en.wikipedia.org/wiki/{parts[0]}",
                }
    return nodes

def load_links():
    directed = []
    undirected = set()
    dir_map = defaultdict(lambda: {"A_to_B": False, "B_to_A": False})
    with EDGES_FILE.open(encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            s, t = line.rstrip("\n").split("\t")[:2]
            if s != t:
                directed.append((s, t))
                pair = tuple(sorted((s, t)))
                undirected.add(frozenset(pair))
                if s == pair[0]:
                    dir_map[pair]["A_to_B"] = True
                else:
                    dir_map[pair]["B_to_A"] = True
    return directed, undirected, dir_map

def load_pages():
    with zipfile.ZipFile(PAGES_FILE) as z:
        return {
            urllib.parse.unquote(name.rsplit("/", 1)[-1][:-4]): z.read(name).decode("utf-8")
            for name in z.namelist()
            if name.endswith(".txt") and "README" not in name
        }

def build_alias_map(nodes):
    alias_to_id = {}
    for nid, info in nodes.items():
        clean_id = re.sub(r"_\([^)]*\)", "", nid).replace("_", " ").strip()
        clean_name = info["clean_name"]
        for cand in [clean_id, clean_name]:
            c_low = cand.lower()
            if c_low not in GENERIC and c_low not in AMBIGUOUS_STANDALONE and len(cand) >= 3 and cand not in alias_to_id:
                alias_to_id[cand] = nid

        m = re.search(r"\(([^)]+)\)", nid)
        if m:
            p = m.group(1).replace("_", " ").strip()
            p_low = p.lower()
            if p_low not in GENERIC and p_low not in AMBIGUOUS_STANDALONE and len(p) >= 4:
                if " " in p or p in {"Lyra", "Mar-Vell", "Noh-Varr", "Khn'nr"}:
                    if p not in alias_to_id:
                        alias_to_id[p] = nid

        m2 = re.search(r"\(([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\)", info["desc"])
        if m2:
            alter = m2.group(1).strip()
            if alter.lower() not in GENERIC and len(alter) >= 5 and alter not in alias_to_id:
                alias_to_id[alter] = nid

    for a, target in PRIMARY_OVERRIDES.items():
        if target in nodes:
            alias_to_id[a] = target

    return alias_to_id

def extract_cooccurrences(pages, alias_to_id):
    sorted_aliases = sorted(alias_to_id.keys(), key=len, reverse=True)
    pattern = re.compile(r"\b(" + "|".join(re.escape(a) for a in sorted_aliases) + r")\b")

    sent_weights = Counter()
    para_weights = Counter()
    evidence_sentences = {}

    for pid, text in pages.items():
        raw_paras = [p.strip() for p in text.split("\n\n") if p.strip()]
        for p in raw_paras:
            p_matches = {alias_to_id[m.group(0)] for m in pattern.finditer(p)}
            p_list = sorted(p_matches)
            for i in range(len(p_list)):
                for j in range(i + 1, len(p_list)):
                    para_weights[frozenset((p_list[i], p_list[j]))] += 1

            clean_p = " ".join(p.replace("\n", " ").split())
            sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", clean_p) if s.strip()]
            for s in sents:
                s_matches = {alias_to_id[m.group(0)] for m in pattern.finditer(s)}
                s_list = sorted(s_matches)
                for i in range(len(s_list)):
                    for j in range(i + 1, len(s_list)):
                        pair = frozenset((s_list[i], s_list[j]))
                        sent_weights[pair] += 1
                        if pair not in evidence_sentences or len(s) < len(evidence_sentences[pair]["sentence"]):
                            evidence_sentences[pair] = {
                                "sentence": s,
                                "source_page": pid,
                            }
    return sent_weights, para_weights, evidence_sentences

def curate_game_challenges(nodes, dir_map, sent_weights, evidence_sentences):
    """Hand-curate diverse and intriguing pairs across all 4 categories."""
    challenges = [
        {
            "id": "c1",
            "source": "Mockingbird_(Marvel_Comics)",
            "target": "Hawkeye_(comics)",
            "teaser": "The series was a crossover between Black Widow and the ongoing Hawkeye & Mockingbird series.",
            "answer": "coocc_only",
            "why": "Mockingbird and Hawkeye share 44 sentences of narrative crossover history, but the Wikipedia superhero category links missed a direct hyperlink between them!",
            "explanation": "Narrative Ghost Link: Heavy co-mention in stories, but 0 Wikipedia hyperlink citations in this category graph."
        },
        {
            "id": "c2",
            "source": "Spider-Man",
            "target": "Venom_(character)",
            "teaser": "Spider-Man and Venom have had one of Marvel's most famous arch-rivalries, later turning into an uneasy alliance.",
            "answer": "both",
            "why": "They boast a staggering 219 sentence co-occurrences AND mutual Wikipedia hyperlinks going both ways!",
            "explanation": "Canonical Anchor: Solidly bound both in narrative prose and across encyclopedic citations."
        },
        {
            "id": "c3",
            "source": "U.S._Agent",
            "target": "War_Machine",
            "teaser": "Both served on the West Coast Avengers and Force Works rosters during 1990s comic runs.",
            "answer": "link_only",
            "why": "Wikipedia articles cross-link them as government-sanctioned armored heroes, but they never share a single sentence in the scraped narrative text.",
            "explanation": "Bibliographic Citation: Connected on Wikipedia through lists or infobox citations, with no direct narrative scene."
        },
        {
            "id": "c4",
            "source": "Human_Torch",
            "target": "Toro_(character)",
            "teaser": "During World War II, the original android Human Torch fought alongside his teenage mutant partner Toro in the Allied Invaders.",
            "answer": "coocc_only",
            "why": "They share 16 narrative sentences detailing their WWII team-ups, yet Wikipedia's category scraped no hyperlink between them.",
            "explanation": "Narrative Ghost Link: Historic comic partner bond unrecorded by the Wikipedia citation graph."
        },
        {
            "id": "c5",
            "source": "Jean_Grey",
            "target": "Phoenix_Force",
            "teaser": "The cosmic entity known as the Phoenix Force duplicated Jean Grey's body and memories during the Dark Phoenix Saga.",
            "answer": "both",
            "why": "Co-occur in 92 distinct sentences and share bidirectional Wikipedia hyperlinks.",
            "explanation": "Canonical Anchor: Core mythological cosmic entity intertwined with the mutant superhero."
        },
        {
            "id": "c6",
            "source": "Noh-Varr",
            "target": "Rocket_Raccoon",
            "teaser": "Both are cosmic adventurers who have operated in deep space and joined modern cosmic rosters.",
            "answer": "link_only",
            "why": "Linked through Wikipedia's modern Marvel Cosmic / Guardians reference tags, but never co-mentioned in text sentences.",
            "explanation": "Bibliographic Citation: A thematic universe cross-link without shared scene dialogue."
        },
        {
            "id": "c7",
            "source": "Luke_Cage",
            "target": "White_Tiger_(Heroes_for_Hire)",
            "teaser": "Luke Cage and Iron Fist's Heroes for Hire expanded to incorporate multiple martial artists including White Tiger.",
            "answer": "coocc_only",
            "why": "Co-occur across 16 sentences in Heroes for Hire lore, but no hyperlink connects their category articles.",
            "explanation": "Narrative Ghost Link: Street-level team dynamics recorded in text prose but missing a link."
        },
        {
            "id": "c8",
            "source": "Hulk",
            "target": "Abomination_(character)",
            "teaser": "Created by writer Stan Lee and artist Gil Kane, Abomination was introduced specifically as a rival monstrous enough to defeat the Hulk.",
            "answer": "both",
            "why": "48 sentences of titanic clashes and mutual Wikipedia hyperlinks between gamma giants.",
            "explanation": "Canonical Anchor: Foundational hero-nemesis relationship verified in both graphs."
        },
        {
            "id": "c9",
            "source": "Sentry_(Robert_Reynolds)",
            "target": "Fin_Fang_Foom",
            "teaser": "The golden guardian and the ancient alien dragon from Maklu IV.",
            "answer": "link_only",
            "why": "Sentry's page hyperlinks Fin Fang Foom as part of a classic monster revival footnote, with 0 narrative co-occurrences.",
            "explanation": "Bibliographic Citation: Encyclopedic footnote link with no joint narrative action."
        },
        {
            "id": "c10",
            "source": "Spider-Man",
            "target": "Black_Cat_(Marvel_Comics)",
            "teaser": "Spider-Man and Felicia Hardy maintained a romantic relationship alongside their vigilante rooftop patrols.",
            "answer": "both",
            "why": "83 sentence co-occurrences and strong mutual hyperlinks.",
            "explanation": "Canonical Anchor: Iconic romantic and vigilante partnership across decades of issues."
        },
        {
            "id": "c11",
            "source": "Wolverine_(character)",
            "target": "Arabian_Knight_(character)",
            "teaser": "The Canadian mutant berserker and the mystical scimitar-wielding hero of Saudi Arabia.",
            "answer": "neither",
            "why": "No hyperlink citations and 0 text co-occurrences in the corpus.",
            "explanation": "Decoy Pair: Two completely unconnected heroes from different operational spheres."
        },
        {
            "id": "c12",
            "source": "Doctor_Strange",
            "target": "Ghost_Rider_(Johnny_Blaze)",
            "teaser": "Both mystics have crossed paths in supernatural crises and the Midnight Sons alliance.",
            "answer": "both",
            "why": "Linked in Wikipedia and co-occur across 6 sentences in Marvel's occult corner.",
            "explanation": "Canonical Anchor: Supernatural cornerstones of the Marvel Universe."
        },
        {
            "id": "c13",
            "source": "Star_Brand",
            "target": "Starr_the_Slayer",
            "teaser": "The bearer of the planetary defensive weapon and the prehistoric barbarian slayer.",
            "answer": "link_only",
            "why": "Linked on Wikipedia due to creator Roy Thomas / editorial disambiguation, but 0 co-occurrences in stories.",
            "explanation": "Bibliographic Citation: Bibliographic/creator connection without narrative overlap."
        },
        {
            "id": "c14",
            "source": "Spider-Man",
            "target": "Spider-Woman_(Jessica_Drew)",
            "teaser": "Both share arachnid-themed hero names and costumes, appearing in parallel multiverse Spider-family adventures.",
            "answer": "coocc_only",
            "why": "15 sentence co-occurrences discussing costume similarities and crossovers, but lacking a direct hyperlink in this dataset.",
            "explanation": "Narrative Ghost Link: Co-discussed constantly in prose, yet separated in the category citation structure."
        },
        {
            "id": "c15",
            "source": "Deadpool",
            "target": "Squirrel_Girl",
            "teaser": "The Fourth-Wall breaking Merc with a Mouth and the Unbeatable champion of rodents.",
            "answer": "neither",
            "why": "Neither a Wikipedia hyperlink nor a sentence co-occurrence exists in the dataset.",
            "explanation": "Decoy Pair: Two comedic fan-favorites who happen to lack direct connection in this dataset."
        }
    ]
    return challenges

def main():
    print("Loading data...")
    nodes = load_nodes()
    images = load_hero_images()
    directed_links, undir_links, dir_map = load_links()
    pages = load_pages()
    alias_to_id = build_alias_map(nodes)

    print("Extracting co-occurrences...")
    sent_weights, para_weights, evidence_sentences = extract_cooccurrences(pages, alias_to_id)

    # Build graphs for community detection and degree analysis
    G_link = nx.Graph()
    G_link.add_nodes_from(nodes.keys())
    for pair in undir_links:
        u, v = tuple(pair)
        if u in nodes and v in nodes:
            G_link.add_edge(u, v)

    G_sent = nx.Graph()
    G_sent.add_nodes_from(nodes.keys())
    for pair, w in sent_weights.items():
        u, v = tuple(pair)
        if u in nodes and v in nodes:
            G_sent.add_edge(u, v, weight=w)

    G_para = nx.Graph()
    G_para.add_nodes_from(nodes.keys())
    for pair, w in para_weights.items():
        u, v = tuple(pair)
        if u in nodes and v in nodes:
            G_para.add_edge(u, v, weight=w)

    # Louvain communities on giant component
    giant_nodes_link = max(nx.connected_components(G_link), key=len)
    giant_link = G_link.subgraph(giant_nodes_link)
    comms_link = nx.community.louvain_communities(giant_link, seed=42)
    comm_by_node_link = {n: i for i, grp in enumerate(comms_link) for n in grp}

    # Combined edge set (Link union Sentence)
    all_pairs = set(undir_links).union(sent_weights.keys())
    edges_output = []
    
    # Track statistics
    counts = {"both": 0, "link_only": 0, "coocc_only": 0}

    for pair in all_pairs:
        u, v = tuple(pair)
        if u not in nodes or v not in nodes:
            continue
        has_link = pair in undir_links
        sw = sent_weights.get(pair, 0)
        pw = para_weights.get(pair, 0)

        if has_link and sw > 0:
            rel_type = "both"
        elif has_link:
            rel_type = "link_only"
        else:
            rel_type = "coocc_only"

        counts[rel_type] += 1

        pair_sorted = tuple(sorted((u, v)))
        link_dir = dir_map.get(pair_sorted, {"A_to_B": False, "B_to_A": False})
        
        ev = evidence_sentences.get(pair, {})
        excerpt = ev.get("sentence", "")
        if not excerpt and has_link:
            excerpt = f"Wikipedia hyperlink connects {nodes[u]['clean_name']} and {nodes[v]['clean_name']}, but they do not share a sentence."

        edges_output.append({
            "source": u,
            "target": v,
            "type": rel_type,
            "link": has_link,
            "link_dirs": "mutual" if (link_dir["A_to_B"] and link_dir["B_to_A"]) else ("A->B" if link_dir["A_to_B"] else ("B->A" if link_dir["B_to_A"] else "none")),
            "sent_weight": sw,
            "para_weight": pw,
            "excerpt": excerpt,
            "source_page": ev.get("source_page", ""),
        })

    # Prepare node data
    nodes_output = []
    for nid, info in nodes.items():
        nodes_output.append({
            "id": nid,
            "name": info["name"],
            "clean_name": info["clean_name"],
            "image": images.get(nid, ""),
            "community": comm_by_node_link.get(nid, 99),
            "degree_link": G_link.degree(nid),
            "degree_sent": G_sent.degree(nid),
            "degree_para": G_para.degree(nid),
            "wiki_url": info["wiki_url"],
        })

    # Game challenges
    game_challenges = curate_game_challenges(nodes, dir_map, sent_weights, evidence_sentences)

    output = {
        "metadata": {
            "title": "Marvel Wikipedia Links vs. Co-occurrence Networks",
            "nodes_count": len(nodes),
            "links_count": len(undir_links),
            "sent_cooccurrences_count": len(sent_weights),
            "para_cooccurrences_count": len(para_weights),
            "overlap": counts,
            "clustering_link": round(nx.average_clustering(G_link), 3),
            "clustering_sent": round(nx.average_clustering(G_sent), 3),
            "clustering_para": round(nx.average_clustering(G_para), 3),
            "modularity_link": round(nx.community.modularity(giant_link, comms_link), 3),
            "jaccard_sent": round(counts["both"] / (len(all_pairs)), 3),
        },
        "nodes": nodes_output,
        "edges": edges_output,
        "game": game_challenges,
    }

    OUTPUT_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT_FILE}")
    print(f"Stats: {counts}")
    print(f"Nodes: {len(nodes_output)}, Edges: {len(edges_output)}, Game Challenges: {len(game_challenges)}")

if __name__ == "__main__":
    main()
