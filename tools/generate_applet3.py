"""Generate applet 3: Marvel network vs random / Watts-Strogatz / Barabasi-Albert.

Produces:
  - assets/model_comparison.json      (all computed data for the article)
  - assets/applets/network-models-comparison.html  (interactive D3 applet)
"""

import json
import math
import random

import networkx as nx

SEED = 42
DATA_NODES = 'week1_nodes.tsv'
DATA_EDGES = 'week1_edges.tsv'


def load_marvel():
    """Return undirected Marvel graph (303 nodes, unique edges)."""
    nodes = []
    with open(DATA_NODES, encoding='utf-8') as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            parts = line.rstrip('\n').split('\t')
            if parts[0] == 'node_id':  # header
                continue
            nodes.append(parts[0])

    edges = set()
    with open(DATA_EDGES, encoding='utf-8') as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            s, t = line.rstrip('\n').split('\t')
            if s == t:
                continue
            edges.add(tuple(sorted((s, t))))

    G = nx.Graph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)
    return G


def degree_distribution(G):
    """Return sorted [{k, count, p}] for observed degrees."""
    counts = {}
    for _, d in G.degree():
        counts[d] = counts.get(d, 0) + 1
    total = G.number_of_nodes()
    return [{"k": k, "count": counts[k], "p": round(counts[k] / total, 6)}
            for k in sorted(counts)]


def summarize(G, name):
    ccs = sorted(nx.connected_components(G), key=len, reverse=True)
    gc = G.subgraph(ccs[0])
    degrees = [d for _, d in G.degree()]
    return {
        "id": name,
        "N": G.number_of_nodes(),
        "M": G.number_of_edges(),
        "avg_degree": round(2 * G.number_of_edges() / G.number_of_nodes(), 3),
        "clustering": round(nx.average_clustering(G), 4),
        "avg_path": round(nx.average_shortest_path_length(gc), 3),
        "diameter": nx.diameter(gc),
        "components": nx.number_connected_components(G),
        "gc_size": len(ccs[0]),
        "gc_frac": round(len(ccs[0]) / G.number_of_nodes(), 4),
        "max_degree": max(degrees),
        "assortativity": round(nx.degree_assortativity_coefficient(G), 4),
    }


def build_networks():
    random.seed(SEED)

    G_marvel = load_marvel()
    N = G_marvel.number_of_nodes()
    M = G_marvel.number_of_edges()

    # Erdos-Renyi G(N, M): exact same edge count.
    G_er = nx.gnm_random_graph(N, M, seed=SEED)

    # Watts-Strogatz: ring with k=10 (1515 edges) rewired at p=0.2,
    # then a small random fraction of edges removed to match M exactly.
    WS_K, WS_P = 10, 0.2
    G_ws = nx.watts_strogatz_graph(N, WS_K, WS_P, seed=SEED)
    drop_ws = G_ws.number_of_edges() - M
    G_ws.remove_edges_from(random.sample(list(G_ws.edges()), drop_ws))

    # Barabasi-Albert: m=5 (1490 edges), then remove few edges to match M.
    BA_M = 5
    G_ba = nx.barabasi_albert_graph(N, BA_M, seed=SEED)
    drop_ba = G_ba.number_of_edges() - M
    G_ba.remove_edges_from(random.sample(list(G_ba.edges()), drop_ba))

    networks = {
        "marvel": G_marvel,
        "g_nm": G_er,
        "watts_strogatz": G_ws,
        "barabasi_albert": G_ba,
    }
    return networks, N, M, {"ws_k": WS_K, "ws_p": WS_P, "ba_m": BA_M}


