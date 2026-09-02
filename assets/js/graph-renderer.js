/**
 * Universal Graph & Mathematical Plotting Engine
 * Parses Markdown code blocks (```network, ```function-plot, ```plotly, ```mermaid, ```dot)
 * and dynamically converts them into interactive responsive visual widgets.
 */

(function () {
  'use strict';

  // Helper: check if dark mode is active
  function isDarkMode() {
    return document.documentElement.getAttribute('data-theme') === 'dark';
  }

  // Theme palettes
  const LightPalette = {
    bg: '#ffffff',
    text: '#1e293b',
    border: '#e2e8f0',
    grid: '#f1f5f9',
    edge: '#64748b',
    highlight: '#2563eb',
    clusters: ['#2563eb', '#0d9488', '#d97706', '#dc2626', '#7c3aed', '#ec4899', '#0284c7']
  };

  const DarkPalette = {
    bg: '#182234',
    text: '#f1f5f9',
    border: '#334155',
    grid: '#1e293b',
    edge: '#94a3b8',
    highlight: '#60a5fa',
    clusters: ['#60a5fa', '#2dd4bf', '#fbbf24', '#f87171', '#c084fc', '#f472b6', '#38bdf8']
  };

  function getPalette() {
    return isDarkMode() ? DarkPalette : LightPalette;
  }

  // --- 1. RENDER VIS.JS NETWORK GRAPHS ---
  function renderNetworkBlock(block, index) {
    try {
      const rawText = block.textContent.trim();
      let config = {};
      try {
        config = JSON.parse(rawText);
      } catch (e) {
        console.error('Network graph JSON parse error:', e, rawText);
        return;
      }

      const title = config.title || 'Interactive Network Graph';
      const height = config.height || '420px';
      const caption = config.caption || '';
      const physicsEnabled = config.physics !== undefined ? config.physics : true;

      // Create card wrapper
      const card = document.createElement('div');
      card.className = 'graph-card-wrapper';
      card.id = 'network-card-' + index;

      // Header with Title & Toolbar
      const header = document.createElement('div');
      header.className = 'graph-card-header';
      header.innerHTML = `
        <div class="graph-title-group">
          <span class="graph-type-badge network">Network</span>
          <span class="graph-title-text">${title}</span>
        </div>
        <div class="graph-toolbar">
          <button class="graph-tool-btn zoom-in-btn" title="Zoom In">＋</button>
          <button class="graph-tool-btn zoom-out-btn" title="Zoom Out">－</button>
          <button class="graph-tool-btn fit-btn" title="Fit to Screen">↺ Reset</button>
          <button class="graph-tool-btn physics-btn" title="Toggle Physics">${physicsEnabled ? '⏸ Freeze' : '▶ Physics'}</button>
          <button class="graph-tool-btn fullscreen-btn" title="Fullscreen">⛶ Fullscreen</button>
          <button class="graph-tool-btn save-btn" title="Save PNG">💾 Export</button>
        </div>
      `;

      // Canvas Container
      const canvasContainer = document.createElement('div');
      canvasContainer.className = 'graph-canvas-container';
      canvasContainer.style.height = height;

      card.appendChild(header);
      card.appendChild(canvasContainer);

      if (caption) {
        const captionDiv = document.createElement('div');
        captionDiv.className = 'graph-card-caption';
        captionDiv.innerHTML = caption;
        card.appendChild(captionDiv);
      }

      // Replace pre element with card
      block.parentNode.replaceChild(card, block);

      // Process Nodes & Colors
      const palette = getPalette();
      const nodesData = (config.nodes || []).map((node, i) => {
        const n = Object.assign({}, node);
        if (!n.font) {
          n.font = {
            face: 'Inter, sans-serif',
            size: 13,
            color: palette.text
          };
        }
        if (!n.shape) {
          n.shape = 'dot';
        }
        if (!n.size) {
          n.size = 20;
        }
        return n;
      });

      const edgesData = (config.edges || []).map(edge => {
        const e = Object.assign({}, edge);
        if (!e.color) {
          e.color = {
            color: palette.edge,
            highlight: palette.highlight,
            hover: palette.highlight
          };
        }
        if (e.smooth === undefined) {
          e.smooth = { type: 'continuous', roundness: 0.15 };
        }
        return e;
      });

      const data = {
        nodes: new vis.DataSet(nodesData),
        edges: new vis.DataSet(edgesData)
      };

      const options = {
        nodes: {
          borderWidth: 2,
          shadow: true
        },
        edges: {
          width: 1.8,
          shadow: false
        },
        physics: {
          enabled: physicsEnabled,
          solver: 'forceAtlas2Based',
          forceAtlas2Based: {
            gravitationalConstant: -35,
            centralGravity: 0.008,
            springLength: 90,
            springConstant: 0.08,
            damping: 0.85
          },
          stabilization: {
            iterations: 120
          }
        },
        interaction: {
          hover: true,
          tooltipDelay: 100,
          zoomView: true,
          dragView: true,
          navigationButtons: false
        },
        groups: config.groups || {
          default: { color: { background: palette.clusters[0], border: palette.clusters[0] } }
        }
      };

      // Instantiate Network
      const network = new vis.Network(canvasContainer, data, options);

      // Toolbar Handlers
      header.querySelector('.zoom-in-btn').addEventListener('click', () => {
        const scale = network.getScale();
        network.moveTo({ scale: scale * 1.3, animation: true });
      });

      header.querySelector('.zoom-out-btn').addEventListener('click', () => {
        const scale = network.getScale();
        network.moveTo({ scale: scale * 0.7, animation: true });
      });

      header.querySelector('.fit-btn').addEventListener('click', () => {
        network.fit({ animation: { duration: 600, easingFunction: 'easeInOutQuad' } });
      });

      const physicsBtn = header.querySelector('.physics-btn');
      let currentPhysics = physicsEnabled;
      physicsBtn.addEventListener('click', () => {
        currentPhysics = !currentPhysics;
        network.setOptions({ physics: { enabled: currentPhysics } });
        physicsBtn.textContent = currentPhysics ? '⏸ Freeze' : '▶ Physics';
      });

      const fsBtn = header.querySelector('.fullscreen-btn');
      fsBtn.addEventListener('click', () => {
        card.classList.toggle('fullscreen');
        setTimeout(() => network.fit(), 300);
      });

      header.querySelector('.save-btn').addEventListener('click', () => {
        const canvas = canvasContainer.querySelector('canvas');
        if (canvas) {
          const image = canvas.toDataURL('image/png');
          const a = document.createElement('a');
          a.download = (title.toLowerCase().replace(/[^a-z0-9]+/g, '-') || 'network') + '.png';
          a.href = image;
          a.click();
        }
      });

      // Handle Theme Updates
      window.addEventListener('themeChanged', () => {
        const pal = getPalette();
        const updatedNodes = nodesData.map(node => ({
          id: node.id,
          font: { color: pal.text, face: 'Inter, sans-serif', size: 13 }
        }));
        data.nodes.update(updatedNodes);
      });

    } catch (err) {
      console.error('Error rendering network graph:', err);
    }
  }

  // --- 2. RENDER MATHEMATICAL FUNCTION PLOTS ---
  function renderFunctionPlotBlock(block, index) {
    try {
      const rawText = block.textContent.trim();
      let config = {};
      try {
        config = JSON.parse(rawText);
      } catch (e) {
        console.error('Function plot JSON parse error:', e, rawText);
        return;
      }

      const title = config.title || 'Mathematical Function Plot';
      const height = config.height || '380px';
      const caption = config.caption || '';

      const card = document.createElement('div');
      card.className = 'graph-card-wrapper';
      card.id = 'funcplot-card-' + index;

      const header = document.createElement('div');
      header.className = 'graph-card-header';
      header.innerHTML = `
        <div class="graph-title-group">
          <span class="graph-type-badge function">Function Plot</span>
          <span class="graph-title-text">${title}</span>
        </div>
        <div class="graph-toolbar">
          <button class="graph-tool-btn fit-btn" title="Reset View">↺ Reset</button>
          <button class="graph-tool-btn fullscreen-btn" title="Fullscreen">⛶ Fullscreen</button>
        </div>
      `;

      const canvasContainer = document.createElement('div');
      canvasContainer.className = 'graph-canvas-container';
      canvasContainer.id = 'funcplot-canvas-' + index;
      canvasContainer.style.height = height;

      card.appendChild(header);
      card.appendChild(canvasContainer);

      if (caption) {
        const captionDiv = document.createElement('div');
        captionDiv.className = 'graph-card-caption';
        captionDiv.innerHTML = caption;
        card.appendChild(captionDiv);
      }

      block.parentNode.replaceChild(card, block);

      function drawPlot() {
        const width = canvasContainer.clientWidth || 700;
        const h = parseInt(height) || 380;
        const palette = getPalette();

        const plotOptions = {
          target: '#' + canvasContainer.id,
          width: width,
          height: h,
          grid: config.grid !== undefined ? config.grid : true,
          xAxis: config.xAxis || { domain: config.xDomain || [-10, 10] },
          yAxis: config.yAxis || { domain: config.yDomain || [-5, 5] },
          disableZoom: config.disableZoom || false,
          data: config.data || []
        };

        if (typeof functionPlot === 'function') {
          canvasContainer.innerHTML = '';
          const instance = functionPlot(plotOptions);

          header.querySelector('.fit-btn').addEventListener('click', () => {
            drawPlot();
          });
        }
      }

      // Initial Draw
      setTimeout(drawPlot, 100);

      // Handle Resize & Theme Change
      window.addEventListener('resize', drawPlot);
      window.addEventListener('themeChanged', drawPlot);

      header.querySelector('.fullscreen-btn').addEventListener('click', () => {
        card.classList.toggle('fullscreen');
        setTimeout(drawPlot, 250);
      });

    } catch (err) {
      console.error('Error rendering function plot:', err);
    }
  }

  // --- 3. RENDER PLOTLY SCIENTIFIC PLOTS (3D Surfaces, Heatmaps) ---
  function renderPlotlyBlock(block, index) {
    try {
      const rawText = block.textContent.trim();
      let config = {};
      try {
        config = JSON.parse(rawText);
      } catch (e) {
        console.error('Plotly JSON parse error:', e, rawText);
        return;
      }

      const title = config.title || '3D Scientific Visualization';
      const height = config.height || '460px';
      const caption = config.caption || '';

      const card = document.createElement('div');
      card.className = 'graph-card-wrapper';
      card.id = 'plotly-card-' + index;

      const header = document.createElement('div');
      header.className = 'graph-card-header';
      header.innerHTML = `
        <div class="graph-title-group">
          <span class="graph-type-badge plotly">Plotly 3D</span>
          <span class="graph-title-text">${title}</span>
        </div>
        <div class="graph-toolbar">
          <button class="graph-tool-btn fullscreen-btn" title="Fullscreen">⛶ Fullscreen</button>
        </div>
      `;

      const canvasContainer = document.createElement('div');
      canvasContainer.className = 'graph-canvas-container';
      canvasContainer.id = 'plotly-canvas-' + index;
      canvasContainer.style.height = height;

      card.appendChild(header);
      card.appendChild(canvasContainer);

      if (caption) {
        const captionDiv = document.createElement('div');
        captionDiv.className = 'graph-card-caption';
        captionDiv.innerHTML = caption;
        card.appendChild(captionDiv);
      }

      block.parentNode.replaceChild(card, block);

      function drawPlotly() {
        const palette = getPalette();

        // Check if user provided simplified mathematical surface formula
        let plotData = config.data;
        if (config.type === 'surface' && config.fn) {
          const xMin = config.xRange ? config.xRange[0] : -3;
          const xMax = config.xRange ? config.xRange[1] : 3;
          const xSteps = config.xRange ? config.xRange[2] : 30;

          const yMin = config.yRange ? config.yRange[0] : -3;
          const yMax = config.yRange ? config.yRange[1] : 3;
          const ySteps = config.yRange ? config.yRange[2] : 30;

          const x = [];
          const y = [];
          const z = [];

          const fnCompiled = new Function('x', 'y', 'return ' + config.fn);

          for (let i = 0; i <= xSteps; i++) {
            x.push(xMin + (i / xSteps) * (xMax - xMin));
          }
          for (let j = 0; j <= ySteps; j++) {
            y.push(yMin + (j / ySteps) * (yMax - yMin));
          }
          for (let j = 0; j <= ySteps; j++) {
            const row = [];
            for (let i = 0; i <= xSteps; i++) {
              row.push(fnCompiled(x[i], y[j]));
            }
            z.push(row);
          }

          plotData = [{
            type: 'surface',
            x: x,
            y: y,
            z: z,
            colorscale: config.colorscale || 'Viridis',
            showscale: true
          }];
        }

        const layout = Object.assign({
          autosize: true,
          margin: { l: 20, r: 20, b: 20, t: 30 },
          paper_bgcolor: palette.bg,
          plot_bgcolor: palette.bg,
          font: { family: 'Inter, sans-serif', color: palette.text },
          scene: {
            xaxis: { gridcolor: palette.border, zerolinecolor: palette.border },
            yaxis: { gridcolor: palette.border, zerolinecolor: palette.border },
            zaxis: { gridcolor: palette.border, zerolinecolor: palette.border }
          }
        }, config.layout || {});

        if (typeof Plotly !== 'undefined') {
          Plotly.newPlot(canvasContainer.id, plotData, layout, { responsive: true, displayModeBar: true });
        }
      }

      setTimeout(drawPlotly, 100);
      window.addEventListener('resize', drawPlotly);
      window.addEventListener('themeChanged', drawPlotly);

      header.querySelector('.fullscreen-btn').addEventListener('click', () => {
        card.classList.toggle('fullscreen');
        setTimeout(drawPlotly, 250);
      });

    } catch (err) {
      console.error('Error rendering Plotly block:', err);
    }
  }

  // --- 4. RENDER MERMAID DIAGRAMS ---
  function renderMermaidBlocks() {
    if (typeof mermaid !== 'undefined') {
      mermaid.initialize({
        startOnLoad: false,
        theme: isDarkMode() ? 'dark' : 'default',
        securityLevel: 'loose'
      });
      document.querySelectorAll('pre code.language-mermaid').forEach(el => {
        const pre = el.closest('pre');
        const code = el.textContent;
        const div = document.createElement('div');
        div.className = 'mermaid';
        div.textContent = code;
        pre.parentNode.replaceChild(div, pre);
      });
      mermaid.run();
    }
  }

  // --- 5. RENDER GRAPHVIZ (DOT) DIAGRAMS ---
  function renderDotBlocks() {
    if (window['@hpcc-js/wasm']) {
      window['@hpcc-js/wasm'].Graphviz.load().then(graphviz => {
        document.querySelectorAll('pre code.language-dot, pre code.language-graphviz').forEach(el => {
          const pre = el.closest('pre');
          const dotSrc = el.textContent;
          try {
            const svg = graphviz.dot(dotSrc);
            const div = document.createElement('div');
            div.className = 'graphviz-container';
            div.style.textAlign = 'center';
            div.style.margin = '1.5rem 0';
            div.innerHTML = svg;
            pre.parentNode.replaceChild(div, pre);
          } catch (e) {
            console.error('Graphviz rendering error:', e);
          }
        });
      });
    }
  }

  // --- Scan and initialize all graphs on DOMContentLoaded ---
  document.addEventListener('DOMContentLoaded', function () {
    // 1. Vis.js Networks
    const networkBlocks = document.querySelectorAll('pre code.language-network, pre code.language-network-graph');
    networkBlocks.forEach((codeEl, i) => {
      renderNetworkBlock(codeEl.closest('pre'), i);
    });

    // Also scan any divs with class network-graph-block
    document.querySelectorAll('.network-graph-block pre').forEach((pre, i) => {
      renderNetworkBlock(pre, i + 100);
    });

    // 2. Mathematical Function Plots
    const funcBlocks = document.querySelectorAll('pre code.language-function-plot, pre code.language-math-plot');
    funcBlocks.forEach((codeEl, i) => {
      renderFunctionPlotBlock(codeEl.closest('pre'), i);
    });

    // 3. Plotly 3D & Advanced Plots
    const plotlyBlocks = document.querySelectorAll('pre code.language-plotly');
    plotlyBlocks.forEach((codeEl, i) => {
      renderPlotlyBlock(codeEl.closest('pre'), i);
    });

    // 4. Mermaid
    renderMermaidBlocks();

    // 5. Graphviz DOT
    renderDotBlocks();
  });
})();
