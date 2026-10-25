"""Generate applet 6: Marvel Co-occurrence vs. Hyperlink Network & Detective Game.

Reads assets/marvel_cooccurrence_comparison.json and outputs
assets/applets/marvel-cooccurrence-game.html
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "assets" / "marvel_cooccurrence_comparison.json"
OUT_HTML = ROOT / "assets" / "applets" / "marvel-cooccurrence-game.html"

def generate_html(data):
    data_json = json.dumps(data, ensure_ascii=False)
    
    html = f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Marvel Network: Citations vs. Co-occurrences</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Bangers&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js"></script>
  <style>
    :root {{
      --bg: #0b0f19;
      --panel: #131b2e;
      --card: #1a243b;
      --card-hover: #22304e;
      --border: #2a3859;
      --text: #f1f5f9;
      --text-muted: #94a3b8;
      --both: #10b981;
      --link: #3b82f6;
      --coocc: #f59e0b;
      --neither: #64748b;
      --accent: #ef4444;
      --gold: #fbbf24;
      --shadow: 0 8px 24px rgba(0, 0, 0, 0.45);
    }}
    :root[data-theme="light"] {{
      --bg: #f8fafc;
      --panel: #ffffff;
      --card: #f1f5f9;
      --card-hover: #e2e8f0;
      --border: #cbd5e1;
      --text: #0f172a;
      --text-muted: #64748b;
      --both: #059669;
      --link: #2563eb;
      --coocc: #d97706;
      --neither: #94a3b8;
      --accent: #dc2626;
      --gold: #d97706;
      --shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
      overflow-x: hidden;
      padding-bottom: 2rem;
    }}
    .applet-header {{
      background: var(--panel);
      border-bottom: 1px solid var(--border);
      padding: 1rem 1.25rem;
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 1rem;
    }}
    .applet-title {{
      font-family: 'Bangers', cursive, sans-serif;
      font-size: 1.85rem;
      letter-spacing: 0.05em;
      color: var(--text);
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }}
    .applet-title span {{
      color: var(--gold);
    }}
    .tabs {{
      display: flex;
      gap: 0.5rem;
      background: var(--bg);
      padding: 0.25rem;
      border-radius: 8px;
      border: 1px solid var(--border);
    }}
    .tab-btn {{
      background: transparent;
      border: none;
      color: var(--text-muted);
      padding: 0.5rem 1rem;
      border-radius: 6px;
      font-weight: 600;
      font-size: 0.85rem;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 0.4rem;
      transition: all 0.2s ease;
    }}
    .tab-btn:hover {{
      color: var(--text);
      background: rgba(255, 255, 255, 0.05);
    }}
    .tab-btn.active {{
      background: var(--card);
      color: var(--gold);
      box-shadow: 0 2px 8px rgba(0,0,0,0.25);
    }}
    .tab-content {{
      display: none;
      width: 100%;
    }}
    .tab-content.active {{
      display: block;
    }}

    /* GAME VIEW */
    .game-container {{
      max-width: 960px;
      margin: 1.5rem auto;
      padding: 0 1rem;
    }}
    .game-hud {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--panel);
      padding: 0.85rem 1.25rem;
      border-radius: 12px;
      border: 1px solid var(--border);
      margin-bottom: 1.5rem;
      box-shadow: var(--shadow);
    }}
    .hud-stat {{
      display: flex;
      flex-direction: column;
      align-items: center;
    }}
    .hud-label {{
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--text-muted);
      font-weight: 700;
    }}
    .hud-val {{
      font-family: 'Bangers', cursive, sans-serif;
      font-size: 1.7rem;
      color: var(--gold);
      line-height: 1.1;
    }}
    .streak-badge {{
      display: inline-flex;
      align-items: center;
      gap: 0.25rem;
      background: rgba(239, 68, 68, 0.15);
      color: #ef4444;
      border: 1px solid rgba(239, 68, 68, 0.3);
      padding: 0.2rem 0.5rem;
      border-radius: 999px;
      font-size: 0.8rem;
      font-weight: 700;
    }}
    .matchup-card {{
      background: var(--panel);
      border: 2px solid var(--border);
      border-radius: 16px;
      padding: 1.75rem;
      box-shadow: var(--shadow);
      margin-bottom: 1.5rem;
      position: relative;
    }}
    .matchup-heroes {{
      display: grid;
      grid-template-columns: 1fr auto 1fr;
      align-items: center;
      gap: 1.5rem;
      margin-bottom: 1.75rem;
    }}
    .hero-box {{
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      background: var(--card);
      border: 1px solid var(--border);
      padding: 1.25rem 1rem;
      border-radius: 12px;
    }}
    .hero-avatar {{
      width: 90px;
      height: 90px;
      border-radius: 50%;
      object-fit: cover;
      border: 3px solid var(--gold);
      background: #000;
      margin-bottom: 0.75rem;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }}
    .hero-avatar-fallback {{
      width: 90px;
      height: 90px;
      border-radius: 50%;
      background: linear-gradient(135deg, #1e293b, #334155);
      border: 3px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: 'Bangers', cursive, sans-serif;
      font-size: 2.2rem;
      color: var(--text);
      margin-bottom: 0.75rem;
    }}
    .hero-name {{
      font-family: 'Bangers', cursive, sans-serif;
      font-size: 1.35rem;
      letter-spacing: 0.04em;
      margin-bottom: 0.25rem;
    }}
    .hero-degree-tag {{
      font-size: 0.75rem;
      color: var(--text-muted);
      background: rgba(255, 255, 255, 0.06);
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
    }}
    .vs-badge {{
      font-family: 'Bangers', cursive, sans-serif;
      font-size: 2rem;
      color: var(--accent);
      background: var(--card);
      border: 2px solid var(--border);
      width: 56px;
      height: 56px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 16px rgba(0,0,0,0.3);
    }}
    .story-teaser {{
      background: var(--card);
      border-left: 4px solid var(--gold);
      padding: 1.1rem 1.25rem;
      border-radius: 0 8px 8px 0;
      font-size: 0.95rem;
      font-style: italic;
      color: var(--text);
      margin-bottom: 1.75rem;
      line-height: 1.5;
    }}
    .game-question {{
      text-align: center;
      font-size: 1.05rem;
      font-weight: 600;
      margin-bottom: 1.25rem;
      color: var(--text-muted);
    }}
    .choice-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.85rem;
    }}
    @media (max-width: 640px) {{
      .choice-grid {{ grid-template-columns: 1fr; }}
      .matchup-heroes {{ grid-template-columns: 1fr; gap: 0.75rem; }}
      .vs-badge {{ margin: 0 auto; }}
    }}
    .choice-btn {{
      background: var(--card);
      border: 2px solid var(--border);
      color: var(--text);
      padding: 1rem 1.2rem;
      border-radius: 10px;
      font-size: 0.95rem;
      font-weight: 600;
      text-align: left;
      cursor: pointer;
      display: flex;
      flex-direction: column;
      gap: 0.3rem;
      transition: all 0.15s ease;
    }}
    .choice-btn:hover:not(:disabled) {{
      transform: translateY(-2px);
      border-color: var(--gold);
      background: var(--card-hover);
    }}
    .choice-btn .choice-title {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 1rem;
    }}
    .choice-btn .choice-desc {{
      font-size: 0.78rem;
      color: var(--text-muted);
      font-weight: 400;
    }}
    .choice-btn.both .indicator {{ color: var(--both); }}
    .choice-btn.link_only .indicator {{ color: var(--link); }}
    .choice-btn.coocc_only .indicator {{ color: var(--coocc); }}
    .choice-btn.neither .indicator {{ color: var(--neither); }}

    /* FEEDBACK CARD */
    .feedback-box {{
      display: none;
      margin-top: 1.5rem;
      padding: 1.25rem;
      border-radius: 12px;
      animation: fadeIn 0.3s ease;
    }}
    @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(6px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    .feedback-box.correct {{
      background: rgba(16, 185, 129, 0.12);
      border: 2px solid var(--both);
    }}
    .feedback-box.incorrect {{
      background: rgba(239, 68, 68, 0.12);
      border: 2px solid var(--accent);
    }}
    .feedback-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.75rem;
    }}
    .feedback-title {{
      font-family: 'Bangers', cursive, sans-serif;
      font-size: 1.4rem;
      letter-spacing: 0.04em;
    }}
    .feedback-box.correct .feedback-title {{ color: var(--both); }}
    .feedback-box.incorrect .feedback-title {{ color: var(--accent); }}
    .concordance-excerpt {{
      background: var(--card);
      border-radius: 8px;
      padding: 0.85rem 1rem;
      font-size: 0.9rem;
      margin: 0.75rem 0;
      border-left: 3px solid var(--gold);
    }}
    .concordance-excerpt mark {{
      background: rgba(251, 191, 36, 0.3);
      color: inherit;
      padding: 1px 4px;
      border-radius: 3px;
    }}
    .feedback-insight {{
      font-size: 0.88rem;
      color: var(--text);
      line-height: 1.45;
      margin-bottom: 1rem;
    }}
    .btn-next {{
      background: var(--gold);
      color: #0b0f19;
      border: none;
      padding: 0.75rem 1.5rem;
      border-radius: 8px;
      font-weight: 700;
      font-size: 0.95rem;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      transition: opacity 0.15s;
    }}
    .btn-next:hover {{ opacity: 0.9; }}

    /* GRAPH VIEW */
    .graph-layout {{
      display: grid;
      grid-template-columns: minmax(0, 1.8fr) minmax(320px, 0.85fr);
      min-height: 720px;
    }}
    @media (max-width: 900px) {{
      .graph-layout {{ grid-template-columns: 1fr; }}
    }}
    .graph-canvas-wrap {{
      position: relative;
      background: radial-gradient(circle at 50% 50%, rgba(30, 41, 59, 0.5), var(--bg));
      overflow: hidden;
      min-height: 680px;
    }}
    svg.network-svg {{
      width: 100%;
      height: 700px;
      display: block;
    }}
    .graph-controls {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 0.75rem;
      padding: 0.85rem 1.25rem;
      background: var(--panel);
      border-bottom: 1px solid var(--border);
    }}
    .ctrl-group {{
      display: flex;
      align-items: center;
      gap: 0.4rem;
      font-size: 0.85rem;
    }}
    .ctrl-group label {{
      color: var(--text-muted);
      font-weight: 600;
      text-transform: uppercase;
      font-size: 0.75rem;
    }}
    select, input[type="text"] {{
      background: var(--card);
      border: 1px solid var(--border);
      color: var(--text);
      padding: 0.45rem 0.75rem;
      border-radius: 6px;
      font-size: 0.85rem;
      outline: none;
    }}
    select:focus, input[type="text"]:focus {{
      border-color: var(--gold);
    }}
    .graph-legend {{
      position: absolute;
      bottom: 1rem;
      left: 1rem;
      background: rgba(19, 27, 46, 0.88);
      backdrop-filter: blur(8px);
      padding: 0.6rem 0.9rem;
      border-radius: 8px;
      border: 1px solid var(--border);
      font-size: 0.78rem;
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
    }}
    .legend-item {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }}
    .legend-line {{
      width: 16px;
      height: 3px;
      border-radius: 2px;
    }}
    .inspector-panel {{
      background: var(--panel);
      border-left: 1px solid var(--border);
      padding: 1.5rem;
      overflow-y: auto;
      max-height: 780px;
    }}
    .inspector-panel h2 {{
      font-family: 'Bangers', cursive, sans-serif;
      font-size: 1.6rem;
      letter-spacing: 0.04em;
      margin-bottom: 0.5rem;
      color: var(--gold);
    }}
    .edge-badge {{
      display: inline-block;
      padding: 0.25rem 0.6rem;
      border-radius: 999px;
      font-size: 0.72rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 0.75rem;
    }}
    .edge-badge.both {{ background: rgba(16, 185, 129, 0.2); color: var(--both); border: 1px solid var(--both); }}
    .edge-badge.link_only {{ background: rgba(59, 130, 246, 0.2); color: var(--link); border: 1px solid var(--link); }}
    .edge-badge.coocc_only {{ background: rgba(245, 158, 11, 0.2); color: var(--coocc); border: 1px solid var(--coocc); }}

    /* METRICS TAB */
    .metrics-container {{
      max-width: 1000px;
      margin: 1.5rem auto;
      padding: 0 1rem;
    }}
    .metrics-table {{
      width: 100%;
      border-collapse: collapse;
      background: var(--panel);
      border-radius: 12px;
      overflow: hidden;
      border: 1px solid var(--border);
      margin-bottom: 2rem;
      box-shadow: var(--shadow);
    }}
    .metrics-table th, .metrics-table td {{
      padding: 0.85rem 1rem;
      text-align: left;
      border-bottom: 1px solid var(--border);
      font-size: 0.9rem;
    }}
    .metrics-table th {{
      background: var(--card);
      font-weight: 700;
      color: var(--gold);
      text-transform: uppercase;
      font-size: 0.78rem;
      letter-spacing: 0.05em;
    }}
    .metrics-table tr:last-child td {{ border-bottom: none; }}
    .metrics-table tr:hover td {{ background: var(--card-hover); }}

    .hubs-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 1rem;
    }}
    .hub-card {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.25rem;
      box-shadow: var(--shadow);
    }}
    .hub-card-header {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
      margin-bottom: 1rem;
    }}
    .hub-avatar {{
      width: 48px;
      height: 48px;
      border-radius: 50%;
      object-fit: cover;
      border: 2px solid var(--gold);
    }}
    .hub-avatar-fallback {{
      width: 48px;
      height: 48px;
      border-radius: 50%;
      background: var(--card);
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: 'Bangers', cursive, sans-serif;
      font-size: 1.3rem;
      border: 2px solid var(--border);
    }}
    .hub-name {{
      font-family: 'Bangers', cursive, sans-serif;
      font-size: 1.2rem;
      letter-spacing: 0.03em;
    }}
    .bar-row {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin-bottom: 0.4rem;
      font-size: 0.78rem;
    }}
    .bar-label {{
      width: 65px;
      color: var(--text-muted);
      font-weight: 600;
    }}
    .bar-track {{
      flex: 1;
      height: 10px;
      background: var(--card);
      border-radius: 999px;
      overflow: hidden;
    }}
    .bar-fill {{
      height: 100%;
      border-radius: 999px;
      transition: width 0.3s ease;
    }}
    .bar-val {{
      width: 30px;
      text-align: right;
      font-weight: 700;
      color: var(--text);
    }}

    /* GAME COMPLETE */
    .game-over-box {{
      display: none;
      text-align: center;
      padding: 2.5rem 1.5rem;
      background: var(--panel);
      border: 2px solid var(--gold);
      border-radius: 16px;
      box-shadow: var(--shadow);
      animation: fadeIn 0.4s ease;
    }}
    .game-over-title {{
      font-family: 'Bangers', cursive, sans-serif;
      font-size: 2.5rem;
      color: var(--gold);
      margin-bottom: 0.5rem;
    }}
    .rank-badge {{
      display: inline-block;
      font-family: 'Bangers', cursive, sans-serif;
      font-size: 1.5rem;
      background: linear-gradient(135deg, rgba(251,191,36,0.2), rgba(239,68,68,0.2));
      border: 2px solid var(--gold);
      color: var(--gold);
      padding: 0.4rem 1.25rem;
      border-radius: 999px;
      margin: 1rem 0;
    }}
  </style>
</head>
<body>

  <!-- HEADER -->
  <header class="applet-header">
    <div class="applet-title">
      MARVEL NETWORK: <span>CITATIONS VS. CO-OCCURRENCES</span>
    </div>
    <nav class="tabs">
      <button class="tab-btn active" data-tab="game-tab">🕵️ Detective Game</button>
      <button class="tab-btn" data-tab="graph-tab">🕸️ Graph Explorer</button>
      <button class="tab-btn" data-tab="metrics-tab">📊 Network Metrics</button>
    </nav>
  </header>

  <!-- TAB 1: GAME -->
  <section id="game-tab" class="tab-content active">
    <div class="game-container">
      <div class="game-hud">
        <div class="hud-stat">
          <span class="hud-label">Case</span>
          <span class="hud-val" id="case-num">1 / 15</span>
        </div>
        <div class="hud-stat">
          <span class="hud-label">Score</span>
          <span class="hud-val" id="score-val">0</span>
        </div>
        <div class="hud-stat">
          <span class="hud-label">Streak</span>
          <span class="hud-val" id="streak-val">0</span>
        </div>
        <div class="hud-stat">
          <span class="hud-label">Multiplier</span>
          <span class="streak-badge" id="mult-badge">1x</span>
        </div>
      </div>

      <div class="matchup-card" id="matchup-card">
        <div class="matchup-heroes">
          <div class="hero-box" id="hero-left"></div>
          <div class="vs-badge">VS</div>
          <div class="hero-box" id="hero-right"></div>
        </div>

        <div class="story-teaser" id="story-teaser">
          "Loading narrative excerpt..."
        </div>

        <p class="game-question">Does their connection exist in Wikipedia Hyperlinks, Story Co-occurrence, Both, or Neither?</p>

        <div class="choice-grid" id="choice-grid">
          <button class="choice-btn both" data-choice="both">
            <span class="choice-title"><span class="indicator">●</span> Both (Canonical Anchor)</span>
            <span class="choice-desc">Wikipedia editors hyperlinked them AND they co-occur in story prose.</span>
          </button>
          <button class="choice-btn link_only" data-choice="link_only">
            <span class="choice-title"><span class="indicator">●</span> Citation Only (Bibliographic)</span>
            <span class="choice-desc">Wikipedia pages hyperlink each other, but they NEVER share a story sentence.</span>
          </button>
          <button class="choice-btn coocc_only" data-choice="coocc_only">
            <span class="choice-title"><span class="indicator">●</span> Ghost Link (Narrative)</span>
            <span class="choice-desc">They interact across story sentences, but Wikipedia editors omitted a hyperlink!</span>
          </button>
          <button class="choice-btn neither" data-choice="neither">
            <span class="choice-title"><span class="indicator">●</span> Neither (Decoy Pair)</span>
            <span class="choice-desc">No hyperlinks and zero story co-occurrences in the dataset.</span>
          </button>
        </div>

        <div class="feedback-box" id="feedback-box">
          <div class="feedback-header">
            <span class="feedback-title" id="feedback-title">CORRECT!</span>
            <span class="edge-badge" id="feedback-badge">BOTH</span>
          </div>
          <div class="concordance-excerpt" id="feedback-concordance"></div>
          <p class="feedback-insight" id="feedback-insight"></p>
          <button class="btn-next" id="btn-next-case">Next Case →</button>
        </div>
      </div>

      <div class="game-over-box" id="game-over-box">
        <h2 class="game-over-title">INVESTIGATION COMPLETE!</h2>
        <p>You have inspected all 15 connection cases across the Marvel Universe.</p>
        <div>
          <span class="rank-badge" id="final-rank">AVENGER</span>
        </div>
        <p style="margin-bottom: 1.5rem; font-size: 1.1rem;">
          Final Score: <strong id="final-score" style="color:var(--gold);">0</strong> · Accuracy: <strong id="final-acc">0%</strong> · Max Streak: <strong id="final-streak">0</strong>
        </p>
        <button class="btn-next" id="btn-restart">Play Again ↺</button>
      </div>
    </div>
  </section>

  <!-- TAB 2: GRAPH EXPLORER -->
  <section id="graph-tab" class="tab-content">
    <div class="graph-controls">
      <div class="ctrl-group">
        <label for="filter-type">Edge Type:</label>
        <select id="filter-type">
          <option value="all">All Overlap (Both + Links + Co-occurrences)</option>
          <option value="both">🟢 Both (762 links)</option>
          <option value="link_only">🔵 Citation Only (672 links)</option>
          <option value="coocc_only">🟠 Ghost Links (728 links)</option>
        </select>
      </div>
      <div class="ctrl-group">
        <label for="filter-weight">Min Sentences:</label>
        <select id="filter-weight">
          <option value="1">All (w ≥ 1)</option>
          <option value="2">Moderate (w ≥ 2)</option>
          <option value="5">Frequent (w ≥ 5)</option>
        </select>
      </div>
      <div class="ctrl-group">
        <label for="hero-search">Find Hero:</label>
        <input type="text" id="hero-search" list="heroes-datalist" placeholder="e.g. Wolverine, Spider-Man">
        <datalist id="heroes-datalist"></datalist>
      </div>
      <button class="btn-next" id="btn-reset-graph" style="padding: 0.4rem 0.8rem; font-size: 0.8rem;">Reset View</button>
    </div>

    <div class="graph-layout">
      <div class="graph-canvas-wrap">
        <svg id="network-svg" class="network-svg" role="img" aria-label="Marvel co-occurrence and hyperlink graph"></svg>
        <div class="graph-legend">
          <div class="legend-item"><span class="legend-line" style="background:var(--both);"></span> Both (Canonical)</div>
          <div class="legend-item"><span class="legend-line" style="background:var(--link);"></span> Citation Only</div>
          <div class="legend-item"><span class="legend-line" style="background:var(--coocc);"></span> Ghost Link (Story Co-occ)</div>
        </div>
      </div>

      <aside class="inspector-panel" id="inspector-panel">
        <h2>INSPECTOR</h2>
        <p class="text-muted" style="font-size:0.85rem; margin-bottom:1rem;">Click on any node or edge to inspect its structural evidence, citation direction, and sentence concordance.</p>
        <div id="inspector-content">
          <div style="text-align:center; padding: 3rem 1rem; color:var(--text-muted);">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin-bottom:0.75rem; opacity:0.5;">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
            <p>Select a node or edge to reveal concordance excerpts.</p>
          </div>
        </div>
      </aside>
    </div>
  </section>

  <!-- TAB 3: METRICS & HUBS -->
  <section id="metrics-tab" class="tab-content">
    <div class="metrics-container">
      <h2 style="font-family:'Bangers',cursive; font-size: 2rem; color:var(--gold); margin-bottom: 1rem;">STRUCTURAL METRICS COMPARISON</h2>
      <table class="metrics-table">
        <thead>
          <tr>
            <th>Network Layer</th>
            <th>Nodes</th>
            <th>Edges</th>
            <th>Avg Degree ⟨k⟩</th>
            <th>Density</th>
            <th>Clustering C</th>
            <th>Modularity Q</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Wikipedia Links (Undirected)</strong></td>
            <td>303</td>
            <td>1,434</td>
            <td>9.47</td>
            <td>0.0313</td>
            <td>0.307</td>
            <td>0.385</td>
          </tr>
          <tr>
            <td><strong>Sentence Co-occurrence (w ≥ 1)</strong></td>
            <td>303</td>
            <td>1,504</td>
            <td>9.93</td>
            <td>0.0329</td>
            <td>0.404</td>
            <td>0.495</td>
          </tr>
          <tr>
            <td><strong>Sentence Co-occurrence (w ≥ 2)</strong></td>
            <td>232</td>
            <td>724</td>
            <td>6.24</td>
            <td>0.0270</td>
            <td>0.394</td>
            <td>0.543</td>
          </tr>
          <tr>
            <td><strong>Paragraph Co-occurrence (w ≥ 1)</strong></td>
            <td>303</td>
            <td>3,576</td>
            <td>23.60</td>
            <td>0.0782</td>
            <td>0.579</td>
            <td>0.336</td>
          </tr>
        </tbody>
      </table>

      <h2 style="font-family:'Bangers',cursive; font-size: 2rem; color:var(--gold); margin-bottom: 1rem;">TOP HUBS: LINKS VS. CO-OCCURRENCE</h2>
      <p style="color:var(--text-muted); font-size:0.9rem; margin-bottom: 1.5rem;">
        Notice how Spider-Man, Hulk, and Wolverine dominate both layers, but subtle differences emerge: bibliographic hubs like Doctor Strange receive broad citations, whereas street-level and narrative partners cluster heavily in co-occurrence sentences.
      </p>

      <div class="hubs-grid" id="hubs-grid"></div>
    </div>
  </section>

  <script>
    // INJECTED DATASET
    const DATA = {data_json};

    // TAB MANAGEMENT
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {{
      btn.addEventListener('click', () => {{
        tabBtns.forEach(b => b.classList.remove('active'));
        tabContents.forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
        const activeId = btn.dataset.tab;
        document.getElementById(activeId).classList.add('active');
        if (activeId === 'graph-tab' && !graphInitialized) {{
          initGraph();
        }}
      }});
    }});

    // MAP NODES BY ID
    const nodeMap = new Map();
    DATA.nodes.forEach(n => nodeMap.set(n.id, n));

    // POPULATE SEARCH DATALIST
    const datalist = document.getElementById('heroes-datalist');
    DATA.nodes.forEach(n => {{
      const opt = document.createElement('option');
      opt.value = n.clean_name;
      datalist.appendChild(opt);
    }});

    // --- GAME ENGINE ---
    let currentCaseIdx = 0;
    let score = 0;
    let streak = 0;
    let maxStreak = 0;
    let correctCount = 0;
    let answered = false;

    const challenges = DATA.game;

    function renderHeroCard(containerId, nid) {{
      const node = nodeMap.get(nid) || {{ clean_name: nid.replace(/_/g, ' '), image: '', degree_link: 0, degree_sent: 0 }};
      const container = document.getElementById(containerId);
      const initial = (node.clean_name && node.clean_name.length > 0) ? node.clean_name.charAt(0) : '?';
      
      let avatarHtml = '';
      if (node.image) {{
        avatarHtml = `<img src="${{node.image}}" alt="${{node.clean_name}}" class="hero-avatar" onerror="this.style.display='none'; if(this.nextElementSibling) this.nextElementSibling.style.display='flex';"/><div class="hero-avatar-fallback" style="display:none;">${{initial}}</div>`;
      }} else {{
        avatarHtml = `<div class="hero-avatar-fallback">${{initial}}</div>`;
      }}

      container.innerHTML = `
        ${{avatarHtml}}
        <div class="hero-name">${{node.clean_name}}</div>
        <div class="hero-degree-tag">Links: ${{node.degree_link}} · Co-occ: ${{node.degree_sent}}</div>
      `;
    }}

    function loadCase(idx) {{
      answered = false;
      const c = challenges[idx];
      document.getElementById('case-num').innerText = (idx + 1) + ' / ' + challenges.length;
      renderHeroCard('hero-left', c.source);
      renderHeroCard('hero-right', c.target);
      document.getElementById('story-teaser').innerText = '"' + c.teaser + '"';

      const fb = document.getElementById('feedback-box');
      fb.style.display = 'none';
      fb.className = 'feedback-box';

      document.querySelectorAll('.choice-btn').forEach(btn => {{
        btn.disabled = false;
        btn.style.opacity = '1';
        btn.style.borderColor = 'var(--border)';
      }});
    }}

    function handleChoice(choice) {{
      if (answered) return;
      answered = true;

      const c = challenges[currentCaseIdx];
      const isCorrect = (choice === c.answer);
      const mult = Math.min(3, 1 + Math.floor(streak / 2));

      document.querySelectorAll('.choice-btn').forEach(btn => {{
        btn.disabled = true;
        if (btn.dataset.choice === c.answer) {{
          btn.style.borderColor = 'var(--both)';
        }} else if (btn.dataset.choice === choice) {{
          btn.style.borderColor = 'var(--accent)';
        }} else {{
          btn.style.opacity = '0.5';
        }}
      }});

      if (isCorrect) {{
        streak++;
        if (streak > maxStreak) maxStreak = streak;
        correctCount++;
        const pts = 100 * mult;
        score += pts;
      }} else {{
        streak = 0;
      }}

      // Update HUD
      document.getElementById('score-val').innerText = score;
      document.getElementById('streak-val').innerText = streak;
      const newMult = Math.min(3, 1 + Math.floor(streak / 2));
      document.getElementById('mult-badge').innerText = newMult + 'x' + (streak >= 2 ? ' 🔥' : '');

      // Show Feedback
      const fb = document.getElementById('feedback-box');
      fb.style.display = 'block';
      fb.className = 'feedback-box ' + (isCorrect ? 'correct' : 'incorrect');
      document.getElementById('feedback-title').innerText = isCorrect ? 'EXCELLENT INTUITION! +' + (100 * mult) + ' PTS' : 'INTRIGUING GAP!';

      const badge = document.getElementById('feedback-badge');
      const badgeLabels = {{
        both: 'CANONICAL ANCHOR (BOTH)',
        link_only: 'CITATION ONLY (BIBLIOGRAPHIC)',
        coocc_only: 'GHOST LINK (STORY CO-OCCURRENCE)',
        neither: 'DECOY (NEITHER)'
      }};
      badge.innerText = badgeLabels[c.answer] || c.answer.toUpperCase();
      badge.className = 'edge-badge ' + c.answer;

      document.getElementById('feedback-concordance').innerHTML = '<strong>Wikipedia Narrative Evidence:</strong><br/>"' + c.teaser + '"';
      document.getElementById('feedback-insight').innerText = c.why;
    }}

    document.querySelectorAll('.choice-btn').forEach(btn => {{
      btn.addEventListener('click', () => handleChoice(btn.dataset.choice));
    }});

    document.getElementById('btn-next-case').addEventListener('click', () => {{
      if (currentCaseIdx < challenges.length - 1) {{
        currentCaseIdx++;
        loadCase(currentCaseIdx);
      }} else {{
        showGameOver();
      }}
    }});

    function showGameOver() {{
      document.getElementById('matchup-card').style.display = 'none';
      const go = document.getElementById('game-over-box');
      go.style.display = 'block';

      const acc = Math.round((correctCount / challenges.length) * 100);
      document.getElementById('final-score').innerText = score;
      document.getElementById('final-acc').innerText = acc + '%';
      document.getElementById('final-streak').innerText = maxStreak;

      let rank = 'Street Vigilante';
      if (acc >= 90) rank = 'Watcher of the Multiverse 👁️';
      else if (acc >= 75) rank = 'Sorcerer Supreme ✨';
      else if (acc >= 60) rank = 'Avenger 🛡️';
      else if (acc >= 40) rank = 'S.H.I.E.L.D. Special Agent 📂';
      document.getElementById('final-rank').innerText = rank;
    }}

    document.getElementById('btn-restart').addEventListener('click', () => {{
      currentCaseIdx = 0;
      score = 0;
      streak = 0;
      maxStreak = 0;
      correctCount = 0;
      document.getElementById('score-val').innerText = '0';
      document.getElementById('streak-val').innerText = '0';
      document.getElementById('mult-badge').innerText = '1x';
      document.getElementById('matchup-card').style.display = 'block';
      document.getElementById('game-over-box').style.display = 'none';
      loadCase(0);
    }});

    loadCase(0);

    // --- GRAPH EXPLORER (D3) ---
    let graphInitialized = false;
    let simulation, svg, g, linkElements, nodeElements;
    const width = 960;
    const height = 700;

    function initGraph() {{
      graphInitialized = true;
      svg = d3.select('#network-svg')
        .attr('viewBox', [0, 0, width, height]);

      g = svg.append('g');

      // Zoom support
      svg.call(d3.zoom()
        .extent([[0, 0], [width, height]])
        .scaleExtent([0.2, 8])
        .on('zoom', (event) => g.attr('transform', event.transform))
      );

      updateGraphData();
    }}

    function updateGraphData() {{
      const typeFilter = document.getElementById('filter-type').value;
      const minWeight = parseInt(document.getElementById('filter-weight').value, 10);

      // Filter edges
      const filteredEdges = DATA.edges.filter(e => {{
        if (typeFilter !== 'all' && e.type !== typeFilter) return false;
        if (e.type !== 'link_only' && e.sent_weight < minWeight) return false;
        return true;
      }});

      // Active nodes
      const activeNodeIds = new Set();
      filteredEdges.forEach(e => {{
        activeNodeIds.add(e.source.id || e.source);
        activeNodeIds.add(e.target.id || e.target);
      }});

      const filteredNodes = DATA.nodes
        .filter(n => activeNodeIds.has(n.id))
        .map(n => Object.assign({{}}, n));

      const edgeCopies = filteredEdges.map(e => Object.assign({{}}, e));

      g.selectAll('*').remove();

      simulation = d3.forceSimulation(filteredNodes)
        .force('link', d3.forceLink(edgeCopies).id(d => d.id).distance(45))
        .force('charge', d3.forceManyBody().strength(-60))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(14));

      // Color mapping
      const edgeColors = {{
        both: '#10b981',
        link_only: '#3b82f6',
        coocc_only: '#f59e0b'
      }};

      linkElements = g.append('g')
        .attr('stroke-opacity', 0.6)
        .selectAll('line')
        .data(edgeCopies)
        .join('line')
        .attr('stroke', d => edgeColors[d.type] || '#64748b')
        .attr('stroke-width', d => d.type === 'both' ? 2 : 1.2)
        .attr('cursor', 'pointer')
        .on('click', (event, d) => inspectEdge(d));

      nodeElements = g.append('g')
        .selectAll('circle')
        .data(filteredNodes)
        .join('circle')
        .attr('r', d => Math.max(4, Math.min(18, Math.sqrt(d.degree_sent + d.degree_link) * 1.8)))
        .attr('fill', d => d3.schemeTableau10[d.community % 10] || '#94a3b8')
        .attr('stroke', '#0b0f19')
        .attr('stroke-width', 1.5)
        .attr('cursor', 'pointer')
        .on('click', (event, d) => inspectNode(d))
        .call(d3.drag()
          .on('start', dragstarted)
          .on('drag', dragged)
          .on('end', dragended)
        );

      nodeElements.append('title')
        .text(d => d.clean_name + ' (Links: ' + d.degree_link + ', Co-occ: ' + d.degree_sent + ')');

      simulation.on('tick', () => {{
        linkElements
          .attr('x1', d => d.source.x)
          .attr('y1', d => d.source.y)
          .attr('x2', d => d.target.x)
          .attr('y2', d => d.target.y);

        nodeElements
          .attr('cx', d => d.x)
          .attr('cy', d => d.y);
      }});
    }}

    function dragstarted(event) {{
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }}
    function dragged(event) {{
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }}
    function dragended(event) {{
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }}

    document.getElementById('filter-type').addEventListener('change', updateGraphData);
    document.getElementById('filter-weight').addEventListener('change', updateGraphData);
    document.getElementById('btn-reset-graph').addEventListener('click', () => {{
      document.getElementById('hero-search').value = '';
      document.getElementById('filter-type').value = 'all';
      document.getElementById('filter-weight').value = '1';
      updateGraphData();
    }});

    // SEARCH HERO HIGHLIGHT
    document.getElementById('hero-search').addEventListener('input', (e) => {{
      const query = e.target.value.trim().toLowerCase();
      if (!query || !nodeElements) return;

      const targetNode = DATA.nodes.find(n => n.clean_name.toLowerCase() === query || n.id.toLowerCase() === query);
      if (targetNode) {{
        inspectNode(targetNode);
        nodeElements.attr('opacity', d => d.id === targetNode.id ? 1 : 0.25);
        linkElements.attr('opacity', d => (d.source.id === targetNode.id || d.target.id === targetNode.id) ? 1 : 0.05);
      }} else {{
        nodeElements.attr('opacity', 1);
        linkElements.attr('opacity', 0.6);
      }}
    }});

    function inspectNode(node) {{
      const panel = document.getElementById('inspector-content');
      const initial = (node.clean_name && node.clean_name.length > 0) ? node.clean_name.charAt(0) : '?';
      const imgHtml = node.image 
        ? `<img src="${{node.image}}" style="width:70px; height:70px; border-radius:50%; object-fit:cover; border:2px solid var(--gold); margin-bottom:0.75rem;" onerror="this.style.display='none'; if(this.nextElementSibling) this.nextElementSibling.style.display='flex';"/><div class="hero-avatar-fallback" style="display:none; width:70px; height:70px; font-size:1.8rem; margin:0 auto 0.75rem;">${{initial}}</div>`
        : `<div class="hero-avatar-fallback" style="width:70px; height:70px; font-size:1.8rem; margin:0 auto 0.75rem;">${{initial}}</div>`;

      panel.innerHTML = `
        <div style="text-align:center; margin-bottom:1.25rem;">
          ${{imgHtml}}
          <h3 style="font-family:'Bangers',cursive; font-size:1.5rem; color:var(--text);">${{node.clean_name}}</h3>
          <a href="${{node.wiki_url}}" target="_blank" style="font-size:0.78rem; color:var(--gold); text-decoration:none;">Wikipedia Article ↗</a>
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.5rem; margin-bottom:1rem;">
          <div style="background:var(--card); padding:0.6rem; border-radius:6px; text-align:center;">
            <div style="font-size:0.7rem; color:var(--text-muted); font-weight:700;">LINK DEGREE</div>
            <div style="font-family:'Bangers',cursive; font-size:1.4rem; color:var(--link);">${{node.degree_link}}</div>
          </div>
          <div style="background:var(--card); padding:0.6rem; border-radius:6px; text-align:center;">
            <div style="font-size:0.7rem; color:var(--text-muted); font-weight:700;">CO-OCC DEGREE</div>
            <div style="font-family:'Bangers',cursive; font-size:1.4rem; color:var(--coocc);">${{node.degree_sent}}</div>
          </div>
        </div>
        <p style="font-size:0.85rem; color:var(--text-muted); line-height:1.4;">
          <strong>Louvain Community:</strong> #${{node.community}}<br/>
          <strong>Paragraph Degree:</strong> ${{node.degree_para}}
        </p>
      `;
    }}

    function inspectEdge(edge) {{
      const sourceId = edge.source.id || edge.source;
      const targetId = edge.target.id || edge.target;
      const sNode = nodeMap.get(sourceId) || {{ clean_name: sourceId }};
      const tNode = nodeMap.get(targetId) || {{ clean_name: targetId }};
      const panel = document.getElementById('inspector-content');

      const badgeClasses = {{ both: 'both', link_only: 'link_only', coocc_only: 'coocc_only' }};
      const typeLabels = {{ both: 'Canonical Anchor (Both)', link_only: 'Citation Only', coocc_only: 'Narrative Ghost Link' }};

      panel.innerHTML = `
        <span class="edge-badge ${{badgeClasses[edge.type]}}">${{typeLabels[edge.type] || edge.type}}</span>
        <h3 style="font-family:'Bangers',cursive; font-size:1.4rem; margin-bottom:0.75rem;">
          ${{sNode.clean_name}} <span style="color:var(--text-muted);">↔</span> ${{tNode.clean_name}}
        </h3>
        <div style="background:var(--card); padding:0.75rem; border-radius:8px; font-size:0.85rem; margin-bottom:1rem;">
          <div><strong>Sentence Mentions:</strong> ${{edge.sent_weight}}</div>
          <div><strong>Paragraph Mentions:</strong> ${{edge.para_weight}}</div>
          <div><strong>Wikipedia Link:</strong> ${{edge.link ? (edge.link_dirs === 'mutual' ? 'Mutual (Both Ways)' : 'One-way: ' + edge.link_dirs) : 'None (Ghost Edge)'}}</div>
        </div>
        <div>
          <div style="font-size:0.75rem; font-weight:700; color:var(--text-muted); text-transform:uppercase; margin-bottom:0.4rem;">Concordance Evidence:</div>
          <div class="concordance-excerpt" style="font-size:0.85rem; line-height:1.4;">
            "${{edge.excerpt || 'No excerpt available.'}}"
          </div>
        </div>
      `;
    }}

    // --- POPULATE TOP HUBS ---
    function renderHubs() {{
      const hubsGrid = document.getElementById('hubs-grid');
      // Top 10 by either link or sent
      const topIds = ['Spider-Man', 'Hulk', 'Wolverine_(character)', 'Doctor_Strange', 'Iron_Man_(Ultimate_Marvel_character)', 'Deadpool', 'She-Hulk', 'Ghost_Rider_(Johnny_Blaze)', 'Phoenix_Force', 'Venom_(character)'];
      
      const maxVal = 130;
      topIds.forEach(id => {{
        const node = nodeMap.get(id);
        if (!node) return;

        const card = document.createElement('div');
        card.className = 'hub-card';

        const initial = (node.clean_name && node.clean_name.length > 0) ? node.clean_name.charAt(0) : '?';
        let avatarHtml = '';
        if (node.image) {{
          avatarHtml = `<img src="${{node.image}}" alt="${{node.clean_name}}" class="hub-avatar" onerror="this.style.display='none'; if(this.nextElementSibling) this.nextElementSibling.style.display='flex';"/><div class="hub-avatar-fallback" style="display:none;">${{initial}}</div>`;
        }} else {{
          avatarHtml = `<div class="hub-avatar-fallback">${{initial}}</div>`;
        }}

        const linkPct = Math.round((node.degree_link / maxVal) * 100);
        const sentPct = Math.round((node.degree_sent / maxVal) * 100);

        card.innerHTML = `
          <div class="hub-card-header">
            ${{avatarHtml}}
            <div>
              <div class="hub-name">${{node.clean_name}}</div>
              <div style="font-size:0.72rem; color:var(--text-muted);">Community #${{node.community}}</div>
            </div>
          </div>
          <div class="bar-row">
            <span class="bar-label">Links:</span>
            <div class="bar-track">
              <div class="bar-fill" style="width: ${{linkPct}}%; background: var(--link);"></div>
            </div>
            <span class="bar-val">${{node.degree_link}}</span>
          </div>
          <div class="bar-row">
            <span class="bar-label">Co-occ:</span>
            <div class="bar-track">
              <div class="bar-fill" style="width: ${{sentPct}}%; background: var(--coocc);"></div>
            </div>
            <span class="bar-val">${{node.degree_sent}}</span>
          </div>
        `;
        hubsGrid.appendChild(card);
      }});
    }}
    renderHubs();
  </script>
</body>
</html>"""
    return html

def main():
    print("Reading data from:", DATA_FILE)
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    html = generate_html(data)
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"Generated {OUT_HTML} ({len(html):,} bytes)")

if __name__ == "__main__":
    main()
