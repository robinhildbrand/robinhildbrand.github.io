/**
 * Interactive Network Graph Engine using D3.js (Canvas & SVG)
 * High-performance, physics-enabled, multi-layout network visualizer
 */

class NetworkGraph {
  constructor(container, options = {}) {
    this.container = typeof container === 'string' ? document.querySelector(container) : container;
    if (!this.container) {
      console.warn('NetworkGraph: container not found', container);
      return;
    }

    this.options = {
      width: options.width || this.container.clientWidth || 600,
      height: options.height || this.container.clientHeight || 400,
      layout: options.layout || 'force', // 'force', 'circle-alpha', 'circle-degree'
      nodeRadius: options.nodeRadius || 7,
      nodeColor: options.nodeColor || '#6366f1',
      linkColor: options.linkColor || '#475569',
      highlightColor: options.highlightColor || '#38bdf8',
      showLabels: options.showLabels !== undefined ? options.showLabels : false,
      enableParticles: options.enableParticles || false,
      chargeStrength: options.chargeStrength !== undefined ? options.chargeStrength : -400,
      linkDistance: options.linkDistance !== undefined ? options.linkDistance : 200,
      collisionRadius: options.collisionRadius || 24,
      onNodeClick: options.onNodeClick || null,
      onNodeHover: options.onNodeHover || null,
      onPathTraceComplete: options.onPathTraceComplete || null,
      theme: options.theme || (document.documentElement.getAttribute('data-theme') || 'dark'),
      ...options
    };

    this.data = { nodes: [], links: [] };
    this.particles = [];
    this.simulation = null;
    this.transform = { k: 1, x: 0, y: 0 };
    this.cameraTween = null;      // {from:{k,x,y}, to:{k,x,y}, start, duration}
    this.cameraTweenAnimId = null;
    this.hoveredNode = null;
    this.selectedNode = null;
    this.animFrameId = null;
    this.isPhysicsRunning = true;

    // Path tracer state
    this.adj = new Map();
    this.pathTrace = null; // { path, nodeIndex, phase, activeEdges, otherEdges, currentNodeId }
    this.pathTraceAnimId = null;
    this.pathTraceRunId = 0; // bumped to cancel any in-flight fly-through
    this.pathTrail = []; // [{from, to}] visited edges for persistent trail
    this.pathTrailClearTimer = null;

    console.debug('[graph-engine] v19 loaded — manual camera, fly-through trace, autoreset');
    this.init();
  }

