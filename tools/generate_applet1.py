import json

with open('assets/marvel_data.json', encoding='utf-8') as f:
    data = json.load(f)

nodes_json = json.dumps(data['nodes'])
edges_json = json.dumps(data['edges'])

html_content = f'''<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Marvel Network: Node Radii by In/Out-Degree</title>
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
      --cyan: #38bdf8;
      --pink: #f472b6;
      --amber: #fbbf24;
      --emerald: #34d399;
      --edge: rgba(148, 163, 184, 0.22);
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
      --cyan: #0284c7;
      --pink: #db2777;
      --amber: #d97706;
      --emerald: #059669;
      --edge: rgba(100, 116, 139, 0.25);
    }}
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
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
    /* Top Toolbar */
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
    .toolbar-group {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .toolbar-label {{
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
    }}
    .btn-segmented {{
      display: inline-flex;
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 2px;
      gap: 2px;
    }}
    .seg-btn {{
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-family: var(--font-sans);
      font-size: 0.8rem;
      font-weight: 500;
      padding: 5px 12px;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.15s ease;
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .seg-btn:hover {{
      color: var(--text);
      background: rgba(148, 163, 184, 0.1);
    }}
    .seg-btn.active {{
      background: var(--primary);
      color: #ffffff;
      font-weight: 600;
      box-shadow: 0 1px 3px rgba(0,0,0,0.2);
    }}
    .seg-btn.active.mode-in {{
      background: #0284c7;
    }}
    .seg-btn.active.mode-out {{
      background: #db2777;
    }}
    .seg-btn.active.mode-diff {{
      background: #7c3aed;
    }}
    .btn-pill {{
      background: var(--bg);
      border: 1px solid var(--border);
      color: var(--text);
      font-family: var(--font-sans);
      font-size: 0.78rem;
      font-weight: 500;
      padding: 5px 10px;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.15s ease;
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }}
    .btn-pill:hover {{
      border-color: var(--primary);
      color: var(--primary);
    }}
    .btn-pill.active {{
      background: var(--primary);
      color: #fff;
      border-color: var(--primary);
    }}
    .search-box {{
      position: relative;
      display: flex;
      align-items: center;
    }}
    .search-input {{
      background: var(--bg);
      border: 1px solid var(--border);
      color: var(--text);
      font-family: var(--font-sans);
      font-size: 0.78rem;
      padding: 5px 10px 5px 26px;
      border-radius: 6px;
      width: 140px;
      outline: none;
      transition: width 0.2s ease, border-color 0.2s ease;
    }}
    .search-input:focus {{
      width: 180px;
      border-color: var(--primary);
    }}
    .search-icon {{
      position: absolute;
      left: 8px;
      font-size: 0.75rem;
      color: var(--text-muted);
      pointer-events: none;
    }}
    /* Main Viewport */
    .viewport-container {{
      flex: 1;
      position: relative;
      overflow: hidden;
    }}
    svg.graph-svg {{
      width: 100%;
      height: 100%;
      cursor: grab;
    }}
    svg.graph-svg:active {{
      cursor: grabbing;
    }}
    /* Inspector Card */
    .inspector-card {{
      position: absolute;
      top: 14px;
      right: 14px;
      width: 280px;
      max-width: calc(100% - 28px);
      background: var(--bg-panel);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 14px 16px;
      box-shadow: 0 10px 25px -5px rgba(0,0,0,0.35);
      z-index: 10;
      backdrop-filter: blur(8px);
      transition: opacity 0.2s ease, transform 0.2s ease;
    }}
    .inspector-header {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 8px;
    }}
    .inspector-name {{
      font-size: 1rem;
      font-weight: 700;
      color: var(--text);
      line-height: 1.25;
    }}
    .badge-rank {{
      font-size: 0.7rem;
      font-family: var(--font-mono);
      background: var(--bg-card);
      border: 1px solid var(--border);
      padding: 2px 6px;
      border-radius: 4px;
      color: var(--cyan);
      white-space: nowrap;
    }}
    .inspector-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin: 10px 0;
    }}
    .metric-box {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 8px 10px;
      text-align: center;
    }}
    .metric-val {{
      font-family: var(--font-mono);
      font-size: 1.3rem;
      font-weight: 700;
      line-height: 1;
      margin-bottom: 2px;
    }}
    .metric-val.in {{ color: var(--cyan); }}
    .metric-val.out {{ color: var(--pink); }}
    .metric-lbl {{
      font-size: 0.68rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--text-muted);
    }}
    .inspector-diff {{
      font-size: 0.75rem;
      color: var(--text-muted);
      margin-bottom: 8px;
      display: flex;
      justify-content: space-between;
      border-bottom: 1px dashed var(--border);
      padding-bottom: 6px;
    }}
    .inspector-desc {{
      font-size: 0.76rem;
      color: var(--text-muted);
      line-height: 1.4;
      max-height: 90px;
      overflow-y: auto;
    }}
    /* Floating Legend */
    .graph-legend {{
      position: absolute;
      bottom: 14px;
      left: 14px;
      background: var(--bg-panel);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 10px 14px;
      font-size: 0.75rem;
      z-index: 10;
      box-shadow: 0 4px 12px rgba(0,0,0,0.25);
      display: flex;
      flex-direction: column;
      gap: 6px;
    }}
    .legend-item {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .legend-circle {{
      width: 12px;
      height: 12px;
      border-radius: 50%;
      display: inline-block;
    }}
    .legend-line {{
      width: 18px;
      height: 2px;
      display: inline-block;
    }}
    /* Floating Controls (Zoom) */
    .zoom-controls {{
      position: absolute;
      bottom: 14px;
      right: 14px;
      display: flex;
      flex-direction: column;
      gap: 6px;
      z-index: 10;
    }}
    .zoom-btn {{
      width: 32px;
      height: 32px;
      border-radius: 8px;
      background: var(--bg-panel);
      border: 1px solid var(--border);
      color: var(--text);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }}
    .zoom-btn:hover {{
      border-color: var(--primary);
      color: var(--primary);
    }}
    /* Spider-Man Banner */
    .highlight-banner {{
      position: absolute;
      top: 14px;
      left: 14px;
      background: var(--bg-panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 8px 12px;
      font-size: 0.78rem;
      color: var(--text);
      z-index: 10;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .pulse-dot {{
      width: 8px;
      height: 8px;
      background: #ef4444;
      border-radius: 50%;
      box-shadow: 0 0 8px #ef4444;
      animation: pulse 1.8s infinite;
    }}
    @keyframes pulse {{
      0%, 100% {{ transform: scale(1); opacity: 1; }}
      50% {{ transform: scale(1.4); opacity: 0.7; }}
    }}
  </style>
</head>
<body>

  <!-- Top Toolbar -->
  <div class="applet-toolbar">
    <div class="toolbar-group">
      <span class="toolbar-label">Node Radius:</span>
      <div class="btn-segmented">
        <button class="seg-btn active mode-in" id="btn-mode-in" title="Radius proportional to incoming edges">
          <span style="font-size:0.9rem">↓</span> In-Degree (k_in)
        </button>
        <button class="seg-btn" id="btn-mode-out" title="Radius proportional to outgoing edges">
          <span style="font-size:0.9rem">↑</span> Out-Degree (k_out)
        </button>
        <button class="seg-btn" id="btn-mode-diff" title="Radius proportional to asymmetry (|k_in - k_out|)">
          <span>⇄</span> Asymmetry (|Δk|)
        </button>
      </div>
    </div>

    <div class="toolbar-group">
      <span class="toolbar-label">View Subgraph:</span>
      <button class="btn-pill active" id="btn-focus-spidey" title="Focus Spider-Man and his 106 in / 9 out connections">
        🕸️ Spider-Man Focus
      </button>
      <button class="btn-pill" id="btn-focus-hubs" title="Top 40 most connected Marvel characters">
        👑 Top Hubs
      </button>
      <button class="btn-pill" id="btn-focus-all" title="Full 303 Marvel character network">
        🌌 Full Universe
      </button>
    </div>

    <div class="toolbar-group">
      <div class="search-box">
        <span class="search-icon">🔍</span>
        <input type="text" class="search-input" id="search-input" placeholder="Find character...">
      </div>
    </div>
  </div>

  <!-- Main Viewport -->
  <div class="viewport-container" id="viewport">
    <svg class="graph-svg" id="graph-svg"></svg>

    <!-- Highlight Banner -->
    <div class="highlight-banner" id="banner">
      <div class="pulse-dot"></div>
      <span id="banner-text">Viewing Spider-Man ego-network: <strong>106 incoming links</strong> vs <strong>9 outgoing links</strong></span>
    </div>

    <!-- Inspector Card -->
    <div class="inspector-card" id="inspector">
      <div class="inspector-header">
        <div class="inspector-name" id="insp-name">Spider-Man</div>
        <span class="badge-rank" id="insp-rank">Rank #1 In</span>
      </div>
      <div class="inspector-grid">
        <div class="metric-box">
          <div class="metric-val in" id="insp-in">106</div>
          <div class="metric-lbl">In-Degree ↓</div>
        </div>
        <div class="metric-box">
          <div class="metric-val out" id="insp-out">9</div>
          <div class="metric-lbl">Out-Degree ↑</div>
        </div>
      </div>
      <div class="inspector-diff" id="insp-diff">
        <span>Asymmetry (k_in - k_out):</span>
        <strong style="color:var(--cyan)">+97 (Heavy In-Hub)</strong>
      </div>
      <div class="inspector-desc" id="insp-desc">
        Spider-Man is Marvel's flagship icon. 106 characters reference him in their articles, but his article only references 9 superheroes.
      </div>
    </div>

    <!-- Legend -->
    <div class="graph-legend" id="legend">
      <div style="font-weight:600; margin-bottom: 2px;">Legend</div>
      <div class="legend-item">
        <span class="legend-circle" id="legend-node-dot" style="background:#0284c7;"></span>
        <span id="legend-radius-desc">Radius = In-Degree (k_in)</span>
      </div>
      <div class="legend-item">
        <span class="legend-line" style="background:#38bdf8;"></span>
        <span>Incoming link → Target</span>
      </div>
      <div class="legend-item">
        <span class="legend-line" style="background:#f472b6;"></span>
        <span>Outgoing link from Selected</span>
      </div>
    </div>

    <!-- Zoom Controls -->
    <div class="zoom-controls">
      <button class="zoom-btn" id="zoom-in" title="Zoom In">+</button>
      <button class="zoom-btn" id="zoom-out" title="Zoom Out">−</button>
      <button class="zoom-btn" id="zoom-fit" title="Fit Graph">⊙</button>
    </div>
  </div>

  <script>
    // Embedded Marvel data
    const ALL_NODES = {nodes_json};
    const ALL_EDGES = {edges_json};

    // Node lookup maps
    const nodeMap = new Map();
    ALL_NODES.forEach(n => nodeMap.set(n.id, n));

    // Calculate In/Out neighbors
    const inNeighbors = new Map();
    const outNeighbors = new Map();
    ALL_NODES.forEach(n => {{
      inNeighbors.set(n.id, new Set());
      outNeighbors.set(n.id, new Set());
    }});
    ALL_EDGES.forEach(e => {{
      if (outNeighbors.has(e.source)) outNeighbors.get(e.source).add(e.target);
      if (inNeighbors.has(e.target)) inNeighbors.get(e.target).add(e.source);
    }});

    // State
    let currentMode = 'in'; // 'in', 'out', 'diff'
    let currentScope = 'spidey'; // 'spidey', 'hubs', 'all'
    let selectedNodeId = 'Spider-Man';
    let hoveredNodeId = null;

    // Dimensions
    const container = document.getElementById('viewport');
    let width = container.clientWidth || 800;
    let height = container.clientHeight || 500;

    // SVG & Zoom
    const svg = d3.select('#graph-svg');
    const gMain = svg.append('g');
    const gLinks = gMain.append('g').attr('class', 'links');
    const gNodes = gMain.append('g').attr('class', 'nodes');
    const gLabels = gMain.append('g').attr('class', 'labels');

    const zoom = d3.zoom()
      .scaleExtent([0.2, 5])
      .on('zoom', (event) => gMain.attr('transform', event.transform));

    svg.call(zoom);

    // Filter subgraphs
    function getActiveDataset() {{
      let activeNodes = [];
      let activeEdges = [];

      if (currentScope === 'spidey') {{
        // Spider-Man + all his in and out neighbors
        const spideyIn = inNeighbors.get('Spider-Man') || new Set();
        const spideyOut = outNeighbors.get('Spider-Man') || new Set();
        const idSet = new Set(['Spider-Man', ...spideyIn, ...spideyOut]);

        activeNodes = ALL_NODES.filter(n => idSet.has(n.id)).map(n => ({{ ...n }}));
        activeEdges = ALL_EDGES.filter(e => idSet.has(e.source) && idSet.has(e.target)).map(e => ({{ ...e }}));
      }} else if (currentScope === 'hubs') {{
        // Top 45 connected nodes by in + out
        const sorted = [...ALL_NODES].sort((a,b) => (b.in_deg + b.out_deg) - (a.in_deg + a.out_deg));
        const idSet = new Set(sorted.slice(0, 45).map(n => n.id));
        idSet.add('Spider-Man');
        activeNodes = ALL_NODES.filter(n => idSet.has(n.id)).map(n => ({{ ...n }}));
        activeEdges = ALL_EDGES.filter(e => idSet.has(e.source) && idSet.has(e.target)).map(e => ({{ ...e }}));
      }} else {{
        // All nodes
        activeNodes = ALL_NODES.map(n => ({{ ...n }}));
        activeEdges = ALL_EDGES.map(e => ({{ ...e }}));
      }}

      return {{ nodes: activeNodes, links: activeEdges }};
    }}

    // Radius scaling functions
    function getNodeRadius(d, mode) {{
      if (mode === 'in') {{
        // in_deg ranges 0 to 106. Min 4px, Spider-Man ~40px
        return Math.max(4, Math.sqrt(d.in_deg) * 3.8 + 3.5);
      }} else if (mode === 'out') {{
        // out_deg ranges 0 to 28. Min 4px, max ~26px
        return Math.max(4, Math.sqrt(d.out_deg) * 4.4 + 3.5);
      }} else {{
        // Asymmetry |in - out|
        const diff = Math.abs(d.in_deg - d.out_deg);
        return Math.max(4, Math.sqrt(diff) * 3.6 + 3.5);
      }}
    }}

    function getNodeColor(d, mode) {{
      if (d.id === 'Spider-Man') return '#ef4444'; // Red for Spider-Man
      if (mode === 'in') {{
        // Cyan / Blue scale
        const t = Math.min(1, d.in_deg / 65);
        return d3.interpolateRgb('#38bdf8', '#4338ca')(1 - t);
      }} else if (mode === 'out') {{
        // Pink / Coral scale
        const t = Math.min(1, d.out_deg / 28);
        return d3.interpolateRgb('#fb7185', '#be123c')(1 - t);
      }} else {{
        // Asymmetry: blue for sink (in > out), orange/pink for source (out > in)
        return d.in_deg >= d.out_deg ? '#38bdf8' : '#f59e0b';
      }}
    }}

    // Simulation
    let simulation = null;
    let currentData = {{ nodes: [], links: [] }};

    function updateSimulation() {{
      currentData = getActiveDataset();

      if (simulation) simulation.stop();

      const charge = currentScope === 'spidey' ? -220 : (currentScope === 'hubs' ? -340 : -140);
      const linkDist = currentScope === 'spidey' ? 120 : (currentScope === 'hubs' ? 150 : 80);

      simulation = d3.forceSimulation(currentData.nodes)
        .force('link', d3.forceLink(currentData.links).id(d => d.id).distance(linkDist))
        .force('charge', d3.forceManyBody().strength(charge))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(d => getNodeRadius(d, currentMode) + 6))
        .alphaDecay(0.028);

      renderElements();
      simulation.on('tick', ticked);

      // Trigger fit
      setTimeout(() => fitToView(), 350);
    }}

    let linkElements, nodeElements, labelElements;

    function renderElements() {{
      // Links
      linkElements = gLinks.selectAll('line')
        .data(currentData.links, d => `${{d.source.id || d.source}}-${{d.target.id || d.target}}`)
        .join('line')
        .attr('stroke', 'var(--edge)')
        .attr('stroke-width', 1.2)
        .attr('stroke-opacity', 0.4);

      // Nodes
      nodeElements = gNodes.selectAll('circle')
        .data(currentData.nodes, d => d.id)
        .join('circle')
        .attr('r', d => getNodeRadius(d, currentMode))
        .attr('fill', d => getNodeColor(d, currentMode))
        .attr('stroke', '#ffffff')
        .attr('stroke-width', d => d.id === selectedNodeId ? 3 : 1)
        .attr('stroke-opacity', d => d.id === selectedNodeId ? 1 : 0.4)
        .attr('cursor', 'pointer')
        .call(d3.drag()
          .on('start', dragstarted)
          .on('drag', dragged)
          .on('end', dragended))
        .on('click', (event, d) => {{
          event.stopPropagation();
          selectNode(d.id);
        }})
        .on('mouseenter', (event, d) => {{
          hoveredNodeId = d.id;
          highlightConnections(d.id);
        }})
        .on('mouseleave', () => {{
          hoveredNodeId = null;
          highlightConnections(selectedNodeId);
        }});

      // Labels for top nodes
      labelElements = gLabels.selectAll('text')
        .data(currentData.nodes, d => d.id)
        .join('text')
        .text(d => d.name)
        .attr('font-size', d => d.id === 'Spider-Man' ? '12px' : '10px')
        .attr('font-weight', d => (d.id === 'Spider-Man' || d.in_deg > 25 || d.out_deg > 18) ? '700' : '500')
        .attr('fill', 'var(--text)')
        .attr('text-anchor', 'middle')
        .attr('dy', d => -getNodeRadius(d, currentMode) - 4)
        .style('pointer-events', 'none')
        .style('text-shadow', '0 1px 4px rgba(0,0,0,0.8)')
        .style('opacity', d => {{
          if (d.id === selectedNodeId || d.id === 'Spider-Man') return 1;
          if (currentScope === 'all' && d.in_deg < 20 && d.out_deg < 15) return 0;
          return 0.85;
        }});

      highlightConnections(selectedNodeId);
    }}

    function ticked() {{
      linkElements
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      nodeElements
        .attr('cx', d => d.x)
        .attr('cy', d => d.y);

      labelElements
        .attr('x', d => d.x)
        .attr('y', d => d.y);
    }}

    function dragstarted(event, d) {{
      if (!event.active) simulation.alphaTarget(0.2).restart();
      d.fx = d.x;
      d.fy = d.y;
    }}

    function dragged(event, d) {{
      d.fx = event.x;
      d.fy = event.y;
    }}

    function dragended(event, d) {{
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }}

    // Switch Radii Mode smoothly
    function setRadiiMode(mode) {{
      currentMode = mode;
      document.querySelectorAll('.seg-btn').forEach(btn => btn.classList.remove('active'));
      const activeBtn = document.getElementById(`btn-mode-${{mode}}`);
      if (activeBtn) activeBtn.classList.add('active');

      // Update legend text
      const legendDesc = document.getElementById('legend-radius-desc');
      const legendDot = document.getElementById('legend-node-dot');
      if (mode === 'in') {{
        legendDesc.textContent = 'Radius = In-Degree (k_in)';
        legendDot.style.background = '#0284c7';
      }} else if (mode === 'out') {{
        legendDesc.textContent = 'Radius = Out-Degree (k_out)';
        legendDot.style.background = '#db2777';
      }} else {{
        legendDesc.textContent = 'Radius = |k_in - k_out|';
        legendDot.style.background = '#7c3aed';
      }}

      // Smooth transition of radii and colors
      nodeElements.transition()
        .duration(750)
        .attr('r', d => getNodeRadius(d, currentMode))
        .attr('fill', d => getNodeColor(d, currentMode));

      labelElements.transition()
        .duration(750)
        .attr('dy', d => -getNodeRadius(d, currentMode) - 4);

      // Update simulation collision radius and gently reheat
      simulation.force('collision', d3.forceCollide().radius(d => getNodeRadius(d, currentMode) + 6));
      simulation.alpha(0.3).restart();
    }}

    // Highlight node connections
    function highlightConnections(nodeId) {{
      if (!nodeId || !nodeMap.has(nodeId)) {{
        linkElements.attr('stroke', 'var(--edge)').attr('stroke-opacity', 0.4).attr('stroke-width', 1.2);
        nodeElements.attr('opacity', 1);
        return;
      }}

      const inSet = inNeighbors.get(nodeId) || new Set();
      const outSet = outNeighbors.get(nodeId) || new Set();

      // Style links: Cyan for incoming, Pink for outgoing, dimmed for others
      linkElements
        .attr('stroke', d => {{
          const s = d.source.id || d.source;
          const t = d.target.id || d.target;
          if (t === nodeId) return 'var(--cyan)'; // Incoming
          if (s === nodeId) return 'var(--pink)'; // Outgoing
          return 'var(--edge)';
        }})
        .attr('stroke-width', d => {{
          const s = d.source.id || d.source;
          const t = d.target.id || d.target;
          return (t === nodeId || s === nodeId) ? 2.4 : 0.8;
        }})
        .attr('stroke-opacity', d => {{
          const s = d.source.id || d.source;
          const t = d.target.id || d.target;
          return (t === nodeId || s === nodeId) ? 0.9 : 0.08;
        }});

      // Nodes opacity
      nodeElements
        .attr('opacity', d => {{
          if (d.id === nodeId || inSet.has(d.id) || outSet.has(d.id)) return 1;
          return 0.22;
        }})
        .attr('stroke-width', d => d.id === nodeId ? 3.5 : 1)
        .attr('stroke', d => d.id === nodeId ? '#ffffff' : '#ffffff');

      // Labels opacity
      labelElements.style('opacity', d => {{
        if (d.id === nodeId || d.id === 'Spider-Man' || inSet.has(d.id) || outSet.has(d.id)) return 1;
        return 0.1;
      }});
    }}

    // Select Node and populate inspector
    function selectNode(nodeId) {{
      selectedNodeId = nodeId;
      const node = nodeMap.get(nodeId);
      if (!node) return;

      document.getElementById('insp-name').textContent = node.name;
      document.getElementById('insp-in').textContent = node.in_deg;
      document.getElementById('insp-out').textContent = node.out_deg;

      // Rank
      const inRank = [...ALL_NODES].sort((a,b) => b.in_deg - a.in_deg).findIndex(n => n.id === node.id) + 1;
      document.getElementById('insp-rank').textContent = `Rank #${{inRank}} In`;

      // Difference & Role
      const diff = node.in_deg - node.out_deg;
      const diffEl = document.getElementById('insp-diff');
      let roleText = '';
      if (diff > 20) roleText = `+${{diff}} (Strong Target Hub)`;
      else if (diff > 0) roleText = `+${{diff}} (Target Hub)`;
      else if (diff < -10) roleText = `${{diff}} (Strong Source Hub)`;
      else if (diff < 0) roleText = `${{diff}} (Source / Linker)`;
      else roleText = `0 (Balanced Reciprocal)`;

      diffEl.innerHTML = `<span>Asymmetry (k_in - k_out):</span> <strong style="color:${{diff >= 0 ? 'var(--cyan)' : 'var(--pink)'}}">${{roleText}}</strong>`;

      document.getElementById('insp-desc').textContent = node.desc || 'Marvel Comics character appearing in Wikipedia Category:Marvel Comics superheroes.';

      highlightConnections(nodeId);

      // If banner is active, update
      const bannerText = document.getElementById('banner-text');
      bannerText.innerHTML = `Selected <strong>${{node.name}}</strong>: <strong>${{node.in_deg}} in-links</strong> · <strong>${{node.out_deg}} out-links</strong>`;
    }}

    // Fit Graph to view
    function fitToView() {{
      if (!currentData.nodes.length) return;
      const bounds = gNodes.node().getBBox();
      if (!bounds || bounds.width === 0 || bounds.height === 0) return;

      const fullWidth = container.clientWidth || 800;
      const fullHeight = container.clientHeight || 500;
      const midX = bounds.x + bounds.width / 2;
      const midY = bounds.y + bounds.height / 2;

      const scale = 0.85 / Math.max(bounds.width / fullWidth, bounds.height / fullHeight);
      const translate = [fullWidth / 2 - scale * midX, fullHeight / 2 - scale * midY];

      svg.transition()
        .duration(650)
        .call(zoom.transform, d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale));
    }}

    // Event wiring
    document.getElementById('btn-mode-in').onclick = () => setRadiiMode('in');
    document.getElementById('btn-mode-out').onclick = () => setRadiiMode('out');
    document.getElementById('btn-mode-diff').onclick = () => setRadiiMode('diff');

    document.getElementById('btn-focus-spidey').onclick = function() {{
      currentScope = 'spidey';
      document.querySelectorAll('.toolbar-group .btn-pill').forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      selectNode('Spider-Man');
      updateSimulation();
    }};

    document.getElementById('btn-focus-hubs').onclick = function() {{
      currentScope = 'hubs';
      document.querySelectorAll('.toolbar-group .btn-pill').forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      updateSimulation();
    }};

    document.getElementById('btn-focus-all').onclick = function() {{
      currentScope = 'all';
      document.querySelectorAll('.toolbar-group .btn-pill').forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      updateSimulation();
    }};

    // Search
    const searchInput = document.getElementById('search-input');
    searchInput.addEventListener('input', (e) => {{
      const q = e.target.value.toLowerCase().trim();
      if (!q) return;
      const match = ALL_NODES.find(n => n.name.toLowerCase().includes(q) || n.id.toLowerCase().includes(q));
      if (match) {{
        selectNode(match.id);
      }}
    }});

    // Zoom buttons
    document.getElementById('zoom-in').onclick = () => svg.transition().duration(250).call(zoom.scaleBy, 1.3);
    document.getElementById('zoom-out').onclick = () => svg.transition().duration(250).call(zoom.scaleBy, 0.77);
    document.getElementById('zoom-fit').onclick = () => fitToView();

    // Click on canvas background deselects
    svg.on('click', () => {{
      highlightConnections(null);
    }});

    // Window resize
    window.addEventListener('resize', () => {{
      width = container.clientWidth || 800;
      height = container.clientHeight || 500;
      if (simulation) {{
        simulation.force('center', d3.forceCenter(width / 2, height / 2));
        simulation.alpha(0.2).restart();
      }}
    }});

    // Theme sync with parent
    function syncTheme() {{
      try {{
        const parentTheme = window.parent && window.parent.document && window.parent.document.documentElement.getAttribute('data-theme');
        const theme = parentTheme || localStorage.getItem('theme') || 'dark';
        document.documentElement.setAttribute('data-theme', theme);
      }} catch (e) {{
        document.documentElement.setAttribute('data-theme', localStorage.getItem('theme') || 'dark');
      }}
    }}
    syncTheme();
    try {{
      if (window.parent && window.parent.document) {{
        const observer = new MutationObserver(() => syncTheme());
        observer.observe(window.parent.document.documentElement, {{ attributes: true, attributeFilter: ['data-theme'] }});
      }}
    }} catch (e) {{}}

    // Init
    selectNode('Spider-Man');
    updateSimulation();
  </script>
</body>
</html>
'''

with open('assets/applets/degree-radii.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"Successfully created assets/applets/degree-radii.html ({len(html_content)} bytes)")