def main():
    networks, N, M, params = build_networks()

    labels = {
        "marvel": "Marvel universe",
        "g_nm": "Erdős–Rényi G(N, M)",
        "watts_strogatz": "Watts–Strogatz",
        "barabasi_albert": "Barabási–Albert",
    }
    colors = {
        "marvel": "#ef4444",
        "g_nm": "#38bdf8",
        "watts_strogatz": "#34d399",
        "barabasi_albert": "#fbbf24",
    }

    summary = []
    distributions = {}
    for key, G in networks.items():
        stats = summarize(G, key)
        stats["label"] = labels[key]
        stats["color"] = colors[key]
        stats["dist"] = degree_distribution(G)
        summary.append({k: v for k, v in stats.items() if k != "dist"})
        distributions[key] = stats["dist"]

    out = {
        "seed": SEED,
        "total_nodes": N,
        "total_edges": M,
        "generation": {
            "erdos_renyi": "G(N, M): exactly M random edges among N nodes",
            "watts_strogatz": f"ring k={params['ws_k']}, rewiring p={params['ws_p']} (edges trimmed to {M})",
            "barabasi_albert": f"m={params['ba_m']} edges per new node (edges trimmed to {M})",
        },
        "summary": summary,
        "distributions": distributions,
    }

    with open('assets/model_comparison.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    html = render_html(out)
    with open('assets/applets/network-models-comparison.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("Generated assets/model_comparison.json")
    print("Generated assets/applets/network-models-comparison.html")
    for row in summary:
        print(row)


def render_html(data):
    summary_json = json.dumps(data['summary'])
    dist_json = json.dumps(data['distributions'])
    gen_json = json.dumps(data['generation'])
    n = data['total_nodes']
    m = data['total_edges']

    return f'''<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Marvel vs. Random / Small-World / Scale-Free Networks</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js"></script>
  <style>
    :root {{
      --bg: #0f172a;
      --bg-panel: #1e293b;
      --bg-card: #090d16;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --border: #334155;
      --primary: #6366f1;
      --grid: rgba(148, 163, 184, 0.12);
      --marvel: #ef4444;
      --er: #38bdf8;
      --ws: #34d399;
      --ba: #fbbf24;
      --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
    }}
    [data-theme="light"] {{
      --bg: #ffffff;
      --bg-panel: #f8fafc;
      --bg-card: #f1f5f9;
      --text: #0f172a;
      --text-muted: #64748b;
      --border: #e2e8f0;
      --primary: #4f46e5;
      --grid: rgba(100, 116, 139, 0.15);
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: var(--font-sans);
      overflow: hidden;
      width: 100vw;
      height: 100vh;
      display: flex;
      flex-direction: column;
      user-select: none;
    }}
    .applet-toolbar {{
      background: var(--bg-panel);
      border-bottom: 1px solid var(--border);
      padding: 10px 16px;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      z-index: 20;
    }}
    .toolbar-group {{ display: flex; align-items: center; gap: 8px; }}
    .toolbar-label {{
      font-size: 0.75rem; font-weight: 600; text-transform: uppercase;
      letter-spacing: 0.05em; color: var(--text-muted);
    }}
    .btn-segmented {{ display: inline-flex; background: var(--bg); border: 1px solid var(--border); border-radius: 8px; padding: 2px; gap: 2px; }}
    .seg-btn {{
      background: transparent; border: none; color: var(--text-muted);
      font-family: var(--font-sans); font-size: 0.8rem; font-weight: 500;
      padding: 5px 11px; border-radius: 6px; cursor: pointer;
      transition: all 0.15s ease; display: flex; align-items: center; gap: 6px;
    }}
    .seg-btn:hover {{ color: var(--text); background: rgba(148, 163, 184, 0.1); }}
    .seg-btn.active {{ background: var(--primary); color: #fff; font-weight: 600; box-shadow: 0 1px 3px rgba(0,0,0,0.2); }}
    .seg-btn.active.marvel {{ background: var(--marvel); }}
    .seg-btn.active.g_nm {{ background: var(--er); }}
    .seg-btn.active.watts_strogatz {{ background: var(--ws); }}
    .seg-btn.active.barabasi_albert {{ background: var(--ba); }}
    .net-dot {{ display: inline-block; width: 9px; height: 9px; border-radius: 50%; }}
    .main-area {{ flex: 1; position: relative; overflow: hidden; }}
    .chart-container {{ width: 100%; height: 100%; position: relative; }}
    svg.plot-svg {{ width: 100%; height: 100%; display: block; }}
    .axis line, .axis path {{ stroke: var(--border); }}
    .axis text {{ fill: var(--text-muted); font-family: var(--font-mono); font-size: 11px; }}
    .grid line {{ stroke: var(--grid); stroke-dasharray: 2, 3; }}
    .plot-tooltip {{
      position: absolute; pointer-events: none; background: var(--bg-panel);
      border: 1px solid var(--border); border-radius: 8px; padding: 8px 12px;
      font-size: 0.78rem; box-shadow: 0 8px 20px rgba(0,0,0,0.35);
      z-index: 30; opacity: 0; transition: opacity 0.15s ease; max-width: 250px;
    }}
    .legend-wrap {{
      position: absolute; top: 14px; left: 14px; background: var(--bg-panel);
      border: 1px solid var(--border); border-radius: 10px; padding: 10px 14px;
      font-size: 0.75rem; z-index: 10; box-shadow: 0 4px 12px rgba(0,0,0,0.25);
      display: flex; flex-direction: column; gap: 6px; min-width: 220px;
    }}
    .legend-item {{ display: flex; align-items: center; gap: 8px; }}
    .legend-line {{ width: 18px; height: 3px; border-radius: 2px; display: inline-block; }}
    .legend-off {{ opacity: 0.25; }}
    .counter {{ font-family: var(--font-mono); font-size: 0.78rem; color: var(--text); margin-top: 2px; padding-top: 6px; border-top: 1px dashed var(--border); }}
    .bar-axis text {{ fill: var(--text-muted); font-size: 11px; }}
    .table-wrap {{
      position: absolute; bottom: 14px; left: 14px; right: 14px;
      background: var(--bg-panel); border: 1px solid var(--border);
      border-radius: 10px; overflow: hidden; z-index: 10; box-shadow: 0 4px 12px rgba(0,0,0,0.25);
    }}
    table.compare-table {{ width: 100%; border-collapse: collapse; font-size: 0.72rem; }}
    .compare-table th, .compare-table td {{ padding: 6px 8px; text-align: right; white-space: nowrap; }}
    .compare-table th {{ color: var(--text-muted); text-transform: uppercase; font-size: 0.62rem; letter-spacing: 0.03em; font-weight: 600; }}
    .compare-table td:first-child, .compare-table th:first-child {{ text-align: left; font-weight: 600; }}
    .compare-table tr {{ border-bottom: 1px solid var(--border); }}
    .compare-table tbody tr:last-child {{ border-bottom: none; }}
    .metric-key {{ color: var(--text-muted); font-size: 0.7rem; margin-bottom: 2px; }}
    .metric-num {{ font-family: var(--font-mono); font-weight: 700; font-size: 1.05rem; }}
  </style>
</head>
<body>

  <div class="applet-toolbar">
    <div class="toolbar-group">
      <span class="toolbar-label">View:</span>
      <div class="btn-segmented">
        <button class="seg-btn active" id="view-dist" title="Degree distributions on log-log axes">📈 Distributions</button>
        <button class="seg-btn" id="view-metrics" title="Clustering and path-length comparison">📊 Topology Metrics</button>
      </div>
    </div>
    <div class="toolbar-group">
      <span class="toolbar-label">Networks:</span>
      <div class="btn-segmented" id="net-buttons">
        <button class="seg-btn active marvel" data-net="marvel"><span class="net-dot" style="background:#ef4444"></span>Marvel</button>
        <button class="seg-btn active g_nm" data-net="g_nm"><span class="net-dot" style="background:#38bdf8"></span>Erdős–Rényi</button>
        <button class="seg-btn active watts_strogatz" data-net="watts_strogatz"><span class="net-dot" style="background:#34d399"></span>Watts–Strogatz</button>
        <button class="seg-btn active barabasi_albert" data-net="barabasi_albert"><span class="net-dot" style="background:#fbbf24"></span>Barabási–Albert</button>
      </div>
    </div>
  </div>

  <div class="main-area" id="main-area">
    <div class="chart-container" id="chart-container">
      <svg class="plot-svg" id="plot-svg"></svg>
      <div class="plot-tooltip" id="tooltip"></div>
      <div class="legend-wrap" id="legend"></div>
      <div class="table-wrap" id="table-wrap" style="display:none;"></div>
    </div>
  </div>

  <script>
    // Embedded data =========================================================
    const SUMMARY = {summary_json};
    const DIST = {dist_json};
    const GENERATION = {gen_json};
    const TOTAL_N = {n};
    const TOTAL_M = {m};

    // State
    let view = 'dist';
    const active = {{ marvel: true, g_nm: true, watts_strogatz: true, barabasi_albert: true }};
    const COLORS = {{ marvel: '#ef4444', g_nm: '#38bdf8', watts_strogatz: '#34d399', barabasi_albert: '#fbbf24' }};

    const container = document.getElementById('chart-container');
    const svg = d3.select('#plot-svg');
    const tooltip = document.getElementById('tooltip');
    const legendEl = document.getElementById('legend');
    const margin = {{ top: 42, right: 30, bottom: 58, left: 72 }};

    function netLabel(id) {{
      const m = SUMMARY.find(s => s.id === id);
      return m ? m.label : id;
    }}

    // ========================================================================
    // DISTRIBUTION VIEW
    // ========================================================================
    function renderDistributions() {{
      const width = container.clientWidth || 700;
      const height = container.clientHeight || 500;
      const plotW = width - margin.left - margin.right;
      const plotH = height - margin.top - margin.bottom;

      svg.selectAll('*').remove();
      if (!Object.keys(DIST).some(id => active[id])) {{
        svg.append('text').attr('x', width/2).attr('y', height/2).attr('text-anchor', 'middle')
          .attr('fill', 'var(--text-muted)').attr('font-size', '13px')
          .text('Enable at least one network to see its degree distribution.');
        return;
      }}
      const g = svg.append('g').attr('transform', `translate(${{margin.left}},${{margin.top}})`);

      const allK = [];
      const allP = [];
      Object.keys(DIST).forEach(id => {{
        if (!active[id]) return;
        DIST[id].forEach(d => {{ allK.push(d.k); allP.push(Math.max(d.p, 1e-6)); }});
      }});
      // Marvel max degree dominates the x-range; keep common window
      const maxK = d3.max(Object.keys(DIST).map(id => d3.max(DIST[id].filter(d => active[id]).map(d => d.k))));

      const xScale = d3.scaleLog().domain([1, maxK * 1.15]).range([0, plotW]);
      let yMax = d3.max(allP) * 2.2;
      if (!isFinite(yMax) || yMax <= 0) yMax = 1;
      const yScale = d3.scaleLog().domain([0.0004, yMax]).range([plotH, 0]).nice();

      // Grid
      g.append('g').attr('class', 'grid')
        .attr('transform', `translate(0,${{plotH}})`)
        .call(d3.axisBottom(xScale).ticks(6, '~s').tickSize(-plotH).tickFormat(''));
      g.append('g').attr('class', 'grid')
        .call(d3.axisLeft(yScale).ticks(6, '~s').tickSize(-plotW).tickFormat(''));

      // Axes
      g.append('g').attr('class', 'axis x-axis')
        .attr('transform', `translate(0,${{plotH}})`)
        .call(d3.axisBottom(xScale).ticks(6, '~s'));
      g.append('g').attr('class', 'axis y-axis')
        .call(d3.axisLeft(yScale).ticks(6, '~s'));

      g.append('text').attr('x', plotW / 2).attr('y', plotH + 42).attr('text-anchor', 'middle')
        .attr('fill', 'var(--text)').attr('font-size', '12px').attr('font-weight', '600')
        .text('Degree k (log scale)');
      g.append('text').attr('transform', 'rotate(-90)').attr('x', -plotH / 2).attr('y', -52)
        .attr('text-anchor', 'middle').attr('fill', 'var(--text)').attr('font-size', '12px')
        .attr('font-weight', '600')
        .text('P(k) = fraction of nodes (log scale)');

      // Distribution curves
      const order = ['barabasi_albert', 'watts_strogatz', 'g_nm', 'marvel'];
      order.forEach(id => {{
        if (!active[id]) return;
        const pts = DIST[id].map(d => ({{ x: Math.max(d.k, 1), y: Math.max(d.p, 1e-6), k: d.k, count: d.count, p: d.p }}));
        const lineGen = d3.line()
          .x(d => xScale(d.x)).y(d => yScale(d.y)).curve(d3.curveMonotoneX);

        g.append('path')
          .datum(pts)
          .attr('fill', 'none')
          .attr('stroke', COLORS[id])
          .attr('stroke-width', id === 'marvel' ? 3 : 2)
          .attr('stroke-dasharray', id === 'marvel' ? 'none' : '6, 4')
          .attr('stroke-opacity', 0.95)
          .attr('opacity', id === 'marvel' ? 1 : 0.8)
          .attr('d', lineGen);

        g.selectAll(`.dot-${{id}}`)
          .data(pts)
          .join('circle')
          .attr('cx', d => xScale(d.x))
          .attr('cy', d => yScale(d.y))
          .attr('r', id === 'marvel' ? 4.5 : 3.2)
          .attr('fill', COLORS[id])
          .attr('stroke', '#ffffff')
          .attr('stroke-width', 1)
          .attr('cursor', 'pointer')
          .on('mouseenter', (event, d) => showDistTip(event, id, d))
          .on('mousemove', (event) => moveTip(event))
          .on('mouseleave', hideTip);
      }});
    }}

    function showDistTip(event, netId, d) {{
      dimLegend();
      const legendRow = document.querySelector(`#legend [data-grow="${{netId}}"]`);
      if (legendRow) legendRow.classList.remove('legend-off');
      tooltip.style.opacity = 1;
      tooltip.innerHTML = `
        <div style="font-weight:700; color:${{COLORS[netId]}}; margin-bottom:4px;">${{netLabel(netId)}}</div>
        <div style="margin-bottom:2px;">Degree <strong>k = ${{d.k}}</strong></div>
        <div style="margin-bottom:2px;"><strong>${{d.count}}</strong> node${{d.count === 1 ? '' : 's'}}</div>
        <div style="font-size:0.72rem; color:var(--text-muted);">P(k) = ${{d.p.toFixed(4)}}</div>
      `;
      moveTip(event);
    }}

    // ========================================================================
    // METRIC VIEW
    // ========================================================================
    function renderMetrics() {{
      const width = container.clientWidth || 700;
      const height = container.clientHeight || 500;
      const plotW = width - margin.left - margin.right;
      const plotH = height - margin.top - margin.bottom;

      const rows = SUMMARY.filter(s => active[s.id]);
      if (!rows.length) return;

      // --- Grouped bar chart: two sub-plots (clustering, avg path) ---
      svg.selectAll('*').remove();
      const g = svg.append('g').attr('transform', `translate(${{margin.left}},${{margin.top}})`);

      const panelGap = 18;
      const halfW = (plotW - panelGap) / 2;
      const barMargin = {{ top: 6, bottom: 34 }};
      const barH = plotH - barMargin.top - barMargin.bottom;

      // Palette for the grouped bars
      const palette = ['#ef4444', '#38bdf8', '#34d399', '#fbbf24'];
      const rowColors = rows.map((r, i) => ({{ id: r.id, color: r.id === 'marvel' ? '#ef4444' : palette[i] }}));

      const panels = [
        {{ key: 'clustering', title: 'Average Clustering Coefficient C', fmt: v => v.toFixed(3), yLabel: 'C' }},
        {{ key: 'avg_path', title: 'Average Shortest Path Length L', fmt: v => v.toFixed(2), yLabel: 'L' }},
      ];

      panels.forEach((panel, pi) => {{
        const px = pi * (halfW + panelGap);
        const values = rows.map(r => r[panel.key]);
        const yMax = d3.max(values) * 1.2;
        const y = d3.scaleLinear().domain([0, yMax]).range([barH, 0]).nice();
        const xBand = d3.scaleBand().domain(rows.map(r => r.id)).range([0, halfW]).padding(0.3);

        // gridlines
        g.append('g').attr('class', 'grid')
          .call(d3.axisLeft(y).ticks(4).tickSize(-halfW).tickFormat(''));

        g.append('g').attr('class', 'axis y-axis')
          .call(d3.axisLeft(y).ticks(4));

        rows.forEach((r, ri) => {{
          g.append('rect')
            .attr('x', px + xBand(r.id))
            .attr('y', y(r[panel.key]))
            .attr('width', xBand.bandwidth())
            .attr('height', barH - y(r[panel.key]))
            .attr('fill', rowColors[ri].color)
            .attr('rx', 4)
            .attr('opacity', r.id === 'marvel' ? 1 : 0.85)
            .attr('cursor', 'pointer')
            .on('mouseenter', (event) => showMetricTip(event, panel, r))
            .on('mousemove', (event) => moveTip(event))
            .on('mouseleave', hideTip);

          g.append('rect')
            .attr('x', px + xBand(r.id))
            .attr('y', 0)
            .attr('width', xBand.bandwidth())
            .attr('height', barH)
            .attr('fill', 'transparent')
            .attr('pointer-events', 'all')
            .attr('cursor', 'pointer')
            .on('mouseenter', (event) => showMetricTip(event, panel, r))
            .on('mousemove', (event) => moveTip(event))
            .on('mouseleave', hideTip);
        }});

        // bars labels
        rows.forEach((r, ri) => {{
          g.append('text')
            .attr('x', px + xBand(r.id) + xBand.bandwidth() / 2)
            .attr('y', y(r[panel.key]) - 5)
            .attr('text-anchor', 'middle')
            .attr('fill', rowColors[ri].color)
            .attr('font-family', 'var(--font-mono)')
            .attr('font-weight', '700')
            .attr('font-size', '11px')
            .text(panel.fmt(r[panel.key]));
        }});

        // panel title
        g.append('text')
          .attr('x', px + halfW / 2)
          .attr('y', -4)
          .attr('text-anchor', 'middle')
          .attr('fill', 'var(--text)')
          .attr('font-size', '11px')
          .attr('font-weight', '700')
          .text(panel.title);

        // x labels
        rows.forEach((r) => {{
          g.append('text')
            .attr('x', px + xBand(r.id) + xBand.bandwidth() / 2)
            .attr('y', barH + 16)
            .attr('text-anchor', 'middle')
            .attr('fill', 'var(--text-muted)')
            .attr('font-size', '10px')
            .text(shortLabel(r.id));
        }});
      }});

      // --- Comparison table ---
      const tableWrap = document.getElementById('table-wrap');
      tableWrap.style.display = 'block';
      const head = ['Network', 'N', 'M', '<k>', 'C (clust.)', 'L (path)', 'Diam.', 'Comps.', 'Giant %', 'max k'];
      const rowsHtml = rows.map(r => `
        <tr>
          <td><span class="net-dot" style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${{r.color}};margin-right:6px;"></span>${{r.label}}</td>
          <td>${{r.N}}</td><td>${{r.M}}</td><td>${{r.avg_degree}}</td>
          <td>${{r.clustering}}</td><td>${{r.avg_path}}</td><td>${{r.diameter}}</td>
          <td>${{r.components}}</td><td>${{(r.gc_frac * 100).toFixed(1)}}%</td><td>${{r.max_degree}}</td>
        </tr>`).join('');

      tableWrap.innerHTML = `
        <table class="compare-table">
          <thead><tr>${{head.map(h => `<th>${{h}}</th>`).join('')}}</tr></thead>
          <tbody>${{rowsHtml}}</tbody>
        </table>`;

      buildLegend(rows);
    }}

    function shortLabel(id) {{
      return {{ marvel: 'Marvel', g_nm: 'E–R', watts_strogatz: 'W–S', barabasi_albert: 'B–A' }}[id] || id;
    }}

    function showMetricTip(event, panel, r) {{
      dimLegend();
      const legendRow = document.querySelector(`#legend [data-grow="${{r.id}}"]`);
      if (legendRow) legendRow.classList.remove('legend-off');
      const label = panel.key === 'clustering' ? 'Average clustering C' : 'Average path length L';
      const mark = panel.key === 'clustering'
        ? 'C = ' + r.clustering.toFixed(3)
        : 'L = ' + r.avg_path.toFixed(2);
      tooltip.style.opacity = 1;
      tooltip.innerHTML = `
        <div style="font-weight:700; color:${{r.color}}; margin-bottom:4px;">${{r.label}}</div>
        <div style="margin-bottom:2px;">${{label}}</div>
        <div style="font-family:var(--font-mono); font-weight:700;">${{mark}}</div>
      `;
      moveTip(event);
    }}

    function buildLegend(rows) {{
      legendEl.innerHTML = `
        <div style="font-weight:600; margin-bottom:2px;">Legend — ${{view === 'dist' ? 'Degrees P(k), log–log' : 'Network models'}}</div>
        ${{rows.map(r => `
          <div class="legend-item" data-grow="${{r.id}}">
            <span class="legend-line" style="background:${{r.color}}"></span>
            <span>${{r.label}}</span>
          </div>`).join('')}}
        <div class="counter">All four networks share the same size: N = ${{TOTAL_N}}, M = ${{TOTAL_M}}</div>
      `;
    }}

    // ========================================================================
    // Tooltip / legend helpers
    // ========================================================================
    function dimLegend() {{
      document.querySelectorAll('#legend .legend-item').forEach(el => el.classList.add('legend-off'));
    }}
    function moveTip(event) {{
      const rect = container.getBoundingClientRect();
      tooltip.style.left = (event.clientX - rect.left + 14) + 'px';
      tooltip.style.top = (event.clientY - rect.top - 24) + 'px';
    }}
    function hideTip() {{
      tooltip.style.opacity = 0;
      document.querySelectorAll('#legend .legend-item').forEach(el => el.classList.remove('legend-off'));
    }}

    function render() {{
      if (view === 'dist') {{
        document.getElementById('table-wrap').style.display = 'none';
        renderDistributions();
        const rows = SUMMARY.filter(s => active[s.id]);
        buildLegend(rows);
      }} else {{
        renderMetrics();
      }}
    }}

    // Controls ---------------------------------------------------------------
    document.getElementById('view-dist').onclick = () => {{
      view = 'dist';
      document.querySelectorAll('#view-dist, #view-metrics').forEach(b => b.classList.remove('active'));
      document.getElementById('view-dist').classList.add('active');
      render();
    }};
    document.getElementById('view-metrics').onclick = () => {{
      view = 'metrics';
      document.querySelectorAll('#view-dist, #view-metrics').forEach(b => b.classList.remove('active'));
      document.getElementById('view-metrics').classList.add('active');
      render();
    }};

    document.querySelectorAll('#net-buttons .seg-btn').forEach(btn => {{
      btn.onclick = () => {{
        const net = btn.dataset.net;
        active[net] = !active[net];
        btn.classList.toggle('active', active[net]);
        render();
      }};
    }});

    window.addEventListener('resize', () => render());

    // Theme sync -------------------------------------------------------------
    function syncTheme() {{
      try {{
        const parentTheme = window.parent && window.parent.document && window.parent.document.documentElement.getAttribute('data-theme');
        const theme = parentTheme || localStorage.getItem('theme') || 'dark';
        document.documentElement.setAttribute('data-theme', theme);
      }} catch (e) {{}}
      render();
    }}

    syncTheme();
    try {{
      if (window.parent && window.parent.document) {{
        const observer = new MutationObserver(() => syncTheme());
        observer.observe(window.parent.document.documentElement, {{ attributes: true, attributeFilter: ['data-theme'] }});
      }}
    }} catch (e) {{}}
  </script>
</body>
</html>
'''


if __name__ == '__main__':
    main()