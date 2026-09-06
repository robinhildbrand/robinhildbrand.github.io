import json
import math

with open('assets/marvel_data.json', encoding='utf-8') as f:
    data = json.load(f)

in_dist_json = json.dumps(data['in_degree_distribution'])
out_dist_json = json.dumps(data['out_degree_distribution'])
summary_json = json.dumps(data['summary'])

html_content = f'''<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Marvel Network: Degree Distribution & Power Law</title>
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
      --grid: rgba(148, 163, 184, 0.12);
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
      --grid: rgba(100, 116, 139, 0.15);
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
    /* Toolbar */
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
    .toggle-chip {{
      background: var(--bg);
      border: 1px solid var(--border);
      color: var(--text-muted);
      font-family: var(--font-sans);
      font-size: 0.78rem;
      font-weight: 500;
      padding: 5px 10px;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.15s ease;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }}
    .toggle-chip:hover {{
      color: var(--text);
      border-color: var(--primary);
    }}
    .toggle-chip.active {{
      background: rgba(99, 102, 241, 0.15);
      color: var(--primary);
      border-color: var(--primary);
      font-weight: 600;
    }}
    /* Main Layout */
    .viewport-container {{
      flex: 1;
      position: relative;
      display: flex;
      overflow: hidden;
    }}
    .chart-area {{
      flex: 1;
      position: relative;
      overflow: hidden;
    }}
    svg.plot-svg {{
      width: 100%;
      height: 100%;
      display: block;
    }}
    /* Sidebar Details Card */
    .sidebar-panel {{
      width: 290px;
      background: var(--bg-panel);
      border-left: 1px solid var(--border);
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      overflow-y: auto;
      z-index: 10;
    }}
    .panel-title {{
      font-size: 0.95rem;
      font-weight: 700;
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .stat-card {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 10px 12px;
    }}
    .stat-card-title {{
      font-size: 0.7rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      margin-bottom: 4px;
    }}
    .stat-formula {{
      font-family: var(--font-mono);
      font-size: 0.86rem;
      color: var(--cyan);
      font-weight: 600;
    }}
    .stat-param {{
      font-size: 0.78rem;
      color: var(--text-muted);
      margin-top: 4px;
    }}
    .selected-point-box {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}
    .point-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .point-degree {{
      font-size: 1.1rem;
      font-weight: 700;
      font-family: var(--font-mono);
      color: var(--cyan);
    }}
    .point-count {{
      font-size: 0.82rem;
      color: var(--text);
      font-weight: 600;
    }}
    .char-list-title {{
      font-size: 0.7rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--text-muted);
    }}
    .char-chips {{
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
      max-height: 140px;
      overflow-y: auto;
    }}
    .char-chip {{
      background: var(--bg-panel);
      border: 1px solid var(--border);
      font-size: 0.72rem;
      padding: 2px 6px;
      border-radius: 4px;
      color: var(--text);
    }}
    .char-chip.highlight {{
      background: rgba(239, 68, 68, 0.18);
      border-color: #ef4444;
      color: #f87171;
      font-weight: 600;
    }}
    /* Tooltip */
    .plot-tooltip {{
      position: absolute;
      pointer-events: none;
      background: var(--bg-panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 8px 12px;
      font-size: 0.78rem;
      box-shadow: 0 8px 20px rgba(0,0,0,0.35);
      z-index: 30;
      opacity: 0;
      transition: opacity 0.15s ease;
      max-width: 240px;
    }}
    .axis line, .axis path {{
      stroke: var(--border);
    }}
    .axis text {{
      fill: var(--text-muted);
      font-family: var(--font-mono);
      font-size: 11px;
    }}
    .grid line {{
      stroke: var(--grid);
      stroke-dasharray: 2, 3;
    }}
  </style>
</head>
<body>

  <!-- Top Toolbar -->
  <div class="applet-toolbar">
    <div class="toolbar-group">
      <span class="toolbar-label">Plot Axes:</span>
      <div class="btn-segmented">
        <button class="seg-btn active" id="btn-scale-log" title="Logarithmic axes on both X and Y">
          <span>📈</span> Log-Log (k+1 vs N)
        </button>
        <button class="seg-btn" id="btn-scale-lin" title="Standard linear axes">
          <span>📉</span> Linear Scale
        </button>
      </div>
    </div>

    <div class="toolbar-group">
      <span class="toolbar-label">Degree Type:</span>
      <div class="btn-segmented">
        <button class="seg-btn active" id="btn-dist-in" title="In-Degree Distribution">
          ↓ In-Degree (k_in)
        </button>
        <button class="seg-btn" id="btn-dist-out" title="Out-Degree Distribution">
          ↑ Out-Degree (k_out)
        </button>
      </div>
    </div>

    <div class="toolbar-group">
      <span class="toolbar-label">Models:</span>
      <button class="toggle-chip active" id="toggle-fit">
        <span>⚡</span> Power-Law Fit
      </button>
      <button class="toggle-chip active" id="toggle-poisson">
        <span>🎲</span> Poisson (Erdős–Rényi)
      </button>
    </div>
  </div>

  <!-- Main Viewport -->
  <div class="viewport-container">
    <div class="chart-area" id="chart-container">
      <svg class="plot-svg" id="plot-svg"></svg>
      <div class="plot-tooltip" id="tooltip"></div>
    </div>

    <!-- Sidebar Info Panel -->
    <div class="sidebar-panel">
      <div class="panel-title">
        <span>🔬</span> Power Law Analysis
      </div>

      <div class="stat-card">
        <div class="stat-card-title">Power Law Model</div>
        <div class="stat-formula" id="fit-formula">P(k) ∝ (k+1)^-1.22</div>
        <div class="stat-param" id="fit-params">Slope γ = 1.22 · R² = 0.88</div>
      </div>

      <div class="stat-card">
        <div class="stat-card-title">Theoretical Poisson Model</div>
        <div class="stat-formula">P(k) = e^-⟨k⟩ · ⟨k⟩^k / k!</div>
        <div class="stat-param">Mean degree ⟨k⟩ = 5.89</div>
      </div>

      <!-- Selected Point Details -->
      <div class="selected-point-box" id="point-details">
        <div class="point-header">
          <div class="point-degree" id="pt-deg">k_in = 106 (x = 107)</div>
          <div class="point-count" id="pt-count">1 character</div>
        </div>
        <div class="char-list-title">Characters at this degree:</div>
        <div class="char-chips" id="pt-chars">
          <span class="char-chip highlight">Spider-Man</span>
        </div>
      </div>

      <div class="stat-card" style="margin-top:auto;">
        <div class="stat-card-title">Key Observation</div>
        <p style="font-size:0.75rem; color:var(--text-muted); line-height:1.4;">
          <strong>k = 0 has 58 characters</strong>. Plotting <code>k+1</code> on log-log shifts $k=0$ to $x=1$ ($\log_{10} 1 = 0$), preserving all 303 nodes without singularity.
        </p>
      </div>
    </div>
  </div>

  <script>
    // Embedded Data
    const IN_DIST = {in_dist_json};
    const OUT_DIST = {out_dist_json};
    const SUMMARY = {summary_json};

    // State
    let scaleType = 'log'; // 'log', 'linear'
    let distType = 'in'; // 'in', 'out'
    let showFitLine = true;
    let showPoisson = true;
    let selectedPoint = IN_DIST.find(d => d.k === 106) || IN_DIST[IN_DIST.length - 1];

    const container = document.getElementById('chart-container');
    const svg = d3.select('#plot-svg');
    const tooltip = document.getElementById('tooltip');

    const margin = {{ top: 35, right: 35, bottom: 55, left: 65 }};

    function renderPlot() {{
      const width = container.clientWidth || 600;
      const height = container.clientHeight || 450;
      const plotW = width - margin.left - margin.right;
      const plotH = height - margin.top - margin.bottom;

      svg.selectAll('*').remove();

      const g = svg.append('g').attr('transform', `translate(${{margin.left}},${{margin.top}})`);

      const dataset = distType === 'in' ? IN_DIST : OUT_DIST;

      // X Scale: k+1
      let xScale, yScale;

      if (scaleType === 'log') {{
        const maxX = d3.max(dataset, d => d.k_plus_1) * 1.25;
        xScale = d3.scaleLog().domain([1, maxX]).range([0, plotW]).nice();

        const maxY = d3.max(dataset, d => d.count) * 1.35;
        yScale = d3.scaleLog().domain([0.8, maxY]).range([plotH, 0]).nice();
      }} else {{
        const maxX = d3.max(dataset, d => d.k_plus_1) + 5;
        xScale = d3.scaleLinear().domain([0, maxX]).range([0, plotW]).nice();

        const maxY = d3.max(dataset, d => d.count) * 1.1;
        yScale = d3.scaleLinear().domain([0, maxY]).range([plotH, 0]).nice();
      }}

      // Grid Lines
      g.append('g').attr('class', 'grid')
        .attr('transform', `translate(0,${{plotH}})`)
        .call(d3.axisBottom(xScale).ticks(scaleType === 'log' ? 5 : 8).tickSize(-plotH).tickFormat(''));

      g.append('g').attr('class', 'grid')
        .call(d3.axisLeft(yScale).ticks(scaleType === 'log' ? 4 : 8).tickSize(-plotW).tickFormat(''));

      // Axes
      const xAxis = scaleType === 'log' 
        ? d3.axisBottom(xScale).ticks(6, '~s')
        : d3.axisBottom(xScale).ticks(8);

      const yAxis = scaleType === 'log'
        ? d3.axisLeft(yScale).ticks(5, '~s')
        : d3.axisLeft(yScale).ticks(6);

      g.append('g')
        .attr('class', 'axis x-axis')
        .attr('transform', `translate(0,${{plotH}})`)
        .call(xAxis);

      g.append('g')
        .attr('class', 'axis y-axis')
        .call(yAxis);

      // Axis Labels
      g.append('text')
        .attr('x', plotW / 2)
        .attr('y', plotH + 42)
        .attr('text-anchor', 'middle')
        .attr('fill', 'var(--text)')
        .attr('font-size', '12px')
        .attr('font-weight', '600')
        .text(distType === 'in' ? 'Shifted In-Degree: k_in + 1 (log scale)' : 'Shifted Out-Degree: k_out + 1');

      g.append('text')
        .attr('transform', 'rotate(-90)')
        .attr('x', -plotH / 2)
        .attr('y', -45)
        .attr('text-anchor', 'middle')
        .attr('fill', 'var(--text)')
        .attr('font-size', '12px')
        .attr('font-weight', '600')
        .text('Number of Characters N(k)');

      // Linear Regression Fit line
      if (showFitLine) {{
        // Fit on log10(x) and log10(y)
        const logPoints = dataset.map(d => ({{
          lx: Math.log10(d.k_plus_1),
          ly: Math.log10(d.count)
        }}));

        const meanX = d3.mean(logPoints, d => d.lx);
        const meanY = d3.mean(logPoints, d => d.ly);
        const num = d3.sum(logPoints, d => (d.lx - meanX) * (d.ly - meanY));
        const den = d3.sum(logPoints, d => Math.pow(d.lx - meanX, 2));
        const slope = num / den;
        const intercept = meanY - slope * meanX;

        // R^2
        const ssTot = d3.sum(logPoints, d => Math.pow(d.ly - meanY, 2));
        const ssRes = d3.sum(logPoints, d => Math.pow(d.ly - (intercept + slope * d.lx), 2));
        const r2 = 1 - (ssRes / ssTot);

        // Update sidebar
        document.getElementById('fit-formula').textContent = `N(k) ∝ (k+1)^${{slope.toFixed(2)}}`;
        document.getElementById('fit-params').textContent = `Slope γ = ${{Math.abs(slope).toFixed(2)}} · R² = ${{r2.toFixed(2)}}`;

        // Generate line points
        const minXVal = d3.min(dataset, d => d.k_plus_1);
        const maxXVal = d3.max(dataset, d => d.k_plus_1);

        const xSamples = d3.range(minXVal, maxXVal, (maxXVal - minXVal) / 40);
        xSamples.push(maxXVal);

        const fitLineData = xSamples.map(x => {{
          const ly = intercept + slope * Math.log10(x);
          return {{ x: x, y: Math.pow(10, ly) }};
        }}).filter(pt => pt.y >= (scaleType === 'log' ? 0.8 : 0));

        const lineGen = d3.line()
          .x(d => xScale(d.x))
          .y(d => yScale(d.y));

        g.append('path')
          .datum(fitLineData)
          .attr('fill', 'none')
          .attr('stroke', '#6366f1')
          .attr('stroke-width', 2.5)
          .attr('stroke-dasharray', '6, 4')
          .attr('d', lineGen);

        // Label for fit line
        const lastPt = fitLineData[fitLineData.length - 1];
        if (lastPt) {{
          g.append('text')
            .attr('x', xScale(lastPt.x) - 10)
            .attr('y', yScale(lastPt.y) - 10)
            .attr('text-anchor', 'end')
            .attr('fill', '#818cf8')
            .attr('font-size', '10px')
            .attr('font-family', 'var(--font-mono)')
            .attr('font-weight', '600')
            .text(`Power Law Fit (γ = ${{Math.abs(slope).toFixed(2)}})`);
        }}
      }}

      // Theoretical Poisson Curve
      if (showPoisson) {{
        const lambda = distType === 'in' ? SUMMARY.avg_in_degree : SUMMARY.avg_out_degree;
        const totalN = SUMMARY.total_nodes;

        // Compute Poisson for k = 0 to 35
        function factorial(n) {{
          let r = 1;
          for (let i = 2; i <= n; i++) r *= i;
          return r;
        }}

        const poissonPoints = [];
        for (let k = 0; k <= 30; k++) {{
          const p = Math.exp(-lambda) * Math.pow(lambda, k) / factorial(k);
          const expN = totalN * p;
          if (expN >= (scaleType === 'log' ? 0.8 : 0.05)) {{
            poissonPoints.push({{ x: k + 1, y: expN }});
          }}
        }}

        const pLineGen = d3.line()
          .x(d => xScale(d.x))
          .y(d => yScale(d.y))
          .curve(d3.curveMonotoneX);

        g.append('path')
          .datum(poissonPoints)
          .attr('fill', 'none')
          .attr('stroke', '#f59e0b')
          .attr('stroke-width', 2)
          .attr('d', pLineGen);

        // Label
        const peakPt = poissonPoints.reduce((max, p) => p.y > max.y ? p : max, poissonPoints[0]);
        if (peakPt) {{
          g.append('text')
            .attr('x', xScale(peakPt.x))
            .attr('y', yScale(peakPt.y) - 10)
            .attr('text-anchor', 'middle')
            .attr('fill', '#fbbf24')
            .attr('font-size', '10px')
            .attr('font-family', 'var(--font-mono)')
            .attr('font-weight', '600')
            .text('Poisson (Erdős–Rényi)');
        }}
      }}

      // Data Points
      const dots = g.selectAll('.data-dot')
        .data(dataset, d => d.k)
        .join('circle')
        .attr('class', 'data-dot')
        .attr('cx', d => xScale(d.k_plus_1))
        .attr('cy', d => yScale(d.count))
        .attr('r', d => (selectedPoint && d.k === selectedPoint.k) ? 8 : (d.k === 106 ? 7.5 : 5.5))
        .attr('fill', d => {{
          if (d.k === 106) return '#ef4444'; // Spider-Man
          if (selectedPoint && d.k === selectedPoint.k) return 'var(--primary)';
          return 'var(--cyan)';
        }})
        .attr('stroke', '#ffffff')
        .attr('stroke-width', d => (selectedPoint && d.k === selectedPoint.k) ? 2.5 : 1)
        .attr('cursor', 'pointer')
        .on('mouseenter', (event, d) => {{
          showTooltip(event, d);
        }})
        .on('mousemove', (event) => {{
          moveTooltip(event);
        }})
        .on('mouseleave', () => {{
          hideTooltip();
        }})
        .on('click', (event, d) => {{
          selectPoint(d);
        }});

      // Annotations for key points
      const spiderPt = dataset.find(d => d.k === 106);
      if (spiderPt) {{
        g.append('text')
          .attr('x', xScale(spiderPt.k_plus_1) - 10)
          .attr('y', yScale(spiderPt.count) - 10)
          .attr('text-anchor', 'end')
          .attr('fill', '#ef4444')
          .attr('font-size', '11px')
          .attr('font-weight', '700')
          .text('Spider-Man (k=106)');
      }}

      const k0Pt = dataset.find(d => d.k === 0);
      if (k0Pt) {{
        g.append('text')
          .attr('x', xScale(k0Pt.k_plus_1) + 12)
          .attr('y', yScale(k0Pt.count))
          .attr('text-anchor', 'start')
          .attr('fill', 'var(--text-muted)')
          .attr('font-size', '10px')
          .attr('font-family', 'var(--font-mono)')
          .text(`k=0 (${{k0Pt.count}} nodes)`);
      }}
    }}

    function showTooltip(event, d) {{
      tooltip.style.opacity = 1;
      const charSample = d.characters.slice(0, 3).join(', ');
      const more = d.characters.length > 3 ? ` +${{d.characters.length - 3}} more` : '';

      tooltip.innerHTML = `
        <div style="font-weight:700; color:var(--cyan); margin-bottom:4px;">In-Degree k = ${{d.k}} (x = ${{d.k_plus_1}})</div>
        <div style="margin-bottom:4px;"><strong>${{d.count}} character${{d.count > 1 ? 's' : ''}}</strong> (${{(d.count / SUMMARY.total_nodes * 100).toFixed(1)}}%)</div>
        <div style="font-size:0.72rem; color:var(--text-muted);">${{charSample}}${{more}}</div>
      `;
      moveTooltip(event);
    }}

    function moveTooltip(event) {{
      const rect = container.getBoundingClientRect();
      const x = event.clientX - rect.left + 14;
      const y = event.clientY - rect.top - 20;
      tooltip.style.left = `${{x}}px`;
      tooltip.style.top = `${{y}}px`;
    }}

    function hideTooltip() {{
      tooltip.style.opacity = 0;
    }}

    function selectPoint(d) {{
      selectedPoint = d;
      document.getElementById('pt-deg').textContent = `${{distType === 'in' ? 'k_in' : 'k_out'}} = ${{d.k}} (x = ${{d.k_plus_1}})`;
      document.getElementById('pt-count').textContent = `${{d.count}} character${{d.count > 1 ? 's' : ''}} (${{(d.count / SUMMARY.total_nodes * 100).toFixed(1)}}%)`;

      const chipsContainer = document.getElementById('pt-chars');
      chipsContainer.innerHTML = d.characters.map(c => {{
        const isSpidey = c === 'Spider-Man';
        return `<span class="char-chip ${{isSpidey ? 'highlight' : ''}}">${{c}}</span>`;
      }}).join('');

      renderPlot();
    }}

    // Controls
    document.getElementById('btn-scale-log').onclick = function() {{
      scaleType = 'log';
      document.querySelectorAll('#btn-scale-log, #btn-scale-lin').forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      renderPlot();
    }};

    document.getElementById('btn-scale-lin').onclick = function() {{
      scaleType = 'linear';
      document.querySelectorAll('#btn-scale-log, #btn-scale-lin').forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      renderPlot();
    }};

    document.getElementById('btn-dist-in').onclick = function() {{
      distType = 'in';
      document.querySelectorAll('#btn-dist-in, #btn-dist-out').forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      selectedPoint = IN_DIST.find(d => d.k === 106) || IN_DIST[0];
      selectPoint(selectedPoint);
      renderPlot();
    }};

    document.getElementById('btn-dist-out').onclick = function() {{
      distType = 'out';
      document.querySelectorAll('#btn-dist-in, #btn-dist-out').forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      selectedPoint = OUT_DIST[OUT_DIST.length - 1];
      selectPoint(selectedPoint);
      renderPlot();
    }};

    document.getElementById('toggle-fit').onclick = function() {{
      showFitLine = !showFitLine;
      this.classList.toggle('active', showFitLine);
      renderPlot();
    }};

    document.getElementById('toggle-poisson').onclick = function() {{
      showPoisson = !showPoisson;
      this.classList.toggle('active', showPoisson);
      renderPlot();
    }};

    window.addEventListener('resize', () => renderPlot());

    // Theme Sync
    function syncTheme() {{
      try {{
        const parentTheme = window.parent && window.parent.document && window.parent.document.documentElement.getAttribute('data-theme');
        const theme = parentTheme || localStorage.getItem('theme') || 'dark';
        document.documentElement.setAttribute('data-theme', theme);
      }} catch (e) {{
        document.documentElement.setAttribute('data-theme', localStorage.getItem('theme') || 'dark');
      }}
      renderPlot();
    }}
    syncTheme();
    try {{
      if (window.parent && window.parent.document) {{
        const observer = new MutationObserver(() => syncTheme());
        observer.observe(window.parent.document.documentElement, {{ attributes: true, attributeFilter: ['data-theme'] }});
      }}
    }} catch (e) {{}}

    // Init
    selectPoint(selectedPoint);
    renderPlot();
  </script>
</body>
</html>
'''

with open('assets/applets/powerlaw-distribution.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"Successfully created assets/applets/powerlaw-distribution.html ({len(html_content)} bytes)")
