"""Generate applet 4: Spot the Intruder (clique minigame).

Reads Marvel graph data, computes cliques, selects 10 puzzle squads with
exactly one intruder each, and emits a self-contained HTML applet.

  python3 tools/generate_applet4.py
  -> assets/applets/spot-the-intruder.html
"""

import json
import math
from pathlib import Path
from collections import defaultdict

import networkx as nx

SITE_ROOT = Path(__file__).resolve().parent.parent
DATA_NODES = SITE_ROOT / "week1_nodes.tsv"
DATA_EDGES = SITE_ROOT / "week1_edges.tsv"
HERO_DIR = SITE_ROOT / "assets" / "images" / "heroes"
OUT_HTML = SITE_ROOT / "assets" / "applets" / "spot-the-intruder.html"

# --- curated puzzle definitions (node_id lists, all verified real cliques) ---
# Each tuple: (team_label, member_node_ids)
PUZZLE_DEFS = [
    ("X-Men", [
        "Betsy_Braddock", "Cyclops_(Marvel_Comics)", "Emma_Frost",
        "Jean_Grey", "Rachel_Summers", "Storm_(Marvel_Comics)",
        "Wolverine_(character)"
    ]),
    ("X-Men (Cable & Jubilee)", [
        "Cable_(character)", "Cyclops_(Marvel_Comics)", "Emma_Frost",
        "Jean_Grey", "Jubilee_(character)", "Rachel_Summers"
    ]),
    ("Midnight Sons (Monsters)", [
        "Blade_(character)", "Doctor_Strange",
        "Man-Thing", "Morbius",
        "Spider-Man", "Werewolf_by_Night"
    ]),
    ("X-Men (Scarlet Witch)", [
        "Betsy_Braddock", "Cyclops_(Marvel_Comics)",
        "Scarlet_Witch", "Storm_(Marvel_Comics)",
        "Wolverine_(character)", "Jubilee_(character)"
    ]),
    ("Midnight Sons", [
        "Blade_(character)", "Deadpool", "Doctor_Strange",
        "Ghost_Rider", "Moon_Knight", "Spider-Man"
    ]),
    ("Midnight Sons (Gwenpool)", [
        "Blade_(character)", "Deadpool", "Doctor_Strange",
        "Gwenpool", "Moon_Knight", "Spider-Man"
    ]),
    ("X-Men (no Storm)", [
        "Betsy_Braddock", "Cable_(character)", "Emma_Frost",
        "Jean_Grey", "Jubilee_(character)", "Rachel_Summers"
    ]),
    ("Web Warriors", [
        "Black_Cat_(Marvel_Comics)", "Mayday_Parker", "Silk_(character)",
        "Spider-Man", "Spider-Woman_(Gwen_Stacy)", "Venom_(character)"
    ]),
    ("X-Men (core)", [
        "Betsy_Braddock", "Cyclops_(Marvel_Comics)", "Emma_Frost",
        "Jean_Grey", "Rachel_Summers", "Wolverine_(character)"
    ]),
    ("X-Men & Spider-Man", [
        "Betsy_Braddock", "Emma_Frost",
        "Rachel_Summers", "Spider-Man",
        "Storm_(Marvel_Comics)", "Wolverine_(character)"
    ]),
]

# Intruders: famous characters NOT in any puzzle as members, by recognizability
INTRUDER_CANDIDATES = [
    "Hulk", "Black_Widow_(Natasha_Romanova)", "She-Hulk",
    "Luke_Cage", "Black_Panther_(character)",
    "Iron_Fist_(character)", "Star-Lord", "Rocket_Raccoon",
    "Hercules_(Marvel_Comics)",
]


