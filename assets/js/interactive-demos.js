/**
 * Interactive Academic Demos:
 * Real-time Heat Diffusion on Graphs and Random Walk Simulation
 */

window.initDiffusionDemo = function (containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;

  // Graph Definition: Zachary Karate Club / Community network
  const numNodes = 14;
  const nodes = [];
  const edges = [
    { from: 1, to: 2 }, { from: 1, to: 3 }, { from: 1, to: 4 }, { from: 2, to: 3 }, { from: 3, to: 4 },
    { from: 4, to: 5 }, { from: 5, to: 6 }, { from: 6, to: 7 }, { from: 7, to: 8 }, { from: 7, to: 9 },
    { from: 8, to: 9 }, { from: 9, to: 10 }, { from: 10, to: 11 }, { from: 11, to: 12 }, { from: 12, to: 13 },
    { from: 13, to: 14 }, { from: 11, to: 14 }, { from: 1, to: 6 }, { from: 6, to: 11 }
  ];

  // Adjacency and Laplacian Matrix construction
  const A = Array.from({ length: numNodes }, () => Array(numNodes).fill(0));
  const deg = Array(numNodes).fill(0);

  edges.forEach(e => {
    const u = e.from - 1;
    const v = e.to - 1;
    A[u][v] = 1;
    A[v][u] = 1;
    deg[u]++;
    deg[v]++;
  });

  const L = Array.from({ length: numNodes }, () => Array(numNodes).fill(0));
  for (let i = 0; i < numNodes; i++) {
    for (let j = 0; j < numNodes; j++) {
      if (i === j) {
        L[i][j] = deg[i];
      } else if (A[i][j] === 1) {
        L[i][j] = -1;
      }
    }
  }

  // State: Heat vector x(t)
  let x = Array(numNodes).fill(0.0);
  x[0] = 1.0; // Initial heat source at node 1

  for (let i = 1; i <= numNodes; i++) {
    nodes.push({
      id: i,
      label: 'Node ' + i,
      size: 22,
      font: { color: '#ffffff', size: 12, face: 'Inter' },
      color: { background: '#2563eb', border: '#1e3a8a' },
      title: 'Click to inject heat!'
    });
  }

  const nodesDataSet = new vis.DataSet(nodes);
  const edgesDataSet = new vis.DataSet(edges.map(e => ({ from: e.from, to: e.to, width: 2, color: '#94a3b8' })));

  // Setup UI Controls
  container.innerHTML = `
    <div class="graph-card-wrapper">
      <div class="graph-card-header">
        <div class="graph-title-group">
          <span class="graph-type-badge network">Interactive Simulation</span>
          <span class="graph-title-text">Discrete Graph Heat Diffusion: $\\frac{d\\mathbf{x}}{dt} = -\\mathcal{L}\\mathbf{x}$</span>
        </div>
        <div class="graph-toolbar">
          <button class="graph-tool-btn play-sim-btn">▶ Start Diffusion</button>
          <button class="graph-tool-btn reset-sim-btn">↺ Reset Heat</button>
        </div>
      </div>
      <div class="sim-controls-panel">
        <div class="sim-slider-group">
          <label><strong>Diffusion Rate (γ):</strong></label>
          <input type="range" class="gamma-slider" min="0.01" max="0.5" step="0.01" value="0.12">
          <span class="gamma-val">0.12</span>
        </div>
        <div style="margin-left:auto; font-size:0.85rem; color:var(--text-muted);">
          👉 <em>Click any node on the graph to inject thermal energy!</em>
        </div>
      </div>
      <div class="graph-canvas-container" style="height: 400px;"></div>
      <div class="graph-card-caption">
        Heat distribution $\\mathbf{x}(t)$ represented by colormap (Blue = Cold, Orange/Red = High Temperature). Energy dissipates across edges following discrete graph Laplacian operator.
      </div>
    </div>
  `;

  const canvasEl = container.querySelector('.graph-canvas-container');
  const network = new vis.Network(canvasEl, { nodes: nodesDataSet, edges: edgesDataSet }, {
    physics: { solver: 'forceAtlas2Based', forceAtlas2Based: { gravitationalConstant: -40, springLength: 80 } },
    interaction: { hover: true }
  });

  // Color mapper (0 -> blue, 1 -> red)
  function getHeatColor(val) {
    val = Math.max(0, Math.min(1, val));
    const r = Math.round(37 + val * (239 - 37));
    const g = Math.round(99 + val * (68 - 99));
    const b = Math.round(235 + val * (68 - 235));
    return `rgb(${r}, ${g}, ${b})`;
  }

  function updateVisuals() {
    const maxVal = Math.max(...x, 0.001);
    const updates = [];
    for (let i = 0; i < numNodes; i++) {
      const norm = x[i] / maxVal;
      updates.push({
        id: i + 1,
        color: { background: getHeatColor(norm), border: '#0f172a' },
        title: `Temp: ${x[i].toFixed(3)} (Normalized: ${(norm * 100).toFixed(1)}%)`
      });
    }
    nodesDataSet.update(updates);
  }

  updateVisuals();

  let isRunning = false;
  let animId = null;
  let gamma = 0.12;

  const playBtn = container.querySelector('.play-sim-btn');
  const resetBtn = container.querySelector('.reset-sim-btn');
  const gammaSlider = container.querySelector('.gamma-slider');
  const gammaValSpan = container.querySelector('.gamma-val');

  gammaSlider.addEventListener('input', e => {
    gamma = parseFloat(e.target.value);
    gammaValSpan.textContent = gamma.toFixed(2);
  });

  function stepDiffusion() {
    const dt = 0.05;
    const dx = Array(numNodes).fill(0);

    // dx/dt = -gamma * L * x
    for (let i = 0; i < numNodes; i++) {
      let sum = 0;
      for (let j = 0; j < numNodes; j++) {
        sum += L[i][j] * x[j];
      }
      dx[i] = -gamma * sum;
    }

    for (let i = 0; i < numNodes; i++) {
      x[i] = Math.max(0, x[i] + dx[i] * dt);
    }

    updateVisuals();

    if (isRunning) {
      animId = requestAnimationFrame(stepDiffusion);
    }
  }

  playBtn.addEventListener('click', () => {
    isRunning = !isRunning;
    playBtn.textContent = isRunning ? '⏸ Pause Diffusion' : '▶ Resume Diffusion';
    if (isRunning) {
      stepDiffusion();
    }
  });

  resetBtn.addEventListener('click', () => {
    x = Array(numNodes).fill(0.0);
    x[0] = 1.0;
    updateVisuals();
  });

  network.on('click', params => {
    if (params.nodes.length > 0) {
      const clickedId = params.nodes[0] - 1;
      x[clickedId] += 1.0; // Inject heat
      updateVisuals();
    }
  });
};

// Auto initialize any diffusion simulation containers
document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('laplacian-diffusion-sim')) {
    window.initDiffusionDemo('laplacian-diffusion-sim');
  }
});
