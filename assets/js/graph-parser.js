/**
 * Graph Parser & Markdown Block Enhancer
 * Converts ```graph and ```network blocks into interactive D3 network graphs
 */

class GraphParser {
  /**
   * Parse human-friendly text-based network DSL
   * Example:
   * NodeA -> NodeB : directed relation
   * NodeA -- NodeC : undirected connection
   * [Graph Laplacian] -> [Spectral Clustering] : eigenvalue decomposition
   * NodeA { group: "math", size: 14 }
   */
  static parseDSL(text) {
    const lines = text.split('
');
    const nodesMap = new Map();
    const links = [];

    const getOrCreateNode = (rawId, overrides = {}) => {
      let cleanId = rawId.trim();
      let label = cleanId;

      // Check bracket syntax [My Node Label]
      if (cleanId.startsWith('[') && cleanId.endsWith(']')) {
        cleanId = cleanId.slice(1, -1).trim();
        label = cleanId;
      }

      if (!nodesMap.has(cleanId)) {
        nodesMap.set(cleanId, {
          id: cleanId,
          label: label,
          group: 'concept',
          size: 8,
          ...overrides
        });
      } else if (Object.keys(overrides).length > 0) {
        const existing = nodesMap.get(cleanId);
        nodesMap.set(cleanId, { ...existing, ...overrides });
      }
      return nodesMap.get(cleanId);
    };

    lines.forEach(line => {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#') || trimmed.startsWith('//')) return;

      // 1. Check for node attributes definition: NodeA { group: 'math', size: 12 }
      const attrMatch = trimmed.match(/^([^\{]+)\{([^\}]+)\}$/);
      if (attrMatch) {
        const nodeId = attrMatch[1].trim();
        const rawAttrs = attrMatch[2];
        const attrs = {};
        rawAttrs.split(',').forEach(kv => {
          const [k, v] = kv.split(':').map(s => s.trim().replace(/['"]/g, ''));
          if (k && v) {
            attrs[k] = isNaN(Number(v)) ? v : Number(v);
          }
        });
        getOrCreateNode(nodeId, attrs);
        return;
      }

      // 2. Check for link definitions: A -> B : label OR A -- B : label
      const directedMatch = trimmed.match(/(.+?)(->|--)(.+)/);
      if (directedMatch) {
        const sourceStr = directedMatch[1].trim();
        const op = directedMatch[2];
        let targetAndLabel = directedMatch[3].trim();
        let targetStr = targetAndLabel;
        let label = '';

        if (targetAndLabel.includes(':')) {
          const parts = targetAndLabel.split(':');
          targetStr = parts[0].trim();
          label = parts.slice(1).join(':').trim();
        }

        const sourceNode = getOrCreateNode(sourceStr);
        const targetNode = getOrCreateNode(targetStr);

        links.push({
          source: sourceNode.id,
          target: targetNode.id,
          label: label || undefined,
          directed: op === '->',
          weight: 1.5
        });
        return;
      }

      // 3. Standalone node
      getOrCreateNode(trimmed);
    });

    return {
      nodes: Array.from(nodesMap.values()),
      links: links
    };
  }

  /**
   * Parse JSON graph definition
   */
  static parseJSON(jsonStr) {
    try {
      const data = JSON.parse(jsonStr);
      return {
        nodes: data.nodes || [],
        links: data.links || data.edges || []
      };
    } catch (e) {
      console.error('Failed to parse graph JSON:', e);
      return null;
    }
  }

  /**
   * Create interactive graph DOM component with full toolbar
   */
  static mountGraph(containerElement, graphData, options = {}) {
    const graphId = 'graph-' + Math.random().toString(36).substring(2, 9);
    
    containerElement.innerHTML = `
      <div class="embedded-graph-header">
        <div class="graph-title">
          <span class="graph-badge">Network Graph</span>
          <span>${options.title || 'Interactive View'}</span>
        </div>
        <div class="graph-toolbar">
          <button class="graph-btn" data-action="layout" title="Cycle Layout (Force / Circle / Tree)">🔄</button>
          <button class="graph-btn" data-action="physics" title="Toggle Physics Simulation">⚡</button>
          <button class="graph-btn" data-action="particles" title="Toggle Diffusion Particles">✨</button>
          <button class="graph-btn" data-action="labels" title="Toggle Labels">🏷</button>
          <button class="graph-btn" data-action="zoom-in" title="Zoom In">+</button>
          <button class="graph-btn" data-action="zoom-out" title="Zoom Out">−</button>
          <button class="graph-btn" data-action="fit" title="Fit to Screen">⊙</button>
          <button class="graph-btn" data-action="export" title="Export PNG Image">📷</button>
          <button class="graph-btn" data-action="fullscreen" title="Toggle Fullscreen">⛶</button>
        </div>
      </div>
      <div class="graph-viewport" id="${graphId}"></div>
      ${options.caption ? `<div class="graph-caption"><span>${options.caption}</span><span>${graphData.nodes.length} nodes · ${graphData.links.length} edges</span></div>` : ''}
    `;

    const viewport = containerElement.querySelector(`#${graphId}`);
    const graph = new NetworkGraph(viewport, {
      layout: options.layout || 'force',
      enableParticles: options.enableParticles || false,
      showLabels: true,
      ...options
    });

    graph.setData(graphData);

    // Wire up toolbar buttons
    const toolbar = containerElement.querySelector('.graph-toolbar');
    
    toolbar.querySelector('[data-action="zoom-in"]').onclick = () => graph.zoomIn();
    toolbar.querySelector('[data-action="zoom-out"]').onclick = () => graph.zoomOut();
    toolbar.querySelector('[data-action="fit"]').onclick = () => graph.fitToViewport();
    
    const physicsBtn = toolbar.querySelector('[data-action="physics"]');
    physicsBtn.onclick = () => {
      const running = graph.togglePhysics();
      physicsBtn.classList.toggle('active', running);
    };

    const particleBtn = toolbar.querySelector('[data-action="particles"]');
    particleBtn.onclick = () => {
      const on = graph.toggleParticles();
      particleBtn.classList.toggle('active', on);
    };

    const labelsBtn = toolbar.querySelector('[data-action="labels"]');
    labelsBtn.onclick = () => {
      const visible = graph.toggleLabels();
      labelsBtn.classList.toggle('active', visible);
    };

    const layouts = ['force', 'circular', 'concentric', 'tree'];
    let currentLayoutIdx = layouts.indexOf(options.layout || 'force');
    toolbar.querySelector('[data-action="layout"]').onclick = () => {
      currentLayoutIdx = (currentLayoutIdx + 1) % layouts.length;
      const nextLayout = layouts[currentLayoutIdx];
      graph.applyLayout(nextLayout);
    };

    toolbar.querySelector('[data-action="export"]').onclick = () => {
      graph.exportImage((options.title || 'graph').toLowerCase().replace(/\s+/g, '-') + '.png');
    };

    const fsBtn = toolbar.querySelector('[data-action="fullscreen"]');
    fsBtn.onclick = () => {
      if (!document.fullscreenElement) {
        containerElement.requestFullscreen().catch(err => console.error(err));
      } else {
        document.exitFullscreen();
      }
    };

    return graph;
  }
}

window.GraphParser = GraphParser;