def load_graph():
    """Load directed + undirected Marvel graph."""
    nodes, names = [], {}
    with open(DATA_NODES, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.rstrip("\n").split("\t")
            if parts[0] == "node_id":
                continue
            nodes.append(parts[0])
            if len(parts) > 1:
                names[parts[0]] = parts[1]

    edges = set()
    with open(DATA_EDGES, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            a, b = line.rstrip("\n").split("\t")
            if a != b:
                edges.add(tuple(sorted((a, b))))

    G = nx.Graph()
    G.add_nodes_from(nodes)
    G.add_edges_from(sorted(edges))
    return G, names


# node_id -> image filename (basename) for all downloaded hero images
NODE_IMG_SLUG = {
    "Betsy_Braddock": "betsy-braddock",
    "Black_Cat_(Marvel_Comics)": "black-cat",
    "Black_Panther_(character)": "black-panther",
    "Black_Widow_(Natasha_Romanova)": "black-widow",
    "Blade_(character)": "blade",
    "Cable_(character)": "cable",
    "Cyclops_(Marvel_Comics)": "cyclops",
    "Deadpool": "deadpool",
    "Doctor_Strange": "doctor-strange",
    "Emma_Frost": "emma-frost",
    "Ghost_Rider": "ghost-rider",
    "Gwenpool": "gwenpool",
    "Hercules_(Marvel_Comics)": "hercules-marvel",
    "Hulk": "hulk",
    "Iron_Fist_(character)": "iron-fist",
    "Jean_Grey": "jean-grey",
    "Jubilee_(character)": "jubilee",
    "Luke_Cage": "luke-cage",
    "Mayday_Parker": "spider-girl",
    "Moon_Knight": "moon-knight",
    "Rachel_Summers": "rachel-summers",
    "Rocket_Raccoon": "rocket-raccoon",
    "Scarlet_Witch": "scarlet-witch",
    "She-Hulk": "she-hulk",
    "Silk_(character)": "silk",
    "Spider-Man": "spider-man",
    "Spider-Woman": "spider-woman",
    "Spider-Woman_(Gwen_Stacy)": "spider-gwen",
    "Star-Lord": "star-lord",
    "Storm_(Marvel_Comics)": "storm",
    "Venom_(character)": "venom",
    "Wolverine_(Ultimate_Marvel_character)": "wolverine-ultimate",
    "Wolverine_(character)": "wolverine",
    "Morbius": "morbius",
    "Man-Thing": "man-thing",
    "Werewolf_by_Night": "werewolf-by-night",
}


def image_for_node(node_id):
    """Return relative URL to hero image, or None."""
    slug = NODE_IMG_SLUG.get(node_id)
    if not slug:
        return None
    for ext in ("png", "jpg", "jpeg", "webp", "svg"):
        if (HERO_DIR / f"{slug}.{ext}").exists():
            return f"../images/heroes/{slug}.{ext}"
    return None


def pick_intruder(G, squad_set, usage):
    """Pick a recognizable intruder, preferring variety across puzzles.

    Candidates come from a famous shortlist plus the highest-degree characters.
    Must be connected to at least 2 squad members (so they plausibly belong)
    and NOT connected to all of them. Prefers intruders with images, used fewest
    times so far, then near-miss connectivity, then celebrity.
    """
    S = len(squad_set)

    # famous shortlist
    ordered = list(INTRUDER_CANDIDATES)
    # add top-degree characters not already in shortlist
    top_deg = sorted(G.degree, key=lambda x: -x[1])
    for n, _ in top_deg:
        if n not in ordered and len(ordered) < 60:
            ordered.append(n)

    cands = []
    seen = set()
    for cand in ordered:
        if cand in squad_set or cand not in G or cand in seen:
            continue
        seen.add(cand)
        k = sum(1 for s in squad_set if G.has_edge(cand, s))
        if k < 2 or k >= S - 1:
            continue
        has_img = image_for_node(cand) is not None
        cands.append((has_img, usage.get(cand, 0), -k, -G.degree(cand), cand))

    if not cands:
        return None
    # stable order: image first, then least-used, then near-miss, then celebrity
    cands.sort(key=lambda x: (x[0] if not x[0] else 0, x[1], x[2], x[3]))
    # images at top: prefer has_img=1
    cands.sort(key=lambda x: (not x[0], x[1], x[2], x[3]))
    chosen = cands[0][4]
    usage[chosen] = usage.get(chosen, 0) + 1
    return chosen


def build_puzzles(G, names):
    """Build the 10 puzzle objects."""
    puzzles = []
    usage = {}
    for team_label, members in PUZZLE_DEFS:
        squad_set = set(members)
        # the squad must be a real clique: every member knows every other
        for i, a in enumerate(members):
            for b in members[i + 1:]:
                if not G.has_edge(a, b):
                    raise ValueError(
                        f"{team_label}: not a clique — {a} and {b} are not connected"
                    )
        intruder = pick_intruder(G, squad_set, usage)
        if intruder is None:
            print(f"  WARNING: no intruder found for {team_label} ({len(members)} members)")
            continue

        # compute adjacency info for each tile
        tiles = []
        for mid in members:
            conn = sum(1 for s in members if s != mid and G.has_edge(mid, s))
            # also check if connected to intruder
            conn_intruder = 1 if G.has_edge(mid, intruder) else 0
            tiles.append({
                "id": mid,
                "name": names.get(mid, mid),
                "img": image_for_node(mid),
                "knowsInRoom": conn + conn_intruder,  # likes in the whole room
            })
        # intruder tile
        intruder_conn = sum(1 for s in members if G.has_edge(intruder, s))
        intruder_tile = {
            "id": intruder,
            "name": names.get(intruder, intruder),
            "img": image_for_node(intruder),
            "knowsInRoom": intruder_conn,
        }

        # validation: intruder must know fewer people in the room than any member
        min_member_knows = min(t["knowsInRoom"] for t in tiles)
        assert intruder_conn < min_member_knows, (
            f"Intruder {intruder} ({intruder_conn}) not clearly fewer than "
            f"min member ({min_member_knows}) in {team_label}"
        )

        # generate a fun fact for the puzzle
        squad_names = [names.get(m, m).split(" (")[0] for m in members]
        intruder_name = names.get(intruder, intruder).split(" (")[0]
        fact = (
            f"That was the {team_label} — a real clique where every member knows "
            f"every other. {intruder_name} only knew {intruder_conn} of them."
        )

        puzzles.append({
            "team": team_label,
            "squadSize": len(members),
            "tiles": tiles,
            "intruder": intruder_tile,
            "fact": fact,
        })
        print(f"  {team_label}: {len(members)} members, intruder={intruder_name} ({intruder_conn}/{len(members)} connections)")

    return puzzles


def generate_html(puzzles):
    """Generate the self-contained HTML applet."""
    # embed puzzle data as JSON
    data_json = json.dumps(puzzles, indent=2, ensure_ascii=False)

    html = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Spot the Intruder</title>
<style>
:root{color-scheme:dark;--bg:#0a0a1a;--fg:#e0e0e0;--header:#fff;--muted:#777;--badge-bg:#1e1e3a;--badge-border:#2a2a44;--badge-fg:#bbb;--hl:#fbbf24;--tile-bg:#111;--tile-border:#222;--tile-hover:#444;--img-bg:#1a1a2e;--avatar-a:#1e1e3a;--avatar-b:#2a2a4a;--name-fg:#ccc;--btn-bg:#16162a;--btn-border:#2a2a44;--btn-fg:#bbb;--btn-hover:#20203a;--btn-hover-fg:#fff;--done-fg:#aaa;--ref-fg:#555}
:root[data-theme="light"]{color-scheme:light;--bg:#f1f5f9;--fg:#0f172a;--header:#0f172a;--muted:#64748b;--badge-bg:#ffffff;--badge-border:#e2e8f0;--badge-fg:#475569;--hl:#d97706;--tile-bg:#ffffff;--tile-border:#e2e8f0;--tile-hover:#94a3b8;--img-bg:#eef2f7;--avatar-a:#e2e8f0;--avatar-b:#cbd5e1;--name-fg:#0f172a;--btn-bg:#ffffff;--btn-border:#e2e8f0;--btn-fg:#334155;--btn-hover:#f1f5f9;--btn-hover-fg:#0f172a;--done-fg:#475569;--ref-fg:#94a3b8}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--fg);display:flex;flex-direction:column;align-items:center;min-height:100vh;overflow-y:auto;padding:1rem;transition:background .25s,color .25s}
h1{font-size:1.1rem;font-weight:700;color:var(--header);text-align:center}
.sub{font-size:.72rem;color:var(--muted);margin:.2rem 0 .8rem;text-align:center;max-width:440px;line-height:1.3}
.hud{display:flex;gap:1.2rem;align-items:center;flex-wrap:wrap;justify-content:center;margin-bottom:.8rem;font-size:.72rem}
.hud .badge{background:var(--badge-bg);border:1px solid var(--badge-border);border-radius:6px;padding:.2rem .6rem;color:var(--badge-fg);font-weight:600}
.hud .badge .hl{color:var(--hl)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:.7rem;width:100%;max-width:1200px;margin-bottom:.6rem}
.tile{position:relative;border-radius:10px;overflow:hidden;border:2px solid var(--tile-border);background:var(--tile-bg);cursor:pointer;transition:transform .12s,border-color .15s,opacity .25s;aspect-ratio:3/4;display:flex;flex-direction:column}
.tile:hover{border-color:var(--tile-hover);transform:scale(1.03)}
.tile.wrong{opacity:.45;border-color:#94a3b8;cursor:default}
.tile.correct{border-color:#22c55e;box-shadow:0 0 12px rgba(34,197,94,.35)}
.tile.intruder{border-color:#ef4444;box-shadow:0 0 12px rgba(239,68,68,.4)}
.tile.intruder .intruder-badge{display:block}
.intruder-badge{display:none;position:absolute;top:4px;left:4px;background:#ef4444;color:#fff;font-size:.6rem;font-weight:700;padding:1px 6px;border-radius:4px;z-index:2}
.tile img{width:100%;flex:1;object-fit:cover;background:var(--img-bg)}
.tile .avatar{width:100%;flex:1;display:flex;align-items:center;justify-content:center;font-size:2rem;font-weight:700;color:var(--fg);background:linear-gradient(135deg,var(--avatar-a),var(--avatar-b))}
.tile .name{padding:.25rem .3rem;font-size:.62rem;color:var(--name-fg);text-align:center;line-height:1.2;min-height:1.8rem;display:flex;align-items:center;justify-content:center}
.feedback{font-size:.78rem;color:var(--hl);text-align:center;margin:.3rem 0;min-height:1.2rem;font-weight:500;max-width:900px;line-height:1.3}
.actions{display:flex;gap:.8rem;align-items:center;margin:.5rem 0 1rem}
.btn{background:var(--btn-bg);color:var(--btn-fg);border:1px solid var(--btn-border);border-radius:6px;padding:.3rem .8rem;font-size:.72rem;cursor:pointer;font-weight:600;transition:background .12s,color .12s}
.btn:hover{background:var(--btn-hover);color:var(--btn-hover-fg)}
.btn:disabled{opacity:.35;cursor:default}
.btn.primary{background:#b91c1c;border-color:#b91c1c;color:#fff}
.btn.primary:hover{background:#991b1b}
.done-text{font-size:.8rem;color:var(--done-fg);text-align:center;max-width:900px;line-height:1.4;margin:.5rem 0}
.ref{font-size:.6rem;color:var(--ref-fg);margin-top:.5rem;text-align:center}
</style>
</head>
<body>

<h1>Spot the Intruder</h1>
<p class="sub">In every squad, one hero is not friends with everyone. Find them. Tap a tile to accuse.</p>

<div class="hud">
  <div class="badge">Puzzle <span class="hl" id="pz-n">1</span>/<span id="pz-total">10</span></div>
  <div class="badge">Difficulty: <span class="hl" id="pz-diff">Scout</span></div>
  <div class="badge">Guesses: <span class="hl" id="pz-guesses">0</span></div>
</div>

<div class="grid" id="grid"></div>
<div class="feedback" id="fb"></div>
<div class="actions">
  <button class="btn" id="btn-next" disabled>Next squad &rarr;</button>
  <button class="btn" id="btn-restart" style="display:none">Play again</button>
</div>
<div class="done-text" id="done-text"></div>

<p class="ref">Network data: Marvel Comics Wikipedia &middot; 303 characters, 1434 undirected edges</p>

<script>
""" + f"var PUZZLES = {data_json};" + r"""

// ---- theme sync: match the site theme (light/dark) even inside the iframe ----
(function() {
  var html = document.documentElement;
  function apply(theme) {
    if (theme === 'light' || theme === 'dark') html.setAttribute('data-theme', theme);
  }
  function readParent() {
    try {
      var parentHtml = window.parent && window.parent.document &&
        window.parent.document.documentElement;
      return parentHtml ? parentHtml.getAttribute('data-theme') : null;
    } catch (e) { return null; }
  }
  apply(readParent() || 'dark');
  // follow live theme toggles on the host page
  try {
    var parentHtml = window.parent.document.documentElement;
    var mo = new MutationObserver(function() { apply(readParent()); });
    mo.observe(parentHtml, { attributes: true, attributeFilter: ['data-theme'] });
  } catch (e) {}
})();

var grid = document.getElementById('grid');
var fb = document.getElementById('fb');
var pzN = document.getElementById('pz-n');
var pzTotal = document.getElementById('pz-total');
var pzDiff = document.getElementById('pz-diff');
var pzGuesses = document.getElementById('pz-guesses');
var btnNext = document.getElementById('btn-next');
var btnRestart = document.getElementById('btn-restart');
var doneText = document.getElementById('done-text');

var cur = 0, guesses = 0, solved = false, total = PUZZLES.length;
pzTotal.textContent = total;

function shuffle(a) {
  for (var i = a.length - 1; i > 0; i--) {
    var j = Math.floor(Math.random() * (i + 1));
    var t = a[i]; a[i] = a[j]; a[j] = t;
  }
  return a;
}

function renderPuzzle() {
  var p = PUZZLES[cur];
  pzN.textContent = cur + 1;
  guesses = 0;
  solved = false;
  pzGuesses.textContent = '0';
  btnNext.disabled = true;
  fb.textContent = 'Tap a tile to accuse. If wrong, you get a clue.';
  // difficulty label: intruder who knows almost everyone is harder to spot
  pzDiff.textContent = p.intruder.knowsInRoom >= p.squadSize - 2
    ? 'Investigator' : 'Scout';
  // shuffle tiles (mix members + intruder)
  var tiles = shuffle(p.tiles.concat([p.intruder]));
  grid.innerHTML = '';
  tiles.forEach(function(t) {
    var div = document.createElement('div');
    div.className = 'tile';
    div.dataset.id = t.id;
    div.dataset.isIntruder = t.id === p.intruder.id ? '1' : '0';
    // img or fallback avatar
    if (t.img) {
      var img = document.createElement('img');
      img.src = t.img;
      img.alt = t.name;
      img.loading = 'lazy';
      div.appendChild(img);
    } else {
      var av = document.createElement('div');
      av.className = 'avatar';
      av.textContent = t.name.charAt(0);
      div.appendChild(av);
    }
    var nm = document.createElement('div');
    nm.className = 'name';
    nm.textContent = t.name;
    div.appendChild(nm);
    var badge = document.createElement('div');
    badge.className = 'intruder-badge';
    badge.textContent = 'INTRUDER';
    div.appendChild(badge);
    div.addEventListener('click', onGuess);
    grid.appendChild(div);
  });
}

function onGuess(e) {
  if (solved) return;
  var tile = e.currentTarget;
  if (tile.classList.contains('wrong') || tile.classList.contains('correct')) return;
  var p = PUZZLES[cur];
  var isRight = tile.dataset.isIntruder === '1';
  guesses++;
  pzGuesses.textContent = guesses;
  if (isRight) {
    solved = true;
    tile.classList.add('intruder');
    // mark all tiles
    var allTiles = grid.querySelectorAll('.tile');
    for (var i = 0; i < allTiles.length; i++) {
      allTiles[i].classList.add(allTiles[i].dataset.isIntruder === '1' ? 'intruder' : 'correct');
      allTiles[i].removeEventListener('click', onGuess);
    }
    fb.textContent = 'Found the intruder in ' + guesses + (guesses === 1 ? ' pick!' : ' picks!');
    if (cur < total - 1) {
      btnNext.disabled = false;
    } else {
      doneText.textContent = 'All ' + total + ' squads cleared. Every team in Marvel is a clique — everyone knows everyone. That is what makes them teams.';
      btnRestart.style.display = '';
    }
  } else {
    tile.classList.add('wrong');
    tile.removeEventListener('click', onGuess);
    // find connections info
    var connInfo = p.tiles.find(function(t) { return t.id === tile.dataset.id; });
    var conn = connInfo ? connInfo.knowsInRoom : '?';
    var room = p.tiles.length; // other heroes in this room
    fb.textContent = tile.querySelector('.name').textContent + ' knows ' + conn +
      ' of ' + room + ' others here \u2014 not the stranger.';
  }
}

btnNext.addEventListener('click', function() {
  if (cur < total - 1) { cur++; renderPuzzle(); }
});
btnRestart.addEventListener('click', function() {
  cur = 0; doneText.textContent = ''; btnRestart.style.display = 'none'; renderPuzzle();
});

renderPuzzle();
</script>
</body>
</html>"""
    return html


def main():
    print("Loading Marvel graph...")
    G, names = load_graph()
    print(f"  N={G.number_of_nodes()}, M={G.number_of_edges()}")

    print("\nBuilding puzzles...")
    puzzles = build_puzzles(G, names)

    print(f"\nGenerated {len(puzzles)} puzzles. Writing HTML...")
    html = generate_html(puzzles)
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"  -> {OUT_HTML} ({len(html):,} bytes)")

    # validation: every tile should have an image
    missing = 0
    for p in puzzles:
        for t in p["tiles"]:
            if t["img"] is None:
                print(f"  MISSING IMAGE: {t['id']} ({t['name']})")
                missing += 1
        if p["intruder"]["img"] is None:
            print(f"  MISSING IMAGE (intruder): {p['intruder']['id']} ({p['intruder']['name']})")
            missing += 1
    if missing:
        print(f"\n  {missing} tiles missing images (will show letter avatars)")
    else:
        print("\n  All tiles have images!")


if __name__ == "__main__":
    main()
