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
    const lines = text.split('\n');
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
   * Parse a tab-separated node or edge dataset.
   */
  static parseTSV(text, kind) {
    const lines = text.split(/\r?\n/).filter(line => line.trim());
    const headerIndex = lines.findIndex(line => {
      const headers = line.replace(/^#\s*/, '').split('\t');
      return kind === 'nodes' ? headers.includes('node_id') : headers.includes('source');
    });
    if (headerIndex < 0) return { nodes: [], links: [] };

    const headers = lines[headerIndex].replace(/^#\s*/, '').split('\t');
    const dataLines = lines.slice(headerIndex + 1).filter(line => !line.trim().startsWith('#'));
    const rows = dataLines.map(line => {
      const values = line.split('\t');
      return headers.reduce((row, header, index) => {
        row[header] = values[index] || '';
        return row;
      }, {});
    });

    if (kind === 'nodes') {
      return {
        nodes: rows.map(row => ({
          id: row.node_id,
          label: row.name || row.node_id,
          group: 'marvel-character',
          size: 7,
          description: row.description || '',
          wikidataId: row.wikidata_id || '',
          url: row.url || ''
        })),
        links: []
      };
    }

    return {
      nodes: [],
      links: rows.map(row => ({
        source: row.source,
        target: row.target,
        directed: true,
        weight: 1
      }))
    };
  }

  /**
   * Render a static, deterministic SVG diagram of a graph.
   * No physics, no toolbar, no interaction — just a clean fixed picture.
   */
  static mountSVG(containerElement, graphData, options = {}) {
    const graphId = 'static-graph-' + Math.random().toString(36).substring(2, 9);
    const nodes = graphData.nodes || [];
    const links = graphData.links || [];

    if (!nodes.length) {
      containerElement.innerHTML = '<p class="graph-empty">No nodes to render.</p>';
      return;
    }

    // Degree (in + out) per node
    const degree = new Map(nodes.map(n => [n.id, 0]));
    links.forEach(l => {
      if (degree.has(l.source)) degree.set(l.source, degree.get(l.source) + 1);
      if (degree.has(l.target)) degree.set(l.target, degree.get(l.target) + 1);
    });
    const inDeg = new Map(nodes.map(n => [n.id, 0]));
    links.forEach(l => {
      if (inDeg.has(l.target)) inDeg.set(l.target, inDeg.get(l.target) + 1);
    });

    // Root = most-connected node (ties broken alphabetically)
    let rootId = null, maxD = -1, rootKey = '';
    nodes.forEach(n => {
      const d = degree.get(n.id) || 0;
      const key = (n.label || n.id);
      if (d > maxD || (d === maxD && key < rootKey)) {
        maxD = d;
        rootId = n.id;
        rootKey = key;
      }
    });

    // BFS rings from the root -> deterministic radial layout
    const ring = new Map([[rootId, 0]]);
    const queue = [rootId];
    const idSet = new Set(nodes.map(n => n.id));
    while (queue.length) {
      const id = queue.shift();
      const depth = ring.get(id);
      links.forEach(l => {
        const other = l.source === id ? l.target : (l.target === id ? l.source : null);
        if (other != null && !ring.has(other) && idSet.has(other)) {
          ring.set(other, depth + 1);
          queue.push(other);
        }
      });
    }
    nodes.forEach(n => { if (!ring.has(n.id)) ring.set(n.id, Math.min(6, Math.max(...ring.values()) + 1)); });

    const pos = new Map();
    const byRing = new Map();
    nodes.forEach(n => {
      const d = ring.get(n.id);
      if (!byRing.has(d)) byRing.set(d, []);
      byRing.get(d).push(n);
    });
    const ringGap = 78;
    byRing.forEach((group, depth) => {
      if (depth === 0) {
        group.forEach(n => pos.set(n.id, { x: 0, y: 0 }));
        return;
      }
      group.forEach((n, i) => {
        const angle = -Math.PI / 2 + (2 * Math.PI * i) / group.length;
        const r = depth * ringGap;
        pos.set(n.id, { x: r * Math.cos(angle), y: r * Math.sin(angle) });
      });
    });

    // Node radius + colour derived from size and in-degree
    const radOf = n => Math.max(6, 5 + 2.3 * Math.sqrt(n.size || 8));
    const maxIn = Math.max(1, ...nodes.map(n => inDeg.get(n.id) || 0));
    const colorOf = n => {
      const d = inDeg.get(n.id) || 0;
      if ((degree.get(n.id) || 0) === 0) return '#94a3b8';
      const t = Math.sqrt(d / maxIn);
      const hue = 217 - 195 * t; // deep blue hub -> red
      return `hsl(${hue}, 55%, 55%)`;
    };

    const lineEnd = (sx, sy, ex, ey, rs, rt) => {
      const dx = ex - sx, dy = ey - sy;
      const len = Math.hypot(dx, dy) || 1;
      const ux = dx / len, uy = dy / len;
      return {
        x1: sx + ux * rs,
        y1: sy + uy * rs,
        x2: ex - ux * rt,
        y2: ey - uy * rt
      };
    };

    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    const placed = nodes.map(n => {
      const p = pos.get(n.id);
      const rad = radOf(n);
      minX = Math.min(minX, p.x - rad);
      maxX = Math.max(maxX, p.x + rad);
      minY = Math.min(minY, p.y - rad);
      maxY = Math.max(maxY, p.y + rad + 18);
      return { n, p, rad };
    });
    const PAD = 72;
    const vw = maxX - minX + PAD * 2;
    const vh = maxY - minY + PAD * 2;

    const edgeParts = [];
    links.forEach(l => {
      const s = pos.get(l.source), t = pos.get(l.target);
      if (!s || !t) return;
      const rS = radOf(nodes.find(n => n.id === l.source) || {});
      const rT = radOf(nodes.find(n => n.id === l.target) || {});
      const seg = lineEnd(s.x, s.y, t.x, t.y, rS, rT);
      edgeParts.push({ seg, link: l, mx: (seg.x1 + seg.x2) / 2, my: (seg.y1 + seg.y2) / 2 });
    });

    const edges = edgeParts.map(({ seg, link }) => {
      let marker = '';
      if (link.directed !== false) marker = ` marker-end="url(#${graphId}-arr)"`;
      const extra = link.label ? `<text x="${seg.x1}" y="${seg.y1}" dy="-12" text-anchor="middle" class="sg-elabel">${escapeXml(link.label)}</text>` : '';
      return `<line x1="${seg.x1}" y1="${seg.y1}" x2="${seg.x2}" y2="${seg.y2}" ${marker}/>${extra}`;
    }).join('');

    const circles = placed.map(({ n, p, rad }) => {
      const dIn = inDeg.get(n.id) || 0;
      const dOut = (degree.get(n.id) || 0) - dIn;
      return `<g>
        <circle cx="${p.x}" cy="${p.y}" r="${rad}" fill="${colorOf(n)}" stroke="rgba(10,14,18,0.55)" stroke-width="2">
          <title>${escapeXml(n.label || n.id)} — in ${dIn} · out ${dOut}</title>
        </circle>
        <text x="${p.x}" y="${p.y + rad + 13}" text-anchor="middle" class="sg-label">${escapeXml(n.label || n.id)}</text>
      </g>`;
    }).join('');

    const svg = `<svg class="static-graph-svg" viewBox="${minX - PAD} ${minY - PAD} ${vw} ${vh}" role="img" aria-label="${escapeXml(options.title || 'Network diagram')}">
      <defs>
        <marker id="${graphId}-arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#8a94a6"/>
        </marker>
      </defs>
      <g class="sg-edges">${edges}</g>
      <g class="sg-nodes">${circles}</g>
    </svg>`;

    containerElement.innerHTML = `
      <div class="embedded-graph-header">
        <div>
          <span class="graph-badge">Network Diagram</span>
          <span class="graph-title-text">${escapeXml(options.title || '')}</span>
        </div>
        <span class="graph-caption-count">${nodes.length} nodes · ${links.length} edges</span>
      </div>
      <div class="static-graph">${svg}</div>
    `;
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
          <button class="graph-btn graph-btn-text" data-action="layout" title="Cycle Layout (Force / A-Z Circle / Degree Circle)">Lay</button>
          <button class="graph-btn graph-btn-text" data-action="physics" title="Toggle Physics Simulation">Phy</button>
          <button class="graph-btn graph-btn-text" data-action="particles" title="Toggle Diffusion Particles">Dot</button>
          <button class="graph-btn graph-btn-text" data-action="labels" title="Toggle Labels">Tag</button>
          <button class="graph-btn" data-action="zoom-in" title="Zoom In">+</button>
          <button class="graph-btn" data-action="zoom-out" title="Zoom Out">-</button>
          <button class="graph-btn" data-action="fit" title="Fit to Screen">Fit</button>
          <button class="graph-btn graph-btn-text" data-action="export" title="Export PNG Image">PNG</button>
          <button class="graph-btn graph-btn-text" data-action="fullscreen" title="Toggle Fullscreen">Full</button>
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

    const layouts = ['force', 'circle-alpha', 'circle-degree'];
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

function escapeXml(str) {
  return String(str == null ? '' : str)
    .replace(/[&<>"']/g, ch => (
      { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]
    ));
}
