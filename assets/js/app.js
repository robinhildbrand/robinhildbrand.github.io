/**
 * Main Application Orchestrator, Router & UI Controller
 */

class App {
  constructor() {
    this.store = new PostsStore();
    this.currentView = null;
    this.activeGraphInstances = [];

    this.init();
  }

  async init() {
    this.initTheme();
    this.initSearchModal();
    this.initGlobalEvents();

    // Load posts
    await this.store.loadIndex();

    // Setup router
    window.addEventListener('hashchange', () => this.handleRoute());
    this.handleRoute();
  }

  // --- Theme Management ---
  initTheme() {
    const savedTheme = localStorage.getItem('theme') || 
      (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    
    document.documentElement.setAttribute('data-theme', savedTheme);
    this.updateThemeButtonIcon(savedTheme);

    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    if (themeToggleBtn) {
      themeToggleBtn.addEventListener('click', () => {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('theme', next);
        this.updateThemeButtonIcon(next);

        // Notify active graphs to re-render with new colors
        this.activeGraphInstances.forEach(g => {
          if (g && typeof g.render === 'function') g.render();
        });
      });
    }
  }

  updateThemeButtonIcon(theme) {
    const btn = document.getElementById('theme-toggle-btn');
    if (!btn) return;
    btn.innerHTML = theme === 'dark' ? '☀️' : '🌙';
    btn.setAttribute('title', `Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`);
  }

  // --- Router ---
  async handleRoute() {
    // Clear active graphs from previous view
    this.activeGraphInstances.forEach(g => {
      if (g && typeof g.stopPathTrace === 'function') g.stopPathTrace();
      if (g && typeof g.destroy === 'function') g.destroy();
    });
    this.activeGraphInstances = [];

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'instant' });

    const hash = window.location.hash || '#/';
    this.updateActiveNavLinks(hash);

    const appEl = document.getElementById('app');
    if (!appEl) return;