  init() {
    // Remove ONLY the engine-owned children (canvas + its overlays) so the
    // page's own UI (HUD controls, legend, node inspector, search) survives.
    this.container.querySelectorAll(
      ':scope > .network-graph-canvas, :scope > .graph-tooltip, :scope > .graph-path-info'
    ).forEach(el => el.remove());
    
    // Canvas setup with HiDPI support
    this.canvas = document.createElement('canvas');
    this.canvas.className = 'network-graph-canvas';
    this.container.appendChild(this.canvas);
    this.ctx = this.canvas.getContext('2d');

    // Tooltip setup
    this.tooltip = document.createElement('div');
    this.tooltip.className = 'graph-tooltip';
    this.container.appendChild(this.tooltip);

    // Path trace info overlay (status + tags of the traversed path)
    this.pathTraceInfoEl = document.createElement('div');
    this.pathTraceInfoEl.className = 'graph-path-info';
    this.pathTraceInfoEl.style.display = 'none';
    this.container.appendChild(this.pathTraceInfoEl);

    this.updateDimensions();

    // NOTE: camera is fully manual (this.transform = {k, x, y}); no d3.zoom.
    // Wheel/pinch zoom and drag-pan are implemented in setupInteraction. A
    // self-owned transform guarantees the ball and the fit are always exact.

    // Event listeners
    this.setupInteraction();

    // Resize observer (debounced)
    let resizeTimer = null;
    this.resizeObserver = new ResizeObserver(() => {
      if (resizeTimer) clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => {
        this.updateDimensions();
        this.render();
      }, 100);
    });
    this.resizeObserver.observe(this.container);
  }

  updateDimensions() {
    const rect = this.container.getBoundingClientRect();
    this.width = rect.width || this.options.width || 600;
    this.height = rect.height || this.options.height || 400;

    const dpr = window.devicePixelRatio || 1;
    this.canvas.width = this.width * dpr;
    this.canvas.height = this.height * dpr;
    this.canvas.style.width = `${this.width}px`;
    this.canvas.style.height = `${this.height}px`;
    // Explicitly reset the transform to CSS-pixel space; render() re-applies
    // the DPR scale itself each frame so no state can leak between frames.
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    // Keep isolated-node panel anchored to the (new) corner
    this.repositionIsolatedPanel();
  }

  repositionIsolatedPanel() {
    // Camera-aware anchor: the panel rect is computed in SCREEN space (so it
    // always sits in the bottom-right corner of the viewport), then un-projected
    // into world coordinates via the current transform. Nodes stay visually
    // welded to the corner no matter how the user zooms, pans, flies, or refits.
    const isolatedNodes = this.data.nodes.filter(n => n.isolated);
    if (!isolatedNodes.length) {
      this.isolatedPanel = null;
      return;
    }
    const margin = 24;
    const cols = Math.max(4, Math.ceil(Math.sqrt(isolatedNodes.length)));
    const cellW = 84, cellH = 48, pad = 16;
    const rows = Math.ceil(isolatedNodes.length / cols);
    const panelW = cols * cellW + pad * 2;
    const panelH = rows * cellH + pad * 2 + 16;
    const panelX = this.width - panelW - margin;
    const panelY = this.height - panelH - margin;
    this.isolatedPanel = { x: panelX, y: panelY, w: panelW, h: panelH, count: isolatedNodes.length };
    const k = this.transform.k || 1;
    const tx = this.transform.x || 0;
    const ty = this.transform.y || 0;
    isolatedNodes.forEach((node, i) => {
      const col = i % cols;
      const row = Math.floor(i / cols);
      const bx = panelX + pad + col * cellW + cellW / 2;
      const by = panelY + pad + 16 + row * cellH + cellH / 2;
      const wx = (bx - tx) / k;
      const wy = (by - ty) / k;
      node.fx = wx; node.fy = wy; node.x = wx; node.y = wy;
      node._isolatedPanel = true;
    });
  }

  setData(data) {
    // Deep clone data to avoid mutation issues
    const nodes = (data.nodes || []).map(d => ({ ...d }));
    const links = (data.links || []).map(d => ({ ...d }));

    // Node lookup map
    const nodeMap = new Map();
    nodes.forEach(n => nodeMap.set(n.id, n));

    // Resolve string references
    const validLinks = [];
    links.forEach(l => {
      const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
      const targetId = typeof l.target === 'object' ? l.target.id : l.target;
      if (nodeMap.has(sourceId) && nodeMap.has(targetId)) {
        validLinks.push({
          ...l,
          source: sourceId,
          target: targetId,
          weight: l.weight || 1
        });
      }
    });

    this.data = { nodes, links: validLinks };
    this.particles = [];

    // Compute in-degree (incoming links) for size & color scaling
    const inDegMap = new Map();
    validLinks.forEach(l => inDegMap.set(l.target, (inDegMap.get(l.target) || 0) + 1));
    const maxIn = nodes.reduce((max, n) => Math.max(max, inDegMap.get(n.id) || 0), 0) || 1;
    nodes.forEach(n => {
      const inDegree = inDegMap.get(n.id) || 0;
      n.inDegree = inDegree;
      const t = Math.sqrt(inDegree / maxIn);
      n._radius = this.options.nodeRadius * (1.2 + 1.5 * t);
      n._color = d3.interpolateViridis(t);
      n.isolated = inDegree === 0 && !validLinks.some(l => l.source === n.id);
    });

    // Initialize particles if enabled
    if (this.options.enableParticles) {
      this.initParticles();
    }

    this.applyLayout(this.options.layout);
  }

  initParticles() {
    this.particles = [];
    this.data.links.forEach((link, idx) => {
      this.particles.push({
        linkIndex: idx,
        progress: Math.random(),
        speed: 0.001 + Math.random() * 0.002,
        color: link.color || '#38bdf8'
      });
    });
  }

  applyLayout(layoutName = 'force') {
    this.options.layout = layoutName;
    if (this.simulation) this.simulation.stop();

    const { nodes, links } = this.data;
    if (!nodes.length) return;

    if (layoutName === 'force') {
      nodes.forEach(node => {
        node.fx = null;
        node.fy = null;
      });
      this.simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links).id(d => d.id).distance(d => d.distance || this.options.linkDistance))
        .force('charge', d3.forceManyBody().strength(this.options.chargeStrength))
        .force('center', d3.forceCenter(this.width / 2, this.height / 2))
        .force('collision', d3.forceCollide().radius(d => (d._radius != null ? d._radius : (d.size || this.options.nodeRadius)) + this.options.collisionRadius))
        .alpha(1)
        .on('tick', () => this.render());

      // Pin isolated nodes (no connections) to a dedicated panel in the corner
      this.repositionIsolatedPanel();

    } else if (layoutName === 'circle-alpha' || layoutName === 'circle-degree' || layoutName === 'circle-az') {
      const orderedNodes = [...nodes].filter(n => !n.isolated).sort((a, b) => {
        if (layoutName === 'circle-degree') {
          const getId = endpoint => typeof endpoint === 'object' ? endpoint.id : endpoint;
          const degreeA = links.reduce((degree, link) => degree + (getId(link.source) === a.id || getId(link.target) === a.id ? 1 : 0), 0);
          const degreeB = links.reduce((degree, link) => degree + (getId(link.source) === b.id || getId(link.target) === b.id ? 1 : 0), 0);
          return degreeB - degreeA || (a.label || a.id).localeCompare(b.label || b.id);
        }
        // circle-alpha / circle-az: alphabetical order A->Z
        return (a.label || a.id).localeCompare(b.label || b.id);
      });
      const radius = Math.min(this.width, this.height) * 0.38;
      const angleStep = (2 * Math.PI) / orderedNodes.length;
      orderedNodes.forEach((node, i) => {
        node.fx = this.width / 2 + radius * Math.cos(i * angleStep);
        node.fy = this.height / 2 + radius * Math.sin(i * angleStep);
        node.x = node.fx;
        node.y = node.fy;
      });
      // Isolated nodes stay in their corner panel (not on the circle)
      this.repositionIsolatedPanel();
      this.render();
    } else if (layoutName === 'random') {
      nodes.forEach(node => {
        const padding = 60;
        node.fx = padding + Math.random() * (this.width - padding * 2);
        node.fy = padding + Math.random() * (this.height - padding * 2);
        node.x = node.fx;
        node.y = node.fy;
      });
      this.render();
    }

    // Build adjacency list for BFS
    this.buildAdjacency();

    this.startAnimationLoop();
  }

  // Switch layout at runtime and refit the camera to the new arrangement.
  setLayout(layoutName) {
    if (!layoutName || layoutName === this.options.layout) return;
    this.applyLayout(layoutName);
    this.fitToViewport();
    this.render();
  }

  // Center the camera on a node using its CURRENT x/y — i.e. its final
  // position after the physics simulation, never a pre-simulation coordinate.
  centerOnNode(nodeId, duration = 600) {
    const n = this.data.nodes.find(nd => nd.id === nodeId);
    if (!n) return;
    const targetScale = Math.max(this.transform.k, 1.35);
    this.centerOnPoint(n.x, n.y, targetScale, duration);
  }

  startAnimationLoop() {
    if (this.animFrameId) cancelAnimationFrame(this.animFrameId);
    
    if (!this.options.enableParticles || this.particles.length === 0) {
      this.animFrameId = null;
      return;
    }

    const loop = () => {
      if (this.options.enableParticles && this.particles.length > 0) {
        this.updateParticles();
        this.render();
        this.animFrameId = requestAnimationFrame(loop);
      } else {
        this.animFrameId = null;
      }
    };
    this.animFrameId = requestAnimationFrame(loop);
  }

  updateParticles() {
    this.particles.forEach(p => {
      p.progress += p.speed;
      if (p.progress >= 1) p.progress = 0;
    });
  }

  setupInteraction() {

    const getPos = (event) => {
      const rect = this.canvas.getBoundingClientRect();
      const clientX = event.touches ? event.touches[0].clientX : event.clientX;
      const clientY = event.touches ? event.touches[0].clientY : event.clientY;
      const x = clientX - rect.left;
      const y = clientY - rect.top;
      // Invert zoom transform
      return [
        (x - this.transform.x) / this.transform.k,
        (y - this.transform.y) / this.transform.k
      ];
    };

    const findNodeAt = (coords) => {
      const [x, y] = coords;
      for (let i = this.data.nodes.length - 1; i >= 0; i--) {
        const node = this.data.nodes[i];
        const r = (node.size || this.options.nodeRadius) + 4;
        const dx = node.x - x;
        const dy = node.y - y;
        if (dx * dx + dy * dy < r * r) {
          return node;
        }
      }
      return null;
    };

    // Manual camera controls (no d3.zoom):
    //  - wheel: zoom toward the cursor, clamped [0.15, 6]
    //  - drag on empty canvas: pan; a press on a node is reserved for
    //    click-to-trace / node dragging, so it never pans the camera.

    const clampScale = (k) => Math.max(0.15, Math.min(6, k));

    this.canvas.addEventListener('wheel', (event) => {
      event.preventDefault();
      const rect = this.canvas.getBoundingClientRect();
      const sx = event.clientX - rect.left;
      const sy = event.clientY - rect.top;
      const factor = Math.pow(1.0015, -event.deltaY);
      const k = clampScale(this.transform.k * factor);
      // Keep the world point under the cursor fixed on screen
      const wx = (sx - this.transform.x) / this.transform.k;
      const wy = (sy - this.transform.y) / this.transform.k;
      this.transform = {
        k,
        x: sx - k * wx,
        y: sy - k * wy
      };
      this.render();
    }, { passive: false });

    let panState = null; // { startX, startY, origX, origY, active }
    this.canvas.addEventListener('mousedown', (event) => {
      if (event.button !== 0) return;
      const hit = findNodeAt(getPos(event));
      if (hit) return; // node press -> selection/drag, don't pan
      panState = {
        startX: event.clientX,
        startY: event.clientY,
        origX: this.transform.x,
        origY: this.transform.y,
        active: false
      };
    });

    window.addEventListener('mousemove', (event) => {
      if (!panState) return;
      if (!panState.active) {
        const dx = event.clientX - panState.startX;
        const dy = event.clientY - panState.startY;
        if (dx * dx + dy * dy < 4) return; // allow plain clicks
        panState.active = true;
        this.canvas.style.cursor = 'grabbing';
      }
      this.transform.x = panState.origX + (event.clientX - panState.startX);
      this.transform.y = panState.origY + (event.clientY - panState.startY);
      this.render();
    });

    window.addEventListener('mouseup', () => {
      if (panState && panState.active) this.canvas.style.cursor = 'grab';
      panState = null;
    });

    const onMove = (event) => {
      const [x, y] = getPos(event);
      const node = findNodeAt([x, y]);
      
      if (node !== this.hoveredNode) {
        this.hoveredNode = node;
        this.canvas.style.cursor = node ? 'pointer' : 'grab';
        this.updateTooltip(node, event);
        this.render();

        if (this.options.onNodeHover) {
          this.options.onNodeHover(node);
        }
      } else if (node) {
        this.updateTooltipPos(event);
      }
    };

    this.canvas.addEventListener('mousemove', onMove);
    this.canvas.addEventListener('mouseleave', () => {
      this.hoveredNode = null;
      this.hideTooltip();
      this.render();
    });

    this.canvas.addEventListener('click', (event) => {
      const coords = getPos(event);
      const node = findNodeAt(coords);
      if (!node) {
        this.selectedNode = null;
        this.clearTrailNow();
        this.render();
        return;
      }

      // Path trace two-click mode
      if (this.pathTraceMode) {
        if (this.pathTrace && this.pathTrace.phase !== 'done') return;
        if (!this.pathTraceSource) {
          this.pathTraceSource = node.id;
          this.selectedNode = node;
          this.render();
          if (this.pathTraceInfoEl) {
            this.pathTraceInfoEl.innerHTML = `<strong style="color:#22c55e;">${node.label || node.id}</strong> set as source. Now click a target node.`;
          }
        } else if (!this.pathTraceTarget && node.id !== this.pathTraceSource) {
          this.pathTraceTarget = node.id;
          this.selectedNode = null;
          const srcLabel = this.data.nodes.find(n => n.id === this.pathTraceSource)?.label || this.pathTraceSource;
          const tgtLabel = node.label || node.id;
          const path = this.startPathTrace(this.pathTraceSource, this.pathTraceTarget);
          if (path) {
            if (this.pathTraceInfoEl) {
              this.pathTraceInfoEl.innerHTML = `Tracing: <strong style="color:#22c55e;">${srcLabel}</strong> → <strong style="color:#ef4444;">${tgtLabel}</strong> (${path.length - 1} hops)`;
            }
            const stopBtn = document.getElementById('btn-stop-trace');
            if (stopBtn) stopBtn.style.display = 'block';
          } else {
            if (this.pathTraceInfoEl) {
              this.pathTraceInfoEl.innerHTML = `No path found between these characters.`;
            }
            this.pathTraceSource = null;
            this.pathTraceTarget = null;
          }
        }
        return;
      }

      this.selectedNode = node;
      this.render();
      if (this.options.onNodeClick) {
        this.options.onNodeClick(node);
      }
    });
  }

  updateTooltip(node, event) {
    if (!node) {
      this.hideTooltip();
      return;
    }

    const rect = this.container.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    // Count connections
    const links = this.data.links;
    const linksCount = links.filter(l =>
      (l.source.id || l.source) === node.id || (l.target.id || l.target) === node.id
    ).length;
    const inCount = links.filter(l => (l.target.id || l.target) === node.id).length;
    const outCount = links.filter(l => (l.source.id || l.source) === node.id).length;

    let html = `<div class="tooltip-title">${node.label || node.id}</div>`;
    if (node.group || node.tag) {
      html += `<span class="tooltip-tag">${node.group || node.tag}</span>`;
    }
    if (node.description || node.summary) {
      html += `<div class="tooltip-desc">${node.description || node.summary}</div>`;
    }
    html += `<div class="tooltip-connections">🔗 ${linksCount} connection${linksCount !== 1 ? 's' : ''} — <span class="deg-in">↓ ${inCount} in</span> · <span class="deg-out">↑ ${outCount} out</span></div>`;

    this.tooltip.innerHTML = html;
    this.tooltip.style.left = `${x}px`;
    this.tooltip.style.top = `${y}px`;
    this.tooltip.classList.add('visible');
  }

  updateTooltipPos(event) {
    const rect = this.container.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    this.tooltip.style.left = `${x}px`;
    this.tooltip.style.top = `${y}px`;
  }

  hideTooltip() {
    this.tooltip.classList.remove('visible');
  }

  // Main Render Function
  render() {
    const { ctx, width, height, transform, data } = this;
    if (!ctx) return;

    const isDark = (document.documentElement.getAttribute('data-theme') || 'dark') === 'dark';

    // Reset to a known state EVERY frame: CSS-pixel identity scaled by DPR.
    // Nothing leaks into render from previous frames.
    const dpr = window.devicePixelRatio || 1;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, width, height);
    // Canonical single-matrix camera (d3-zoom style): one setTransform puts us
    // in world space — screen = world*k + t — already scaled by devicePixelRatio.
    const k = transform.k || 1;
    ctx.setTransform(dpr * k, 0, 0, dpr * k, dpr * transform.x, dpr * transform.y);

    // Weld the isolated panel to the bottom-right corner under the CURRENT
    // camera (un-projects corner coords into world so hover/drag stay exact).
    this.repositionIsolatedPanel();

    // Active Highlight Map
    const activeNodeIds = new Set();
    const activeLinks = new Set();

    if (this.hoveredNode || this.selectedNode) {
      // On the knowledge graph (pathTraceMode) highlighting is driven by HOVER
      // only: a clicked source must not dim the rest, so choosing the target
      // stays easy. Post-page graphs keep click-selection highlighting.
      const target = this.getHighlightFocus();
      if (target) {
        activeNodeIds.add(target.id);

        data.links.forEach(l => {
          const sId = l.source.id || l.source;
          const tId = l.target.id || l.target;
          if (sId === target.id || tId === target.id) {
            activeLinks.add(l);
            activeNodeIds.add(sId);
            activeNodeIds.add(tId);
          }
        });
      }
    }

    const hasHighlight = activeNodeIds.size > 0 && !this.pathTrace;
    // Note: pathTraceMode (knowledge graph) keeps hover highlighting; an
    // ACTIVE trace (pathTrace != null) temporarily takes over all dimming.

    // 0. Draw Persistent Path Trail (stays after trace completes)
    if (this.pathTrail.length > 0) {
      ctx.setLineDash([]);
      ctx.lineCap = 'round';
      this.pathTrail.forEach(t => {
        const fromNode = data.nodes.find(n => n.id === t.from);
        const toNode = data.nodes.find(n => n.id === t.to);
        if (!fromNode || !toNode) return;
        ctx.beginPath();
        ctx.moveTo(fromNode.x, fromNode.y);
        ctx.lineTo(toNode.x, toNode.y);
        ctx.globalAlpha = 0.85;
        ctx.strokeStyle = '#22c55e';
        ctx.lineWidth = 4;
        ctx.shadowColor = '#22c55e';
        ctx.shadowBlur = 10;
        ctx.stroke();
        ctx.shadowBlur = 0;
      });
      ctx.lineCap = 'butt';
    }

    // 1. Draw Links
    data.links.forEach(link => {
      const s = typeof link.source === 'object' ? link.source : data.nodes.find(n => n.id === link.source);
      const t = typeof link.target === 'object' ? link.target : data.nodes.find(n => n.id === link.target);
      if (!s || !t) return;

      const pt = this.pathTrace;
      const isPathTraceActive = pt && pt.phase !== 'done';
      // While the revealed path is on screen ("done"), softly lift every edge
      // that touches any path node in orange so the neighbours of the path are
      // visible; the trail itself stays green, everything else stays dim.
      const revealActive = !!pt && pt.phase === 'done' && this.pathTrail.length > 0;
      // Sequentially revealed neighbours: during the flight only the nodes the
      // camera has ARRIVED at (path[0..revealIdx-1]) light up orange; at the
      // final reveal every path node's connections are lit.
      let pathNodeIds = null;
      if (pt) {
        pathNodeIds = revealActive
          ? new Set(pt.path)
          : new Set(pt.path.slice(0, Math.min(pt.path.length, pt.revealIdx)));
      }
      const revealedPairs = new Set();
      this.pathTrail.forEach(t => {
        revealedPairs.add(`${t.from}|${t.to}`);
        revealedPairs.add(`${t.to}|${t.from}`);
      });

      let alpha, strokeColor, lineWidth;

      if (isPathTraceActive) {
        const sId = typeof link.source === 'object' ? link.source.id : link.source;
        const tId = typeof link.target === 'object' ? link.target.id : link.target;
        if (pt.activeEdges.has(link)) {
          // Current step — amber
          alpha = 1.0;
          strokeColor = '#b45309';
          lineWidth = 3;
        } else if (revealedPairs.has(`${sId}|${tId}`)) {
          // Already-revealed path edge — green
          alpha = 1.0;
          strokeColor = '#22c55e';
          lineWidth = 3;
        } else if (pathNodeIds.has(sId) || pathNodeIds.has(tId)) {
          // Any other connection of a path node — soft orange (same as the reveal)
          alpha = 0.5;
          strokeColor = '#f97316';
          lineWidth = (link.weight || 1.0) + 1.0;
        } else {
          alpha = 0.06;
          strokeColor = isDark ? '#334155' : '#cbd5e1';
          lineWidth = 0.8;
        }
      } else if (revealActive) {
        const sId = typeof link.source === 'object' ? link.source.id : link.source;
        const tId = typeof link.target === 'object' ? link.target.id : link.target;
        if (revealedPairs.has(`${sId}|${tId}`)) {
          // Trail edges stay green and prominent
          alpha = 0.85;
          strokeColor = '#22c55e';
          lineWidth = 4;
        } else if (pathNodeIds.has(sId) || pathNodeIds.has(tId)) {
          // Any other connection of a path node — soft orange
          alpha = 0.5;
          strokeColor = '#f97316';
          lineWidth = (link.weight || 1.0) + 1.0;
        } else {
          alpha = 0.12;
          strokeColor = isDark ? '#334155' : '#cbd5e1';
          lineWidth = 0.8;
        }
      } else {
        const isLinkActive = !hasHighlight || activeLinks.has(link);
        const focus = this.getHighlightFocus();
        if (isLinkActive && focus && hasHighlight) {
          // Hover/selection highlight: colour in-links and out-links separately.
          const sId = typeof link.source === 'object' ? link.source.id : link.source;
          const tId = typeof link.target === 'object' ? link.target.id : link.target;
          const isIn = tId === focus.id;   // edge pointing INTO the focus node
          const isOut = sId === focus.id;  // edge pointing OUT of the focus node
          alpha = 1.0;
          strokeColor = isIn ? '#f472b6' : (isOut ? '#38bdf8' : (link.color || (isDark ? '#475569' : '#94a3b8')));
          lineWidth = (link.weight || 1.5) + 2;
        } else {
          alpha = hasHighlight ? (isLinkActive ? 0.85 : 0.18) : (link.opacity || 0.3);
          strokeColor = isLinkActive && hasHighlight ? '#38bdf8' : (link.color || (isDark ? '#475569' : '#94a3b8'));
          lineWidth = isLinkActive && hasHighlight ? (link.weight || 1.5) + 1.2 : (link.weight || 1.0);
        }
      }

      ctx.beginPath();
      ctx.moveTo(s.x, s.y);
      ctx.lineTo(t.x, t.y);
      ctx.globalAlpha = alpha;
      ctx.strokeStyle = strokeColor;
      ctx.lineWidth = lineWidth;

      if (link.dashed) {
        ctx.setLineDash([4, 4]);
      } else {
        ctx.setLineDash([]);
      }
      ctx.stroke();

      // Directed Arrow if specified
      if (link.directed) {
        this.drawArrow(s, t, strokeColor, alpha);
      }

      // Edge Label if specified
      if (link.label && (isLinkActive || !hasHighlight)) {
        const midX = (s.x + t.x) / 2;
        const midY = (s.y + t.y) / 2;
        ctx.font = '10px Inter, sans-serif';
        ctx.fillStyle = isDark ? '#94a3b8' : '#475569';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(link.label, midX, midY - 6);
      }
    });

    // 1.5 Dedicated panel for isolated nodes (no connections) — drawn in screen
    // space so it stays pinned to the corner regardless of camera/transform.
    if (this.isolatedPanel) {
      const p = this.isolatedPanel;
      ctx.save();
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.globalAlpha = 1;
      ctx.fillStyle = isDark ? 'rgba(15, 23, 42, 0.78)' : 'rgba(255, 255, 255, 0.85)';
      ctx.strokeStyle = isDark ? 'rgba(148, 163, 184, 0.35)' : 'rgba(71, 85, 105, 0.35)';
      ctx.lineWidth = 1;
      ctx.setLineDash([3, 3]);
      ctx.beginPath();
      ctx.roundRect(p.x - 6, p.y - 6, p.w + 12, 22, 6);
      ctx.fill();
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.font = '10px Inter, sans-serif';
      ctx.textAlign = 'left';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = isDark ? '#94a3b8' : '#475569';
      ctx.fillText(`Isolated — ${p.count} characters, no connections`, p.x, p.y + 5);
      ctx.beginPath();
      ctx.roundRect(p.x - 6, p.y + 10, p.w + 12, p.h - 10, 6);
      ctx.fillStyle = isDark ? 'rgba(15, 23, 42, 0.55)' : 'rgba(255, 255, 255, 0.6)';
      ctx.fill();
      ctx.stroke();
      ctx.restore();
    }

    // 2. Draw Nodes
    data.nodes.forEach(node => {
      const pt = this.pathTrace;
      const isPathTraceActive = pt && pt.phase !== 'done';
      const isInPath = isPathTraceActive && pt.path.includes(node.id);

      let isNodeActive, isTarget, radius, alpha, baseColor;

      if (isPathTraceActive) {
        const isCurrentNode = pt.path[pt.nodeIndex] === node.id;
        const isNextNode = pt.nodeIndex < pt.path.length - 1 && pt.path[pt.nodeIndex + 1] === node.id;

        isTarget = isCurrentNode;
        radius = (node._radius != null ? node._radius : (node.size || this.options.nodeRadius)) * (isCurrentNode ? 1.4 : isInPath ? 1.1 : 1.0);
        alpha = isInPath ? 1.0 : 0.12;
        baseColor = isCurrentNode ? '#22c55e' : (node._color || node.color || this.getNodeColorByGroup(node.group));
      } else {
        isNodeActive = !hasHighlight || activeNodeIds.has(node.id);
        isTarget = (this.hoveredNode && this.hoveredNode.id === node.id) ||
                   (this.selectedNode && this.selectedNode.id === node.id);
        radius = (node._radius != null ? node._radius : (node.size || this.options.nodeRadius)) * (isTarget ? 1.3 : 1.0);
        alpha = hasHighlight ? (isNodeActive ? 1.0 : 0.42) : 1.0;
        baseColor = node._color || node.color || this.getNodeColorByGroup(node.group);
      }

      ctx.globalAlpha = alpha;
      ctx.beginPath();
      ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
      ctx.fillStyle = baseColor;

      if (isTarget) {
        ctx.shadowColor = baseColor;
        ctx.shadowBlur = 15;
      }
      ctx.fill();
      ctx.shadowBlur = 0;

      // Node border
      ctx.lineWidth = isTarget ? 2.5 : 1.5;
      ctx.strokeStyle = isDark ? '#0f172a' : '#ffffff';
      ctx.stroke();

      // 4. Node Labels — show on hover, on selection, on all path nodes during trace
      const showLabel = node.isolated ||
        this.options.showLabels ||
        isTarget ||
        (hasHighlight && isNodeActive && !isPathTraceActive) ||
        isInPath;

      if (showLabel) {
        const label = node.label || node.id;
        ctx.font = `${isTarget ? 'bold 12px' : '11px'} Inter, sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';

        const labelY = node.y + radius + 4;

        // Label pill background
        const textWidth = ctx.measureText(label).width;
        ctx.fillStyle = isDark ? 'rgba(15, 23, 42, 0.85)' : 'rgba(255, 255, 255, 0.85)';
        ctx.fillRect(node.x - textWidth / 2 - 3, labelY - 1, textWidth + 6, 14);

        ctx.fillStyle = isPathTraceActive && pt.path[pt.nodeIndex] === node.id ? '#22c55e' : (isDark ? '#f8fafc' : '#0f172a');
        ctx.fillText(label, node.x, labelY);

        // Show connection count for all nodes on the path
        if (isInPath) {
          const tagY = labelY + 15;
          ctx.font = '9px Inter, sans-serif';
          const linkCount = this.data.links.filter(l =>
            (l.source.id || l.source) === node.id || (l.target.id || l.target) === node.id
          ).length;
          const tagText = `${linkCount} connections`;
          const tagW = ctx.measureText(tagText).width;
          ctx.fillStyle = isDark ? 'rgba(34, 197, 94, 0.2)' : 'rgba(34, 197, 94, 0.15)';
          ctx.beginPath();
          ctx.roundRect(node.x - tagW / 2 - 4, tagY - 1, tagW + 8, 12, 3);
          ctx.fill();
          ctx.fillStyle = '#22c55e';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'top';
          ctx.fillText(tagText, node.x, tagY);
        }
      }

      // P1/P2 source/target badges during path trace mode
      if (this.pathTraceMode && !this.pathTrace) {
        if (this.pathTraceSource === node.id) {
          this.drawBadge(node, 'SRC', '#22c55e', radius);
        }
        if (this.pathTraceTarget === node.id) {
          this.drawBadge(node, 'TGT', '#ef4444', radius);
        }
      }
    });

    // 5. Pulsing ring on the CURRENT node of the fly-through (no particle).
    if (this.pathTrace && this.pathTrace.phase !== 'done' && this.pathTrace.currentNodeId) {
      const cur = data.nodes.find(n => n.id === this.pathTrace.currentNodeId);
      if (cur) {
        const r = (cur._radius != null ? cur._radius : (cur.size || this.options.nodeRadius)) + 6;
        const now = performance.now();
        const pulse = 0.5 + 0.5 * Math.sin(now / 180);
        ctx.beginPath();
        ctx.arc(cur.x, cur.y, r + 2 + pulse * 3, 0, 2 * Math.PI);
        ctx.strokeStyle = `rgba(34, 197, 94, ${0.9 - pulse * 0.5})`;
        ctx.lineWidth = 2.5;
        ctx.stroke();
      }
    }

    // Leave the context in CSS-pixel space for anything drawn after render().
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    // 6. Tag chips pinned to the path nodes during the reveal. Drawn in SCREEN
    // space so they stay readable even when the camera zooms out to fit the
    // whole graph; they vanish together with the trail (clearTrail clears it).
    if (this.pathTrace && this.pathTrace.phase === 'done' && this.pathTrail.length > 0) {
      const k = transform.k || 1;
      const tx = transform.x || 0;
      const ty = transform.y || 0;
      const pathSet = new Set(this.pathTrace.path);
      ctx.font = '9px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      this.data.nodes.forEach(n => {
        if (!pathSet.has(n.id)) return;
        const tags = this.getNodeTags(n);
        if (!tags.length) return;
        const sx = n.x * k + tx;
        const sy = n.y * k + ty;
        if (sx < -70 || sx > width + 70 || sy < -30 || sy > height + 70) return;
        const r = (n._radius != null ? n._radius : (n.size || this.options.nodeRadius)) + 2;
        const MAX_CHIPS = 3;
        const shown = tags.slice(0, MAX_CHIPS);
        shown.forEach((tag, i) => {
          const chipY = sy + r + 6 + i * 15;
          const chipText = '#' + tag;
          const cw = ctx.measureText(chipText).width + 12;
          let cx = sx - cw / 2;
          cx = Math.max(4, Math.min(width - cw - 4, cx));
          ctx.beginPath();
          ctx.roundRect(cx, chipY, cw, 14, 4);
          ctx.fillStyle = isDark ? 'rgba(15, 23, 42, 0.92)' : 'rgba(255, 255, 255, 0.92)';
          ctx.fill();
          ctx.strokeStyle = 'rgba(245, 158, 11, 0.65)';
          ctx.lineWidth = 1;
          ctx.stroke();
          ctx.fillStyle = '#f59e0b';
          ctx.fillText(chipText, cx + cw / 2, chipY + 7);
        });
        if (tags.length > MAX_CHIPS) {
          const chipY = sy + r + 6 + MAX_CHIPS * 15;
          ctx.beginPath();
          ctx.roundRect(sx - 22, chipY, 44, 14, 4);
          ctx.fillStyle = isDark ? 'rgba(15, 23, 42, 0.92)' : 'rgba(255, 255, 255, 0.92)';
          ctx.fill();
          ctx.fillStyle = '#f59e0b';
          ctx.fillText(`+${tags.length - MAX_CHIPS}`, sx, chipY + 7);
        }
      });
    }
  }

  drawArrow(s, t, color, alpha) {
    const { ctx } = this;
    const arrowLen = 8;
    const angle = Math.atan2(t.y - s.y, t.x - s.x);
    const targetRadius = (t.size || this.options.nodeRadius) + 3;
    const endX = t.x - targetRadius * Math.cos(angle);
    const endY = t.y - targetRadius * Math.sin(angle);

    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.moveTo(endX, endY);
    ctx.lineTo(endX - arrowLen * Math.cos(angle - Math.PI / 6), endY - arrowLen * Math.sin(angle - Math.PI / 6));
    ctx.lineTo(endX - arrowLen * Math.cos(angle + Math.PI / 6), endY - arrowLen * Math.sin(angle + Math.PI / 6));
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }

  drawBadge(node, text, color, radius) {
    const { ctx } = this;
    const bx = node.x;
    const by = node.y - radius - 12;

    ctx.save();
    ctx.globalAlpha = 1;
    ctx.font = 'bold 9px Inter, sans-serif';
    const tw = ctx.measureText(text).width;

    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.roundRect(bx - tw / 2 - 5, by - 7, tw + 10, 14, 4);
    ctx.fill();

    ctx.fillStyle = '#fff';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, bx, by);
    ctx.restore();
  }

  getNodeColorByGroup(group) {
    const colors = {
      'theory': '#6366f1',
      'algorithms': '#38bdf8',
      'math': '#a855f7',
      'systems': '#ec4899',
      'concept': '#10b981',
      'article': '#6366f1',
      'tag': '#f59e0b',
      'default': '#818cf8'
    };
    return colors[group] || colors['default'];
  }

  // Controls API
  zoomAt(screenX, screenY, factor) {
    const k1 = Math.max(0.15, Math.min(6, this.transform.k * factor));
    // Zoom toward the screen point: keep world point under cursor fixed
    const wx = (screenX - this.transform.x) / this.transform.k;
    const wy = (screenY - this.transform.y) / this.transform.k;
    this.transform = {
      k: k1,
      x: screenX - k1 * wx,
      y: screenY - k1 * wy
    };
    this.render();
  }

  zoomIn() {
    this.zoomAt(this.width / 2, this.height / 2, 1.3);
  }

  zoomOut() {
    this.zoomAt(this.width / 2, this.height / 2, 0.75);
  }

  resetZoom() {
    this.animateZoomTo({ k: 1, x: 0, y: 0 }, 400);
  }

  // Fit the entire graph, optionally CENTERED on a specific node instead of the
// bounding box midpoint (so the zoom-out keeps focus on e.g. the target node).
  fitToViewport(centerNodeId = null) {
    if (!this.data.nodes.length) return;

    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    this.data.nodes.forEach(n => {
      if (n.x < minX) minX = n.x;
      if (n.x > maxX) maxX = n.x;
      if (n.y < minY) minY = n.y;
      if (n.y > maxY) maxY = n.y;
    });

    const scale = Math.max(0.15, Math.min(2,
      Math.min(this.width / (Math.max(1, maxX - minX) + 100), this.height / (Math.max(1, maxY - minY) + 100))
    ));

    const centerNode = centerNodeId ? this.data.nodes.find(n => n.id === centerNodeId) : null;
    if (centerNode) {
      this.centerOnPoint(centerNode.x, centerNode.y, scale, 500);
    } else {
      this.centerOnPoint((minX + maxX) / 2, (minY + maxY) / 2, scale, 500);
    }
  }

  togglePhysics() {
    this.isPhysicsRunning = !this.isPhysicsRunning;
    if (this.isPhysicsRunning && this.simulation) {
      this.simulation.alpha(0.3).restart();
    } else if (this.simulation) {
      this.simulation.stop();
    }
    return this.isPhysicsRunning;
  }

  toggleLabels() {
    this.options.showLabels = !this.options.showLabels;
    this.render();
    return this.options.showLabels;
  }

  toggleParticles() {
    this.options.enableParticles = !this.options.enableParticles;
    if (this.options.enableParticles && this.particles.length === 0) {
      this.initParticles();
    }
    this.render();
    return this.options.enableParticles;
  }

  exportImage(filename = 'network-graph.png') {
    const link = document.createElement('a');
    link.download = filename;
    link.href = this.canvas.toDataURL('image/png');
    link.click();
  }

  // --- Adjacency & BFS ---
  buildAdjacency() {
    this.adj = new Map();
    for (const n of this.data.nodes) this.adj.set(n.id, new Set());
    for (const l of this.data.links) {
      const s = typeof l.source === 'object' ? l.source.id : l.source;
      const t = typeof l.target === 'object' ? l.target.id : l.target;
      if (this.adj.has(s) && this.adj.has(t)) {
        this.adj.get(s).add(t);
        this.adj.get(t).add(s);
      }
    }
  }

  bfs(source, target) {
    if (source === target) return [source];
    const visited = new Set([source]);
    const queue = [[source]];
    while (queue.length) {
      const path = queue.shift();
      const node = path[path.length - 1];
      for (const neighbor of (this.adj.get(node) || [])) {
        if (neighbor === target) return [...path, neighbor];
        if (!visited.has(neighbor)) {
          visited.add(neighbor);
          queue.push([...path, neighbor]);
        }
      }
    }
    return null;
  }

  // --- Path Tracer ---
  startPathTrace(sourceId, targetId) {
    this.stopPathTrace();
    this.hidePathInfo();

    // Freeze the simulation so node positions (final x/y) stay static during
    // the trace. The fly-through centers the camera on these settled coords.
    if (this.simulation) this.simulation.stop();

    const path = this.bfs(sourceId, targetId);
    if (!path || path.length < 2) return null;

    this.pathTrail = [];
    this.pathTrace = {
      path,
      nodeIndex: 0,
      revealIdx: 1,
      phase: 'active',
      activeEdges: new Set(),
      otherEdges: new Set(),
      currentNodeId: path[0],
      prevTransform: { k: this.transform.k, x: this.transform.x, y: this.transform.y }
    };
    // Remember whether the user had physics running so the reveal can restore it
    this.physicsWasRunning = this.simulation ? this.isPhysicsRunning : false;

    this.startPathTraceLoop();
    return path;
  }

  computeStepEdges() {
    const pt = this.pathTrace;
    if (!pt) return;
    pt.activeEdges.clear();
    pt.otherEdges.clear();

    const currentNodeId = pt.path[pt.nodeIndex];
    const nextNodeId = pt.nodeIndex < pt.path.length - 1 ? pt.path[pt.nodeIndex + 1] : null;

    // Mark exactly the edge of the CURRENT hop as the active step; everything
    // else in the graph is dimmed while the reveal runs.
    this.data.links.forEach(l => {
      const s = typeof l.source === 'object' ? l.source.id : l.source;
      const t = typeof l.target === 'object' ? l.target.id : l.target;
      if ((s === currentNodeId || t === currentNodeId) && nextNodeId && (s === nextNodeId || t === nextNodeId)) {
        pt.activeEdges.add(l);
      } else {
        pt.otherEdges.add(l);
      }
    });
  }

  computePathTags(path) {
    const tags = new Set();
    path.forEach(id => {
      const n = this.data.nodes.find(nd => nd.id === id);
      if (!n) return;
      this.getNodeTags(n).forEach(t => tags.add(String(t).trim().replace(/^#/, '').toLowerCase()));
    });
    return Array.from(tags);
  }

  // Tags belonging to a single node (post .tags arrays or the tag nodes' own id).
  getNodeTags(node) {
    if (Array.isArray(node.tags) && node.tags.length) {
      return node.tags.map(t => String(t).trim().replace(/^#/, ''));
    }
    if (node.type === 'tag' || node.group === 'tag') {
      return [String(node.label || node.id).replace(/^#/, '')];
    }
    return [];
  }

  showPathInfo(html) {
    if (!this.pathTraceInfoEl) return;
    this.pathTraceInfoEl.innerHTML = html;
    this.pathTraceInfoEl.style.display = 'block';
  }

  hidePathInfo() {
    if (!this.pathTraceInfoEl) return;
    this.pathTraceInfoEl.style.display = 'none';
    this.pathTraceInfoEl.innerHTML = '';
  }

  // Promise-based camera fly to a world point (node's final position).
  flyCameraTo(x, y, scale, duration, runId) {
    return new Promise((resolve) => {
      const from = { k: this.transform.k, x: this.transform.x, y: this.transform.y };
      const to = { k: scale, x: this.width / 2 - scale * x, y: this.height / 2 - scale * y };
      const start = performance.now();
      const tick = (now) => {
        if (this.pathTraceRunId !== runId || !this.pathTrace) { resolve(); return; }
        const p = Math.min(1, (now - start) / duration);
        const e = 1 - Math.pow(1 - p, 3); // easeOutCubic
        this.transform = {
          k: from.k + (to.k - from.k) * e,
          x: from.x + (to.x - from.x) * e,
          y: from.y + (to.y - from.y) * e
        };
        try { this.render(); } catch (err) { console.error('[graph-engine] render error:', err); }
        if (p < 1) requestAnimationFrame(tick);
        else resolve();
      };
      requestAnimationFrame(tick);
    });
  }

  sleep(ms, runId) {
    return new Promise((resolve) => {
      setTimeout(() => resolve(), ms);
    });
  }

  // Camera flies between the path nodes IN ORDER, revealing one edge at a
  // time. When it reaches the end it fits the WHOLE graph (islands included)
  // with the path and every traversed tag visible.
  startPathTraceLoop() {
    const FLY_MS = 650;
    const DWELL_MS = 260;
    const FOCUS_SCALE = 1.35;

    const getNode = id => this.data.nodes.find(n => n.id === id);
    const path = this.pathTrace.path;
    const runId = ++this.pathTraceRunId;

    const finish = async (skipFit) => {
      if (skipFit === true) return;
      this.pathTrace.phase = 'done';
      this.pathTrace.currentNodeId = null;
      this.pathTrace.activeEdges.clear();
      // Final reveal: fit the whole graph so even the isolated corner panel
      // stays in view — but keep the focus CENTERED on the target node
      // (e.g. spiderman), not the bounding-box midpoint.
      this.fitToViewport(path[path.length - 1]);
      const tags = this.computePathTags(path);
      const srcL = (getNode(path[0]) || {}).label || path[0];
      const tgtL = (getNode(path[path.length - 1]) || {}).label || path[path.length - 1];
      const tagChips = tags.map(t => `<span class="graph-path-tag">#${t}</span>`).join('');
      this.showPathInfo(
        `<div class="graph-path-info-row"><strong style="color:#22c55e;">${srcL}</strong> → <strong style="color:#ef4444;">${tgtL}</strong> · ${path.length - 1} hop(s)</div>` +
        (tagChips ? `<div class="graph-path-info-tags">Tags: ${tagChips}</div>` : '')
      );
      if (this.options.onPathTraceComplete) this.options.onPathTraceComplete(path);
      this.scheduleTrailClear();
    };

    (async () => {
      // 1. Fly to the source node
      const first = getNode(path[0]);
      if (first) {
        this.pathTrace.currentNodeId = path[0];
        await this.flyCameraTo(first.x, first.y, FOCUS_SCALE, FLY_MS, runId);
        if (this.pathTraceRunId !== runId) return;
        try { this.render(); } catch (e) { console.error('[graph-engine] render error:', e); }
        await this.sleep(DWELL_MS, runId);
        if (this.pathTraceRunId !== runId) return;
      }

      // 2. Walk the path: reveal edge i->i+1, then fly to node i+1
      for (let i = 0; i < path.length - 1; i++) {
        if (this.pathTraceRunId !== runId) return;

        this.pathTrace.nodeIndex = i;
        this.pathTrace.currentNodeId = path[i];
        this.pathTrail.push({ from: path[i], to: path[i + 1] });
        this.computeStepEdges();
        try { this.render(); } catch (e) { console.error('[graph-engine] render error:', e); }

        // Fly on for every hop — INCLUDING the last one, so the camera lands
        // exactly on the target node with its ring visible before the reveal.
        if (i < path.length - 1) {
          const next = getNode(path[i + 1]);
          if (next) {
            this.pathTrace.currentNodeId = path[i + 1];
            await this.flyCameraTo(next.x, next.y, FOCUS_SCALE, FLY_MS, runId);
            if (this.pathTraceRunId !== runId) return;
            // Connections light up only once the camera has ARRIVED: the next
            // node's neighbourhood does not pre-light while we are still flying.
            this.pathTrace.revealIdx = i + 2;
            try { this.render(); } catch (e) { console.error('[graph-engine] render error:', e); }
            await this.sleep(DWELL_MS, runId);
            if (this.pathTraceRunId !== runId) return;
          }
        }
      }

      // 3. Whole-graph reveal (the loop above already pushed every edge)
      if (this.pathTraceRunId !== runId) return;
      await finish();
    })();
  }

  scheduleTrailClear() {
    if (this.pathTrailClearTimer) clearTimeout(this.pathTrailClearTimer);
    const prevTransform = this.pathTrace ? this.pathTrace.prevTransform : null;
    const wasRunning = this.physicsWasRunning;
    this.pathTrailClearTimer = setTimeout(() => {
      this.pathTrail = [];
      // The tag overlay lives exactly as long as the revealed path does
      this.hidePathInfo();
      this.render();
      // Full reset: glide back to the camera the user had before the trace and
      // resume the force simulation if it was running.
      if (prevTransform) {
        this.animateZoomTo(prevTransform, 600);
      }
      if (this.simulation && wasRunning) {
        this.isPhysicsRunning = true;
        this.simulation.alpha(0.15).restart();
      }
      this.physicsWasRunning = false;
    }, 3000);
  }

  clearTrailNow() {
    if (this.pathTrailClearTimer) clearTimeout(this.pathTrailClearTimer);
    this.pathTrail = [];
    this.hidePathInfo();
    this.render();
  }

  // --- Manual camera helpers (no d3.zoom) ---
  getHighlightFocus() {
    // Knowledge graph: only hover highlights connections. Elsewhere a clicked
    // selection also highlights (so post-page graphs keep that behaviour).
    if (this.pathTraceMode) return this.hoveredNode;
    return this.hoveredNode || this.selectedNode;
  }

  cancelCameraTween() {
    this.cameraTween = null;
    if (this.cameraTweenAnimId) {
      cancelAnimationFrame(this.cameraTweenAnimId);
      this.cameraTweenAnimId = null;
    }
  }

  animateZoomTo(target, duration) {
    this.cancelCameraTween();
    const from = {
      k: this.transform.k,
      x: this.transform.x,
      y: this.transform.y
    };
    const start = performance.now();
    this.cameraTween = { from, to: target, start, duration };

    const tick = (now) => {
      if (!this.cameraTween || this.cameraTween.start !== start) return;
      const p = Math.min(1, (now - start) / duration);
      const e = 1 - Math.pow(1 - p, 3); // easeOutCubic
      this.transform = {
        k: from.k + (target.k - from.k) * e,
        x: from.x + (target.x - from.x) * e,
        y: from.y + (target.y - from.y) * e
      };
      this.render();
      if (p < 1) {
        this.cameraTweenAnimId = requestAnimationFrame(tick);
      } else {
        this.cameraTween = null;
        this.cameraTweenAnimId = null;
      }
    };
    this.cameraTweenAnimId = requestAnimationFrame(tick);
  }

  centerOnPoint(x, y, scale = 1.4, duration = 0) {
    // Make world (x, y) map to the exact screen center.
    const target = {
      k: scale,
      x: this.width / 2 - scale * x,
      y: this.height / 2 - scale * y
    };
    this.cancelCameraTween();
    if (duration > 0) {
      this.animateZoomTo(target, duration);
    } else {
      this.transform = target;
      this.render();
    }
  }

  fitNodesToView(nodeIds, padding = 120, duration = 700) {
    if (!nodeIds.length) return;
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    nodeIds.forEach(id => {
      const n = this.data.nodes.find(nd => nd.id === id);
      if (!n) return;
      if (n.x < minX) minX = n.x;
      if (n.x > maxX) maxX = n.x;
      if (n.y < minY) minY = n.y;
      if (n.y > maxY) maxY = n.y;
    });
    if (!isFinite(minX) || !isFinite(minY)) return;

    // Zoom-to-bounds: scale so path bounds + padding fit the viewport, centered.
    const gw = Math.max(1, maxX - minX);
    const gh = Math.max(1, maxY - minY);
    const scale = Math.max(0.15, Math.min(2.0,
      Math.min(this.width / (gw + padding * 2), this.height / (gh + padding * 2))
    ));
    const mx = (minX + maxX) / 2;
    const my = (minY + maxY) / 2;
    this.centerOnPoint(mx, my, scale, duration);
  }

  stopPathTrace() {
    this.pathTraceRunId++; // cancel any in-flight fly-through
    if (this.pathTraceAnimId) {
      cancelAnimationFrame(this.pathTraceAnimId);
      this.pathTraceAnimId = null;
    }
    if (this.pathTrailClearTimer) {
      clearTimeout(this.pathTrailClearTimer);
      this.pathTrailClearTimer = null;
    }
    this.pathTrace = null;
    this.pathTrail = [];
    this.pathTraceSource = null;
    this.pathTraceTarget = null;
    this.selectedNode = null;
    this.hidePathInfo();
    this.render();
  }

  destroy() {
    if (this.animFrameId) cancelAnimationFrame(this.animFrameId);
    if (this.pathTraceAnimId) cancelAnimationFrame(this.pathTraceAnimId);
    if (this.pathTrailClearTimer) clearTimeout(this.pathTrailClearTimer);
    this.hidePathInfo();
    if (this.simulation) this.simulation.stop();
    if (this.resizeObserver) this.resizeObserver.disconnect();
  }
}

window.NetworkGraph = NetworkGraph;
