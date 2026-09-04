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
      chargeStrength: options.chargeStrength || -180,
      linkDistance: options.linkDistance || 80,
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
    this.transform = d3.zoomIdentity;
    this.hoveredNode = null;
    this.selectedNode = null;
    this.animFrameId = null;
    this.isPhysicsRunning = true;

    // Path tracer state
    this.adj = new Map();
    this.pathTrace = null; // { path, nodeIndex, progress, phase, activeEdges, otherEdges }
    this.pathTraceAnimId = null;
    this.pathTrail = []; // [{from, to}] visited edges for persistent trail
    this.pathTrailClearTimer = null;

    this.init();
  }

  init() {
    this.container.innerHTML = '';
    
    // Canvas setup with HiDPI support
    this.canvas = document.createElement('canvas');
    this.canvas.className = 'network-graph-canvas';
    this.container.appendChild(this.canvas);
    this.ctx = this.canvas.getContext('2d');

    // Tooltip setup
    this.tooltip = document.createElement('div');
    this.tooltip.className = 'graph-tooltip';
    this.container.appendChild(this.tooltip);

    this.updateDimensions();

    // Zoom behavior
    this.zoom = d3.zoom()
      .scaleExtent([0.15, 6])
      .on('zoom', (event) => {
        this.transform = event.transform;
        this.render();
      });

    d3.select(this.canvas)
      .call(this.zoom)
      .on('dblclick.zoom', null); // disable double click zoom to allow node selection

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
    this.ctx.scale(dpr, dpr);
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
        .force('collision', d3.forceCollide().radius(d => (d.size || this.options.nodeRadius) + this.options.collisionRadius))
        .alpha(1)
        .on('tick', () => this.render());

    } else if (layoutName === 'circle-alpha' || layoutName === 'circle-degree') {
      const orderedNodes = [...nodes].sort((a, b) => {
        if (layoutName === 'circle-degree') {
          const getId = endpoint => typeof endpoint === 'object' ? endpoint.id : endpoint;
          const degreeA = links.reduce((degree, link) => degree + (getId(link.source) === a.id || getId(link.target) === a.id ? 1 : 0), 0);
          const degreeB = links.reduce((degree, link) => degree + (getId(link.source) === b.id || getId(link.target) === b.id ? 1 : 0), 0);
          return degreeB - degreeA || (a.label || a.id).localeCompare(b.label || b.id);
        }
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
    let isDragging = false;
    let dragNode = null;

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

    const onMove = (event) => {
      if (isDragging && dragNode) {
        const [x, y] = getPos(event);
        dragNode.fx = x;
        dragNode.fy = y;
        if (this.simulation && this.isPhysicsRunning) {
          this.simulation.alpha(0.3).restart();
        } else {
          dragNode.x = x;
          dragNode.y = y;
          this.render();
        }
        return;
      }

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

    // Node Dragging integration with D3 drag
    d3.select(this.canvas).call(
      d3.drag()
        .container(this.canvas)
        .subject((event) => {
          const [x, y] = [
            (event.x - this.transform.x) / this.transform.k,
            (event.y - this.transform.y) / this.transform.k
          ];
          return findNodeAt([x, y]);
        })
        .on('start', (event) => {
          if (!event.subject) return;
          isDragging = true;
          dragNode = event.subject;
          if (this.simulation && this.isPhysicsRunning) {
            this.simulation.alphaTarget(0.3).restart();
          }
          dragNode.fx = dragNode.x;
          dragNode.fy = dragNode.y;
        })
        .on('drag', (event) => {
          if (!dragNode) return;
          const [x, y] = [
            (event.x - this.transform.x) / this.transform.k,
            (event.y - this.transform.y) / this.transform.k
          ];
          dragNode.fx = x;
          dragNode.fy = y;
          if (!this.isPhysicsRunning) {
            dragNode.x = x;
            dragNode.y = y;
            this.render();
          }
        })
        .on('end', (event) => {
          if (!dragNode) return;
          if (this.simulation && this.isPhysicsRunning) {
            this.simulation.alphaTarget(0);
          }
          if (this.options.layout === 'force') {
            dragNode.fx = null;
            dragNode.fy = null;
          }
          isDragging = false;
          dragNode = null;
        })
    );

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
    const linksCount = this.data.links.filter(l => 
      (l.source.id || l.source) === node.id || (l.target.id || l.target) === node.id
    ).length;

    let html = `<div class="tooltip-title">${node.label || node.id}</div>`;
    if (node.group || node.tag) {
      html += `<span class="tooltip-tag">${node.group || node.tag}</span>`;
    }
    if (node.description || node.summary) {
      html += `<div class="tooltip-desc">${node.description || node.summary}</div>`;
    }
    html += `<div class="tooltip-connections">🔗 ${linksCount} connection${linksCount !== 1 ? 's' : ''}</div>`;

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

    // Clear background
    ctx.clearRect(0, 0, width, height);
    ctx.save();

    // Apply zoom & pan translation
    ctx.translate(transform.x, transform.y);
    ctx.scale(transform.k, transform.k);

    // Active Highlight Map
    const activeNodeIds = new Set();
    const activeLinks = new Set();

    if (this.hoveredNode || this.selectedNode) {
      const target = this.hoveredNode || this.selectedNode;
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

    const hasHighlight = activeNodeIds.size > 0 && !this.pathTraceMode;

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

      let alpha, strokeColor, lineWidth;

      if (isPathTraceActive) {
        if (pt.activeEdges.has(link)) {
          alpha = 1.0;
          strokeColor = '#22c55e';
          lineWidth = 3;
        } else if (pt.otherEdges.has(link)) {
          alpha = 0.4;
          strokeColor = '#b45309';
          lineWidth = 1.5;
        } else {
          alpha = 0.06;
          strokeColor = isDark ? '#334155' : '#cbd5e1';
          lineWidth = 0.8;
        }
      } else {
        const isLinkActive = !hasHighlight || activeLinks.has(link);
        alpha = hasHighlight ? (isLinkActive ? 0.9 : 0.08) : (link.opacity || 0.3);
        strokeColor = isLinkActive && hasHighlight ? '#38bdf8' : (link.color || (isDark ? '#475569' : '#94a3b8'));
        lineWidth = isLinkActive && hasHighlight ? (link.weight || 1.5) + 1.2 : (link.weight || 1.0);
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
        radius = (node.size || this.options.nodeRadius) * (isCurrentNode ? 1.4 : isInPath ? 1.1 : 1.0);
        alpha = isInPath ? 1.0 : 0.12;
        baseColor = isCurrentNode ? '#22c55e' : (node.color || this.getNodeColorByGroup(node.group));
      } else {
        isNodeActive = !hasHighlight || activeNodeIds.has(node.id);
        isTarget = (this.hoveredNode && this.hoveredNode.id === node.id) ||
                   (this.selectedNode && this.selectedNode.id === node.id);
        radius = (node.size || this.options.nodeRadius) * (isTarget ? 1.3 : 1.0);
        alpha = hasHighlight ? (isNodeActive ? 1.0 : 0.15) : 1.0;
        baseColor = node.color || this.getNodeColorByGroup(node.group);
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
      const showLabel = this.options.showLabels ||
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

    // 5. Draw Path Trace Ball
    if (this.pathTrace && this.pathTrace.phase !== 'done') {
      const pt = this.pathTrace;
      ctx.globalAlpha = 1.0;
      ctx.beginPath();
      ctx.arc(pt.ballX, pt.ballY, 6, 0, 2 * Math.PI);
      ctx.fillStyle = '#22c55e';
      ctx.shadowColor = '#22c55e';
      ctx.shadowBlur = 18;
      ctx.fill();
      ctx.shadowBlur = 0;
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    ctx.restore();
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
  zoomIn() {
    d3.select(this.canvas).transition().duration(300).call(this.zoom.scaleBy, 1.3);
  }

  zoomOut() {
    d3.select(this.canvas).transition().duration(300).call(this.zoom.scaleBy, 0.75);
  }

  resetZoom() {
    d3.select(this.canvas).transition().duration(400).call(this.zoom.transform, d3.zoomIdentity);
  }

  fitToViewport() {
    if (!this.data.nodes.length) return;
    
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    this.data.nodes.forEach(n => {
      if (n.x < minX) minX = n.x;
      if (n.x > maxX) maxX = n.x;
      if (n.y < minY) minY = n.y;
      if (n.y > maxY) maxY = n.y;
    });

    const padding = 50;
    const graphWidth = maxX - minX + padding * 2;
    const graphHeight = maxY - minY + padding * 2;

    const scale = Math.min(this.width / graphWidth, this.height / graphHeight, 2);
    const midX = (minX + maxX) / 2;
    const midY = (minY + maxY) / 2;

    const transform = d3.zoomIdentity
      .translate(this.width / 2, this.height / 2)
      .scale(scale)
      .translate(-midX, -midY);

    d3.select(this.canvas).transition().duration(500).call(this.zoom.transform, transform);
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

    const path = this.bfs(sourceId, targetId);
    if (!path || path.length < 2) return null;

    this.pathTrail = [];
    this.pathTrace = {
      path,
      nodeIndex: 0,
      progress: 0,
      phase: 'pause',
      pauseFrames: 0,
      activeEdges: new Set(),
      otherEdges: new Set(),
      ballX: 0,
      ballY: 0
    };

    // Set initial ball position
    const startNode = this.data.nodes.find(n => n.id === path[0]);
    if (startNode) {
      this.pathTrace.ballX = startNode.x;
      this.pathTrace.ballY = startNode.y;
    }

    // Compute edges for first step
    this.computeStepEdges();

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

    // Find all edges connected to current node
    this.data.links.forEach(l => {
      const s = typeof l.source === 'object' ? l.source.id : l.source;
      const t = typeof l.target === 'object' ? l.target.id : l.target;

      if (s === currentNodeId || t === currentNodeId) {
        if (nextNodeId && (s === nextNodeId || t === nextNodeId)) {
          pt.activeEdges.add(l);
        } else {
          pt.otherEdges.add(l);
        }
      }
    });
  }

  startPathTraceLoop() {
    const PAUSE_FRAMES = 45;
    const MOVE_SPEED = 0.035;

    // Zoom to the source node at start
    this.zoomToNode(this.pathTrace.path[0], 2.5, 500);

    const step = () => {
      const pt = this.pathTrace;
      if (!pt) return;

      if (pt.phase === 'pause') {
        pt.pauseFrames++;
        if (pt.pauseFrames === 1) {
          // Just arrived at a new node — zoom to it
          this.zoomToNode(pt.path[pt.nodeIndex], 2.8, 350);
        }
        if (pt.pauseFrames >= PAUSE_FRAMES) {
          pt.phase = 'move';
          pt.progress = 0;
          pt.pauseFrames = 0;
        }
      } else if (pt.phase === 'move') {
        pt.progress += MOVE_SPEED;

        const fromNode = this.data.nodes.find(n => n.id === pt.path[pt.nodeIndex]);
        const toNode = this.data.nodes.find(n => n.id === pt.path[pt.nodeIndex + 1]);

        if (fromNode && toNode) {
          pt.ballX = fromNode.x + (toNode.x - fromNode.x) * pt.progress;
          pt.ballY = fromNode.y + (toNode.y - fromNode.y) * pt.progress;
        }

        if (pt.progress >= 1) {
          // Add completed edge to persistent trail
          this.pathTrail.push({ from: pt.path[pt.nodeIndex], to: pt.path[pt.nodeIndex + 1] });

          pt.nodeIndex++;
          pt.progress = 0;

          if (pt.nodeIndex >= pt.path.length - 1) {
            pt.phase = 'done';
            const finalNode = this.data.nodes.find(n => n.id === pt.path[pt.path.length - 1]);
            if (finalNode) {
              pt.ballX = finalNode.x;
              pt.ballY = finalNode.y;
            }
            this.render();
            // Zoom out to show the full path
            this.fitNodesToView(pt.path, 120, 700);
            if (this.options.onPathTraceComplete) this.options.onPathTraceComplete(pt.path);
            this.scheduleTrailClear();
            return;
          }

          pt.phase = 'pause';
          this.computeStepEdges();
        }
      }

      this.render();
      this.pathTraceAnimId = requestAnimationFrame(step);
    };

    this.pathTraceAnimId = requestAnimationFrame(step);
  }

  scheduleTrailClear() {
    if (this.pathTrailClearTimer) clearTimeout(this.pathTrailClearTimer);
    this.pathTrailClearTimer = setTimeout(() => {
      this.pathTrail = [];
      this.render();
    }, 3000);
  }

  clearTrailNow() {
    if (this.pathTrailClearTimer) clearTimeout(this.pathTrailClearTimer);
    this.pathTrail = [];
    this.render();
  }

  // --- Zoom helpers for path tracing ---
  zoomToNode(nodeId, scale = 2.5, duration = 400) {
    const node = this.data.nodes.find(n => n.id === nodeId);
    if (!node) return;
    const transform = d3.zoomIdentity
      .translate(this.width / 2, this.height / 2)
      .scale(scale)
      .translate(-node.x, -node.y);
    d3.select(this.canvas).transition().duration(duration).ease(d3.easeCubicOut)
      .call(this.zoom.transform, transform);
  }

  fitNodesToView(nodeIds, padding = 100, duration = 600) {
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
    const gw = maxX - minX + padding * 2;
    const gh = maxY - minY + padding * 2;
    const scale = Math.min(this.width / gw, this.height / gh, 2.5);
    const midX = (minX + maxX) / 2;
    const midY = (minY + maxY) / 2;
    const transform = d3.zoomIdentity
      .translate(this.width / 2, this.height / 2)
      .scale(scale)
      .translate(-midX, -midY);
    d3.select(this.canvas).transition().duration(duration).ease(d3.easeCubicOut)
      .call(this.zoom.transform, transform);
  }

  stopPathTrace() {
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
    this.render();
  }

  destroy() {
    if (this.animFrameId) cancelAnimationFrame(this.animFrameId);
    if (this.pathTraceAnimId) cancelAnimationFrame(this.pathTraceAnimId);
    if (this.pathTrailClearTimer) clearTimeout(this.pathTrailClearTimer);
    if (this.simulation) this.simulation.stop();
    if (this.resizeObserver) this.resizeObserver.disconnect();
  }
}

window.NetworkGraph = NetworkGraph;