    if (hash === '#/' || hash === '') {
      await this.renderHomeView(appEl);
    } else if (hash === '#/posts') {
      await this.renderPostsListView(appEl);
    } else if (hash.startsWith('#/post/')) {
      const slug = hash.replace('#/post/', '').split('?')[0];
      await this.renderSinglePostView(appEl, slug);
    } else if (hash === '#/graph') {
      await this.renderGlobalGraphView(appEl);
    } else if (hash === '#/about') {
      await this.renderAboutView(appEl);
    } else {
      appEl.innerHTML = `
        <div class="container" style="padding: 6rem 1rem; text-align: center;">
          <h1 style="font-size: 3rem; margin-bottom: 1rem;">404</h1>
          <p style="color: var(--text-secondary); margin-bottom: 2rem;">The requested page could not be found.</p>
          <a href="#/" class="btn btn-primary">Return Home</a>
        </div>
      `;
    }
  }

  updateActiveNavLinks(hash) {
    document.querySelectorAll('.nav-link').forEach(link => {
      const href = link.getAttribute('href');
      if (href === hash || (href === '#/posts' && hash.startsWith('#/post/'))) {
        link.classList.add('active');
      } else {
        link.classList.remove('active');
      }
    });
  }

  // --- Views ---

  // 1. Home View
  async renderHomeView(container) {
    const posts = await this.store.loadIndex();
    const featuredPosts = posts.slice(0, 4);

    container.innerHTML = `
      <section class="hero-section">
        <div class="container">
          <div class="hero-grid">
            <div class="hero-content">
              <div class="hero-badge">
                <span class="hero-badge-pulse"></span>
                <span>Interactive Network Graph Blog</span>
              </div>
              <h1 class="hero-title">
                Exploring Ideas Through <span class="hero-title-highlight">Connected Graphs</span> & Deep Reasoning.
              </h1>
              <p class="hero-description">
                A static blog on spectral graph theory, machine learning, and knowledge graphs with live physics simulations, mathematical rigor, and bi-directional wikilinks.
              </p>
              <div class="hero-cta-group">
                <a href="#/posts" class="btn btn-primary">Read Articles →</a>
                <a href="#/graph" class="btn btn-secondary">Explore Knowledge Graph 🕸️</a>
              </div>
            </div>
            <div class="hero-graph-preview">
              <div class="hero-graph-canvas-container" id="hero-graph-canvas"></div>
              <div class="hero-graph-overlay">
                <span>⚡ Live Knowledge Graph Topology</span>
                <a href="#/graph" style="font-weight: 600;">Full Graph →</a>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section style="padding: 4rem 0;">
        <div class="container">
          <div class="section-header">
            <div>
              <h2 class="section-title">✨ Featured Articles</h2>
              <p class="section-subtitle">Deep dives with embedded interactive graph visualizations</p>
            </div>
            <a href="#/posts" style="font-weight: 600; font-size: 0.9rem;">View all posts (${posts.length}) →</a>
          </div>

          <div class="post-grid">
            ${featuredPosts.map(post => this.renderPostCard(post)).join('')}
          </div>
        </div>
      </section>
    `;

    // Initialize Hero Graph
    const heroCanvasEl = document.getElementById('hero-graph-canvas');
    if (heroCanvasEl) {
      const globalData = this.store.getGlobalGraphData();
      const heroGraph = new NetworkGraph(heroCanvasEl, {
        layout: 'force',
        enableParticles: true,
        chargeStrength: -160,
        linkDistance: 70,
        showLabels: true,
        onNodeClick: (node) => {
          if (node.slug) {
            window.location.hash = `#/post/${node.slug}`;
          } else if (node.type === 'tag') {
          }
        }
      });
      heroGraph.setData(globalData);
      this.activeGraphInstances.push(heroGraph);
    }
  }

  // 2. Posts List View
  async renderPostsListView(container) {
    const posts = await this.store.loadIndex();

    container.innerHTML = `
      <div class="container" style="padding: 3.5rem 1rem 5rem;">
        <div class="section-header" style="margin-bottom: 2rem;">
          <div>
            <h1 class="section-title">📚 All Articles</h1>
            <p class="section-subtitle">Research notes, tutorials, and graph visualizations</p>
          </div>
          <div style="display: flex; gap: 0.5rem; align-items: center;">
            <span style="font-size: 0.85rem; color: var(--text-muted);">${posts.length} posts published</span>
          </div>
        </div>

        <div class="post-grid">
          ${posts.map(post => this.renderPostCard(post)).join('')}
        </div>
      </div>
    `;
  }

  // 3. Single Post View
  async renderSinglePostView(container, slug) {
    try {
      const post = await this.store.getPostBySlug(slug);

      if (!post || !post.rawContent) {
        container.innerHTML = `
          <div class="container" style="padding: 6rem 1rem; text-align: center;">
            <h1 style="font-size: 2.5rem; margin-bottom: 1rem;">Post Not Found</h1>
            <p style="color: var(--text-secondary); margin-bottom: 2rem;">The post "${slug}" could not be loaded.</p>
            <a href="#/posts" class="btn btn-primary">Back to Articles</a>
          </div>
        `;
        return;
      }

      const { metadata, content } = MarkdownProcessor.parseFrontmatter(post.rawContent);
      const postTitle = metadata.title || post.title || slug;
      const postDate = metadata.date || post.date || '';
      const postAuthor = metadata.author || post.author || 'Robin Hildbrand';
      const postReadTime = metadata.readTime || post.readTime || '6 min read';

      const { html, headings, graphsToMount } = MarkdownProcessor.render(content);

      // Prev / Next Navigation
      const allPosts = this.store.posts;
      const currentIndex = allPosts.findIndex(p => p.slug === slug);
      const prevPost = currentIndex > 0 ? allPosts[currentIndex - 1] : null;
      const nextPost = currentIndex < allPosts.length - 1 ? allPosts[currentIndex + 1] : null;

      container.innerHTML = `
        <div class="reading-progress-bar" id="reading-progress"></div>
        <div class="container">
          <div class="post-layout">
            <article class="post-main">
              <header class="post-header">
                <nav class="post-breadcrumb">
                  <a href="#/">Home</a>
                  <span>/</span>
                  <a href="#/posts">Articles</a>
                  <span>/</span>
                  <span>${postTitle}</span>
                </nav>
                <h1 class="post-title">${postTitle}</h1>
                <div class="post-meta-bar">
                  <div class="post-author">
                    <img src="assets/images/avatar.svg" alt="${postAuthor}" class="author-avatar">
                    <span>${postAuthor}</span>
                  </div>
                  <span>•</span>
                  <span>📅 ${postDate}</span>
                  <span>•</span>
                  <span>⏱️ ${postReadTime}</span>
                </div>
                <div class="tag-list" style="margin-top: 1rem;">
                </div>
              </header>

              <div class="prose" id="article-content">
                ${html}
              </div>

              <nav class="post-navigation">
                ${prevPost ? `
                  <a href="#/post/${prevPost.slug}" class="nav-post-card">
                    <span class="nav-post-direction">← Previous Post</span>
                    <span class="nav-post-title">${prevPost.title}</span>
                  </a>
                ` : `<div></div>`}
                ${nextPost ? `
                  <a href="#/post/${nextPost.slug}" class="nav-post-card" style="text-align: right;">
                    <span class="nav-post-direction">Next Post →</span>
                    <span class="nav-post-title">${nextPost.title}</span>
                  </a>
                ` : `<div></div>`}
              </nav>
            </article>

            <aside class="post-sidebar">
              <div class="sidebar-card">
                <div class="sidebar-card-title">🕸️ Article Connections</div>
                <p style="font-size: 0.775rem; color: var(--text-secondary);">Interactive ego-network of related article connections.</p>
                <div class="mini-graph-container" id="post-ego-graph"></div>
                <a href="#/graph" style="font-size: 0.775rem; font-weight: 600; display: block; margin-top: 0.65rem; text-align: right;">Open Global Graph ↗</a>
              </div>

              ${headings.length > 1 ? `
                <div class="sidebar-card" style="margin-top: 1.5rem;">
                  <div class="sidebar-card-title">📑 Table of Contents</div>
                  <ul class="toc-list">
                    ${headings.map(h => `
                      <li class="toc-item-${h.level}">
                        <a href="#${h.slug}" class="toc-link" onclick="event.preventDefault(); document.getElementById('${h.slug}').scrollIntoView({ behavior: 'smooth' });">${h.text}</a>
                      </li>
                    `).join('')}
                  </ul>
                </div>
              ` : ''}
            </aside>
          </div>
        </div>
      `;

      // 1. Mount embedded interactive graphs
      MarkdownProcessor.mountGraphs(graphsToMount);

      // 2. Mount Post Ego Network
      const egoEl = document.getElementById('post-ego-graph');
      if (egoEl) {
        const egoData = this.store.getLocalGraphForPost(slug);
        const egoGraph = new NetworkGraph(egoEl, {
          layout: 'force',
          enableParticles: false,
          chargeStrength: -120,
          linkDistance: 60,
          showLabels: true,
          onNodeClick: (node) => {
            if (node.slug && node.slug !== slug) {
              window.location.hash = `#/post/${node.slug}`;
            }
          }
        });
        egoGraph.setData(egoData);
        this.activeGraphInstances.push(egoGraph);
      }

      // 3. Setup Reading Progress Bar
      const progressBar = document.getElementById('reading-progress');
      const updateProgress = () => {
        const total = document.documentElement.scrollHeight - window.innerHeight;
        const progress = total > 0 ? (window.scrollY / total) * 100 : 0;
        if (progressBar) progressBar.style.width = `${Math.min(100, Math.max(0, progress))}%`;
      };
      window.addEventListener('scroll', updateProgress);
      updateProgress();
    } catch (err) {
      console.error('Error rendering single post view:', err);
      container.innerHTML = `
        <div class="container" style="padding: 6rem 1rem; text-align: center;">
          <h1 style="font-size: 2.5rem; margin-bottom: 1rem;">Failed to Render Article</h1>
          <p style="color: var(--text-secondary); margin-bottom: 2rem;">${err.message || 'An unexpected error occurred while loading this post.'}</p>
          <a href="#/posts" class="btn btn-primary">Back to Articles</a>
        </div>
      `;
    }
  }

  // 4. Global Graph Explorer View
  async renderGlobalGraphView(container) {
    await this.store.loadIndex();
    const globalData = this.store.getGlobalGraphData();
    const tags = Array.from(this.store.tagsMap.keys());

    container.innerHTML = `
      <div class="global-graph-page">
        <div class="graph-instruction-popup" id="graph-instruction-popup">
          <div class="graph-instruction-card">
            <div class="graph-instruction-icon">🕸️</div>
            <h2 class="graph-instruction-title">Marvel Character Network</h2>
            <p class="graph-instruction-text">
              Explore connections between <strong>303 Marvel characters</strong> derived from Wikipedia hyperlinks.
              Hover over any node to see its details and connections.
            </p>
            <div class="graph-instruction-divider"></div>
            <h3 class="graph-instruction-subtitle">Path Tracer</h3>
            <p class="graph-instruction-text">
              Click any node to set it as <span style="color:#22c55e;font-weight:700;">source</span>, then click another node to set it as <span style="color:#ef4444;font-weight:700;">target</span>.
              A green ball will follow the shortest path between them, pausing at each character to show its connections.
            </p>
            <div class="graph-instruction-tips">
              <span>🔍 Scroll to zoom</span>
              <span>✋ Drag to pan</span>
              <span>🖱️ Click + drag nodes to rearrange</span>
            </div>
            <button class="graph-instruction-btn" id="graph-instruction-dismiss">Got it</button>
          </div>
        </div>

        <div class="global-graph-main">
          <div class="global-graph-canvas-container" id="global-graph-canvas">
            <div class="graph-hud-controls">
              <div class="hud-pill">
                <span>🔍</span>
                <input type="text" class="hud-search-input" id="graph-node-search" placeholder="Search nodes...">
              </div>
            </div>

            <div class="node-inspector" id="node-inspector">
              <div class="node-inspector-header">
                <div class="node-inspector-title" id="inspector-title">Node Title</div>
                <button class="node-inspector-close" id="inspector-close">✕</button>
              </div>
              <div class="node-inspector-desc" id="inspector-desc"></div>
              <div class="node-inspector-links-title">Connections</div>
              <ul class="node-inspector-links" id="inspector-links"></ul>
              <a href="#" class="btn btn-primary btn-sm node-inspector-btn" id="inspector-btn">Read Article →</a>
            </div>
          </div>

          <div class="global-graph-sidebar">
            <div class="sidebar-section">
              <div class="sidebar-heading">
                <span>Network Controls</span>
              </div>
              <div class="control-group">
                <label class="control-label">
                  <span>Layout Mode</span>
                </label>
                <select class="control-select" id="graph-layout-select">
                  <option value="force">Force-Directed Physics</option>
                  <option value="circle-alpha">Circle by A-Z</option>
                  <option value="circle-degree">Circle by Degree</option>
                  <option value="random">Random</option>
                </select>
              </div>
              <div class="control-group">
                <label class="control-label">
                  <span>Charge Repulsion</span>
                  <span id="charge-val">-180</span>
                </label>
                <input type="range" class="control-slider" id="slider-charge" min="-400" max="-50" value="-180">
              </div>
              <div class="control-group">
                <label class="control-label">
                  <span>Link Distance</span>
                  <span id="distance-val">80</span>
                </label>
                <input type="range" class="control-slider" id="slider-distance" min="30" max="200" value="80">
              </div>
            </div>

            <div class="sidebar-section">
              <div class="sidebar-heading">
                <span>Visual Toggles</span>
              </div>
              <div style="display: flex; flex-direction: column; gap: 0.6rem;">
                <button class="btn btn-secondary btn-sm" id="btn-toggle-particles">✨ Toggle Flow Particles</button>
                <button class="btn btn-secondary btn-sm" id="btn-toggle-labels">🏷️ Toggle Labels</button>
                <button class="btn btn-secondary btn-sm" id="btn-fit-view">⊙ Fit to Screen</button>
                <button class="btn btn-secondary btn-sm" id="btn-export-graph">📷 Export PNG Snapshot</button>
              </div>
            </div>

            <div class="sidebar-section">
              <div class="sidebar-heading">
                <span>Path Tracer</span>
              </div>
              <div class="path-tracer-section">
                <div class="path-trace-info visible" style="display:block;">
                  Click any node to set it as <strong style="color:#22c55e;">source</strong>, then click another node to set it as <strong style="color:#ef4444;">target</strong>. The tracer ball will follow the shortest path between them.
                </div>
                <button class="path-trace-btn stop" id="btn-stop-trace" style="display:none;">Stop Tracing</button>
                <div class="path-trace-legend">
                  <span class="legend-item"><span class="legend-swatch active"></span> Next edge</span>
                  <span class="legend-item"><span class="legend-swatch other"></span> Other connections</span>
                  <span class="legend-item"><span class="legend-swatch dim"></span> Rest of graph</span>
                  <span class="legend-item"><span class="legend-swatch ball"></span> Ball</span>
                </div>
              </div>
            </div>

            <div class="sidebar-section">
              <div class="sidebar-heading">
                <span>Filter by Topic</span>
              </div>
              <div class="filter-tags-grid">
                ${tags.map(tag => `
                  <label class="tag-checkbox-label checked" data-tag="${tag}">
                    <input type="checkbox" checked value="${tag}">
                    <span>#${tag}</span>
                  </label>
                `).join('')}
              </div>
            </div>
          </div>
        </div>
      </div>
    `;

    const canvasContainer = document.getElementById('global-graph-canvas');
    const inspectorEl = document.getElementById('node-inspector');
    const inspectorTitle = document.getElementById('inspector-title');
    const inspectorDesc = document.getElementById('inspector-desc');
    const inspectorLinks = document.getElementById('inspector-links');
    const inspectorBtn = document.getElementById('inspector-btn');
    const inspectorClose = document.getElementById('inspector-close');

    inspectorClose.onclick = () => inspectorEl.classList.remove('active');

    const graph = new NetworkGraph(canvasContainer, {
      layout: 'force',
      enableParticles: false,
      showLabels: false,
      chargeStrength: -180,
      linkDistance: 80,
      onNodeClick: (node) => {
        inspectorEl.classList.add('active');
        inspectorTitle.innerText = node.label || node.id;
        inspectorDesc.innerText = node.description || (node.type === 'post' ? 'Blog Article' : 'Knowledge Concept');
        
        // Find connected links
        const connected = globalData.links.filter(l => 
          (l.source.id || l.source) === node.id || (l.target.id || l.target) === node.id
        );

        inspectorLinks.innerHTML = connected.map(l => {
          const isSource = (l.source.id || l.source) === node.id;
          const otherId = isSource ? (l.target.id || l.target) : (l.source.id || l.source);
          const otherNode = globalData.nodes.find(n => n.id === otherId);
          return `<li class="node-inspector-link-item"><span>${isSource ? '→' : '←'}</span> <strong>${otherNode ? otherNode.label : otherId}</strong></li>`;
        }).join('');

        if (node.slug) {
          inspectorBtn.style.display = 'block';
          inspectorBtn.href = `#/post/${node.slug}`;
          inspectorBtn.innerText = 'Read Article →';
        } else {
          inspectorBtn.style.display = 'none';
        }
      }
    });

    graph.setData(globalData);
    this.activeGraphInstances.push(graph);

    // Sidebar controls integration
    const layoutSelect = document.getElementById('graph-layout-select');
    layoutSelect.onchange = (e) => graph.applyLayout(e.target.value);

    const sliderCharge = document.getElementById('slider-charge');
    sliderCharge.oninput = (e) => {
      const val = Number(e.target.value);
      document.getElementById('charge-val').innerText = val;
      graph.options.chargeStrength = val;
      if (graph.simulation) {
        graph.simulation.force('charge', d3.forceManyBody().strength(val)).alpha(0.3).restart();
      }
    };

    const sliderDistance = document.getElementById('slider-distance');
    sliderDistance.oninput = (e) => {
      const val = Number(e.target.value);
      document.getElementById('distance-val').innerText = val;
      graph.options.linkDistance = val;
      if (graph.simulation) {
        graph.simulation.force('link').distance(val);
        graph.simulation.alpha(0.3).restart();
      }
    };

    document.getElementById('btn-toggle-particles').onclick = () => graph.toggleParticles();
    document.getElementById('btn-toggle-labels').onclick = () => graph.toggleLabels();
    document.getElementById('btn-fit-view').onclick = () => graph.fitToViewport();
    document.getElementById('btn-export-graph').onclick = () => graph.exportImage('global-knowledge-graph.png');

    // --- Instruction Popup ---
    const instructionPopup = document.getElementById('graph-instruction-popup');
    const instructionDismiss = document.getElementById('graph-instruction-dismiss');
    if (instructionPopup && instructionDismiss) {
      instructionDismiss.addEventListener('click', () => {
        instructionPopup.classList.add('dismissed');
      });
      instructionPopup.addEventListener('click', (e) => {
        if (e.target === instructionPopup) instructionPopup.classList.add('dismissed');
      });
    }

    // --- Path Tracer (click-to-select) ---
    graph.pathTraceMode = true;
    graph.pathTraceSource = null;
    graph.pathTraceTarget = null;
    graph.pathTraceInfoEl = traceInfo;

    const stopTraceBtn = document.getElementById('btn-stop-trace');

    stopTraceBtn.addEventListener('click', () => {
      graph.stopPathTrace();
      graph.pathTraceMode = false;
      graph.pathTraceSource = null;
      graph.pathTraceTarget = null;
      traceInfo.innerHTML = `Click any node to set it as <strong style="color:#22c55e;">source</strong>, then click another node to set it as <strong style="color:#ef4444;">target</strong>. The tracer ball will follow the shortest path between them.`;
      traceInfo.classList.add('visible');
      stopTraceBtn.style.display = 'none';
    });

    graph.options.onPathTraceComplete = (path) => {
      traceInfo.innerHTML = `<strong style="color:#22c55e;">Path complete!</strong> ${path.length - 1} hops traced.`;
      traceInfo.classList.add('visible');
      graph.pathTraceSource = null;
      graph.pathTraceTarget = null;
      setTimeout(() => {
        stopTraceBtn.style.display = 'none';
        traceInfo.innerHTML = `Click any node to set it as <strong style="color:#22c55e;">source</strong>, then click another node to set it as <strong style="color:#ef4444;">target</strong>. The tracer ball will follow the shortest path between them.`;
      }, 3000);
    };

    // Topic filtering
    const tagLabels = document.querySelectorAll('.tag-checkbox-label');
    tagLabels.forEach(lbl => {
      lbl.onclick = (e) => {
        if (e.target.tagName !== 'INPUT') {
          const input = lbl.querySelector('input');
          input.checked = !input.checked;
        }
        lbl.classList.toggle('checked', lbl.querySelector('input').checked);

        const activeTags = new Set(
          Array.from(document.querySelectorAll('.tag-checkbox-label input:checked')).map(i => i.value)
        );

        // Filter nodes & links
        const filteredNodes = globalData.nodes.filter(n => {
          if (n.type === 'tag') return activeTags.has(n.label.replace('#', ''));
          if (n.type === 'post') return n.tags.some(t => activeTags.has(t));
          return true;
        });
        const filteredNodeIds = new Set(filteredNodes.map(n => n.id));
        const filteredLinks = globalData.links.filter(l => 
          filteredNodeIds.has(l.source.id || l.source) && filteredNodeIds.has(l.target.id || l.target)
        );

        graph.setData({ nodes: filteredNodes, links: filteredLinks });
      };
    });

    // Node search highlight
    const searchInput = document.getElementById('graph-node-search');
    searchInput.oninput = (e) => {
      const q = e.target.value.toLowerCase().trim();
      if (!q) {
        graph.hoveredNode = null;
        graph.render();
        return;
      }
      const match = globalData.nodes.find(n => (n.label || n.id).toLowerCase().includes(q));
      if (match) {
        graph.hoveredNode = match;
        graph.render();
      }
    };
  }

  // 5. Tags Overview View
  async renderTagsView(container) {
    await this.store.loadIndex();
    const tags = Array.from(this.store.tagsMap.entries());

    container.innerHTML = `
      <div class="container" style="padding: 3.5rem 1rem 5rem;">
        <div class="section-header">
          <div>
            <h1 class="section-title">🏷️ Topics & Knowledge Clusters</h1>
            <p class="section-subtitle">Taxonomy of themes across all publications</p>
          </div>
        </div>

        <div class="post-grid">
          ${tags.map(([tag, posts]) => `
            <a href="#/tag/${tag}" class="post-card" style="text-decoration: none;">
              <span class="tag-badge" style="width: fit-content; margin-bottom: 0.75rem;">#${tag}</span>
              <h2 class="post-card-title">${tag.replace(/-/g, ' ').replace(/\w/g, l => l.toUpperCase())}</h2>
              <p class="post-card-excerpt">Collection of ${posts.length} article${posts.length !== 1 ? 's' : ''} on this topic.</p>
              <div class="post-card-footer">
                <span style="font-size: 0.8rem; font-weight: 600; color: var(--primary);">Explore Topic →</span>
                <span style="font-size: 0.8rem; color: var(--text-muted);">${posts.length} posts</span>
              </div>
            </a>
          `).join('')}
        </div>
      </div>
    `;
  }

  // 6. Single Tag View
  async renderSingleTagView(container, tag) {
    await this.store.loadIndex();
    const posts = this.store.tagsMap.get(tag) || [];

    container.innerHTML = `
      <div class="container" style="padding: 3.5rem 1rem 5rem;">
        <div class="section-header">
          <div>
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
              <a href="#/tags" style="font-size: 0.85rem; color: var(--text-muted);">Topics</a>
              <span style="color: var(--text-muted);">/</span>
              <span class="tag-badge active">#${tag}</span>
            </div>
            <h1 class="section-title">Posts Tagged: #${tag}</h1>
            <p class="section-subtitle">${posts.length} article${posts.length !== 1 ? 's' : ''} found in this category</p>
          </div>
          <a href="#/tags" class="btn btn-secondary btn-sm">All Topics</a>
        </div>

        <div class="post-grid">
          ${posts.map(post => this.renderPostCard(post)).join('')}
        </div>
      </div>
    `;
  }

  // 7. About View
  async renderAboutView(container) {
    container.innerHTML = '<div class="container content-wrapper" style="padding: 4rem 1rem 5rem;"><div class="prose"><p>This is an individual group website for the course Social Graphs and Interactions at DTU.</p></div></div>';
    return;

    container.innerHTML = `
      <div class="container content-wrapper" style="padding: 4rem 1rem 5rem;">
        <div style="display: flex; align-items: center; gap: 1.5rem; margin-bottom: 2.5rem;">
          <img src="assets/images/avatar.svg" alt="Robin Hildbrand" style="width: 90px; height: 90px; border-radius: 50%; box-shadow: var(--shadow-lg);">
          <div>
            <h1 style="font-size: 2.2rem; font-weight: 800; margin-bottom: 0.25rem;">Robin Hildbrand</h1>
            <p style="color: var(--primary); font-weight: 600; font-size: 1.05rem;">Researcher & Computational Graph Theorist</p>
          </div>
        </div>

        <div class="prose">
          <p>
            Welcome to my digital garden and research blog. My work sits at the intersection of <strong>Spectral Graph Theory</strong>, <strong>Graph Neural Networks</strong>, and <strong>Complex Network Dynamics</strong>.
          </p>
          <p>
            This website is built entirely from scratch with static web technologies (No Jekyll, zero build dependencies, pure HTML5/CSS3/JavaScript, D3.js, KaTeX, and Marked) to provide an uncompromising visual reading experience for networked knowledge.
          </p>

          <h2>Interactive Research Network</h2>
          <p>Below is an interactive network mapping my core research themes, methodologies, and open inquiries:</p>
          
          <div class="embedded-graph-container" id="about-skill-graph"></div>

          <h2>Key Technical Features of this Blog</h2>
          <ul>
            <li><strong>No Jekyll / Zero Build Pipeline:</strong> Pure client-side static application hosted directly on GitHub Pages with instant page transitions and SEO fallback.</li>
            <li><strong>D3 Force-Directed Graph Engine:</strong> Force-directed, alphabetical circular, and degree-based circular layouts, edge particles, zooming, dragging, and image export.</li>
            <li><strong>In-Post Graph Embedding:</strong> Write <code>\`\`\`graph</code> JSON or <code>\`\`\`network</code> DSL inside standard Markdown to render interactive figures inline.</li>
            <li><strong>Bi-directional Wikilinks:</strong> Connect posts with <code>[[post-slug]]</code> syntax and automatically generate dynamic ego-networks.</li>
            <li><strong>LaTeX Math Typesetting:</strong> Powered by KaTeX for equations.</li>
            <li><strong>Instant Command Palette Search:</strong> Hit <kbd class="kbd-shortcut">Cmd+K</kbd> to search everything in real time.</li>
          </ul>
        </div>
      </div>
    `;

    // Mount About Skill Graph
    const skillEl = document.getElementById('about-skill-graph');
    if (skillEl) {
      const skillData = {
        nodes: [
          { id: 'Robin', label: 'Robin Hildbrand', group: 'author', size: 22, color: '#6366f1' },
          { id: 'Spectral', label: 'Spectral Graph Theory', group: 'theory', size: 16, color: '#38bdf8' },
          { id: 'Laplacian', label: 'Graph Laplacians', group: 'math', size: 13, color: '#a855f7' },
          { id: 'GNN', label: 'Graph Neural Networks', group: 'algorithms', size: 16, color: '#ec4899' },
          { id: 'Diffusion', label: 'Diffusion on Networks', group: 'theory', size: 14, color: '#10b981' },
          { id: 'KG', label: 'Knowledge Graphs & LLMs', group: 'systems', size: 15, color: '#f59e0b' },
          { id: 'ComplexNet', label: 'Complex Systems', group: 'theory', size: 14, color: '#38bdf8' }
        ],
        links: [
          { source: 'Robin', target: 'Spectral', weight: 2 },
          { source: 'Robin', target: 'GNN', weight: 2 },
          { source: 'Robin', target: 'KG', weight: 2 },
          { source: 'Spectral', target: 'Laplacian', label: 'eigenvalues', directed: true },
          { source: 'Spectral', target: 'Diffusion', label: 'heat kernel', directed: true },
          { source: 'Spectral', target: 'GNN', label: 'spectral convolution', directed: true },
          { source: 'GNN', target: 'KG', label: 'relational learning', directed: true },
          { source: 'Diffusion', target: 'ComplexNet', label: 'epidemic spread', directed: true }
        ]
      };

      GraphParser.mountGraph(skillEl, skillData, {
        title: 'Robin Hildbrand — Research Map',
        enableParticles: true,
        caption: 'Core research topics, methodologies, and theoretical connections'
      });
    }
  }

  // --- Helpers ---
  renderPostCard(post) {
    const tags = Array.isArray(post.tags) ? post.tags : [];
    return `
      <a href="#/post/${post.slug}" class="post-card">
        <div class="post-card-meta">
          <span class="post-card-date">📅 ${post.date}</span>
          <span>•</span>
          <span class="post-card-time">⏱️ ${post.readTime || '5 min'}</span>
        </div>
        <h3 class="post-card-title">${post.title}</h3>
        <p class="post-card-excerpt">${post.summary || post.excerpt || ''}</p>
        <div class="post-card-footer">
          <div class="tag-list">
            ${tags.slice(0, 2).map(t => `<span class="tag-badge">#${t}</span>`).join('')}
          </div>
          <span class="post-graph-indicator">⚡ Interactive Graph</span>
        </div>
      </a>
    `;
  }

  // --- Search Modal ---
  initSearchModal() {
    const modalBackdrop = document.getElementById('search-modal');
    const searchInput = document.getElementById('search-input');
    const resultsContainer = document.getElementById('search-results');
    const triggerBtn = document.getElementById('search-trigger-btn');

    if (!modalBackdrop || !searchInput || !resultsContainer) return;

    const openModal = () => {
      modalBackdrop.classList.add('open');
      searchInput.value = '';
      resultsContainer.innerHTML = '<div style="padding: 1.5rem; text-align: center; color: var(--text-muted); font-size: 0.85rem;">Type to search posts or network entities...</div>';
      setTimeout(() => searchInput.focus(), 50);
    };

    const closeModal = () => {
      modalBackdrop.classList.remove('open');
    };

    if (triggerBtn) triggerBtn.addEventListener('click', openModal);

    modalBackdrop.addEventListener('click', (e) => {
      if (e.target === modalBackdrop) closeModal();
    });

    document.addEventListener('keydown', (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        modalBackdrop.classList.contains('open') ? closeModal() : openModal();
      }
      if (e.key === 'Escape' && modalBackdrop.classList.contains('open')) {
        closeModal();
      }
    });

    searchInput.addEventListener('input', (e) => {
      const q = e.target.value;
      const results = this.store.search(q);

      if (!q.trim()) {
        resultsContainer.innerHTML = '<div style="padding: 1.5rem; text-align: center; color: var(--text-muted); font-size: 0.85rem;">Type to search posts or network entities...</div>';
        return;
      }

      if (results.length === 0) {
        resultsContainer.innerHTML = '<div style="padding: 1.5rem; text-align: center; color: var(--text-muted); font-size: 0.85rem;">No results found for "' + q + '"</div>';
        return;
      }

      resultsContainer.innerHTML = results.map((res, i) => `
        <a href="${res.url}" class="search-result-item ${i === 0 ? 'selected' : ''}" onclick="document.getElementById('search-modal').classList.remove('open')">
          <div class="search-result-title">${res.type === 'tag' ? '🏷️' : '📄'} ${res.title}</div>
          <div class="search-result-snippet">${res.snippet}</div>
        </a>
      `).join('');
    });
  }

  initGlobalEvents() {
    // Mobile menu toggle
    const mobileBtn = document.getElementById('mobile-menu-btn');
    const mobileNav = document.getElementById('mobile-nav');
    if (mobileBtn && mobileNav) {
      mobileBtn.addEventListener('click', () => {
        mobileNav.classList.toggle('open');
      });
    }
  }
}

// Instantiate on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  window.app = new App();
});
