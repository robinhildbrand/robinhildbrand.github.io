/**
 * Markdown Rendering Pipeline with Math (KaTeX), Wikilinks, Code Highlighting, and Graph Blocks
 */

class MarkdownProcessor {
  /**
   * Parse frontmatter from raw markdown string
   */
  static parseFrontmatter(rawMarkdown) {
    const trimmed = rawMarkdown.trim();
    if (!trimmed.startsWith('---')) {
      return { metadata: {}, content: rawMarkdown };
    }

    const fmMatch = trimmed.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n([\s\S]*)$/);
    if (!fmMatch) {
      return { metadata: {}, content: rawMarkdown };
    }

    const yamlBlock = fmMatch[1].trim();
    const content = fmMatch[2].trim();
    const metadata = {};

    yamlBlock.split(/\r?\n/).forEach(line => {
      const colonIdx = line.indexOf(':');
      if (colonIdx !== -1) {
        const key = line.substring(0, colonIdx).trim();
        let val = line.substring(colonIdx + 1).trim();

        // Handle quoted strings
        if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
          val = val.substring(1, val.length - 1);
        }
        // Handle array syntax [a, b, c]
        else if (val.startsWith('[') && val.endsWith(']')) {
          val = val.substring(1, val.length - 1).split(',').map(s => s.trim().replace(/^['"]|['"]$/g, ''));
        }
        metadata[key] = val;
      }
    });

    return { metadata, content };
  }

  /**
   * Process and render Markdown to sanitized HTML
   */
  static render(markdownContent) {
    try {
      return this._renderInternal(markdownContent);
    } catch (err) {
      console.error('MarkdownProcessor render error:', err);
      return {
        html: `<div class="callout callout-warning"><p>Failed to render markdown content: ${err.message}</p></div>`,
        headings: [],
        graphsToMount: []
      };
    }
  }

  static _renderInternal(markdownContent) {
    let processed = markdownContent;

    // 1. Preserve and protect LaTeX blocks before Marked parses them
    const mathBlocks = [];
    const mathInlines = [];

    // Replace display math $$...$$
    processed = processed.replace(/\$\$([\s\S]+?)\$\$/g, (match, math) => {
      const idx = mathBlocks.length;
      mathBlocks.push(math.trim());
      return `@@MATH_BLOCK_${idx}@@`;
    });

    // Replace inline math $...$ (ensure not preceded or followed by $)
    processed = processed.replace(/(^|[^\$])\$([^\$\r\n]+?)\$/g, (match, prefix, math) => {
      const idx = mathInlines.length;
      mathInlines.push(math.trim());
      return `${prefix}@@MATH_INLINE_${idx}@@`;
    });

    // 2. Configure Marked
    marked.setOptions({
      gfm: true,
      breaks: true,
      highlight: function(code, lang) {
        if (typeof hljs !== 'undefined') {
          const validLang = hljs.getLanguage(lang) ? lang : 'plaintext';
          try {
            return hljs.highlight(code, { language: validLang }).value;
          } catch (e) {
            return hljs.highlightAuto(code).value;
          }
        }
        return code;
      }
    });

    // Custom marked renderer for custom codeblocks (graph, network) and headers
    const renderer = new marked.Renderer();
    const graphsToMount = [];

    renderer.code = function(arg1, arg2) {
      const isObj = typeof arg1 === 'object' && arg1 !== null;
      const code = isObj ? (arg1.text || '') : (arg1 || '');
      const language = isObj ? (arg1.lang || '') : (arg2 || '');
      const lang = (language || '').toLowerCase().trim();

      // In-post JSON graph
      if (lang === 'graph') {
        const graphId = 'embed-graph-' + Math.random().toString(36).substring(2, 9);
        graphsToMount.push({ id: graphId, type: 'json', raw: code });
        return `<div class="embedded-graph-container" id="${graphId}"></div>\n`;
      }

      // In-post DSL network graph
      if (lang === 'network') {
        const graphId = 'embed-graph-' + Math.random().toString(36).substring(2, 9);
        graphsToMount.push({ id: graphId, type: 'dsl', raw: code });
        return `<div class="embedded-graph-container" id="${graphId}"></div>\n`;
      }

      // Standard highlighted code block with copy button
      const highlighted = (typeof hljs !== 'undefined')
        ? (hljs.getLanguage(lang) ? hljs.highlight(code, { language: lang }).value : hljs.highlightAuto(code).value)
        : code;

      return `
        <div class="code-block-wrapper">
          <div class="code-block-header">
            <span>${lang || 'text'}</span>
            <button class="copy-code-btn" onclick="navigator.clipboard.writeText(decodeURIComponent('${encodeURIComponent(code)}')).then(() => { this.innerText = 'Copied!'; setTimeout(() => this.innerText = 'Copy', 2000); })">Copy</button>
          </div>
          <pre><code class="hljs ${lang}">${highlighted}</code></pre>
        </div>\n
      `;
    };

    // Header with slug IDs for Table of Contents
    const headings = [];
    renderer.heading = function(arg1, arg2) {
      const isObj = typeof arg1 === 'object' && arg1 !== null;
      const text = isObj ? (arg1.text || '') : (arg1 || '');
      const level = isObj ? (arg1.depth || 1) : (arg2 || 1);
      const cleanText = String(text).replace(/<[^>]*>/g, '');
      const slug = cleanText.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
      headings.push({ text: cleanText, level, slug });
      return `<h${level} id="${slug}">${text}</h${level}>\n`;
    };

    // 3. Render HTML
    let html = marked.parse(processed, { renderer });

    // 4. Transform Wikilinks: [[post-slug|Title]] or [[post-slug]]
    html = html.replace(/\[\[([^\]\|]+)(?:\|([^\]]+))?\]\]/g, (match, targetSlug, customText) => {
      const cleanSlug = targetSlug.trim();
      const label = customText ? customText.trim() : cleanSlug.replace(/-/g, ' ');
      return `<a class="wikilink" href="#/post/${cleanSlug}" data-post-slug="${cleanSlug}">${label}</a>`;
    });

    // 5. Transform GitHub-style Alert Callouts
    html = html.replace(/<blockquote>\s*<p>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]([\s\S]*?)<\/p>([\s\S]*?)<\/blockquote>/gi, 
      (match, type, titleAndFirstLine, rest) => {
        const alertType = type.toLowerCase();
        let badge = 'NOTE';
        let cls = 'callout-note';
        if (alertType === 'tip') { badge = '💡 TIP'; cls = 'callout-tip'; }
        else if (alertType === 'warning' || alertType === 'caution') { badge = '⚠️ WARNING'; cls = 'callout-warning'; }
        else { badge = 'ℹ️ NOTE'; cls = 'callout-note'; }

        return `
          <div class="callout ${cls}">
            <div class="callout-title">${badge}</div>
            <p>${titleAndFirstLine.trim()}</p>
            ${rest || ''}
          </div>
        `;
      }
    );

    // 6. Restore Math formulas via KaTeX
    html = html.replace(/@@MATH_BLOCK_(\d+)@@/g, (match, idx) => {
      const math = mathBlocks[Number(idx)];
      if (typeof katex !== 'undefined') {
        try {
          return `<div class="katex-display">${katex.renderToString(math, { displayMode: true, throwOnError: false })}</div>`;
        } catch (e) {
          return `<div class="katex-display">$$${math}$$</div>`;
        }
      }
      return `<div class="katex-display">$$${math}$$</div>`;
    });

    html = html.replace(/@@MATH_INLINE_(\d+)@@/g, (match, idx) => {
      const math = mathInlines[Number(idx)];
      if (typeof katex !== 'undefined') {
        try {
          return katex.renderToString(math, { displayMode: false, throwOnError: false });
        } catch (e) {
          return `$${math}$`;
        }
      }
      return `$${math}$`;
    });

    // 7. Sanitize HTML
    if (typeof DOMPurify !== 'undefined') {
      html = DOMPurify.sanitize(html, {
        ADD_TAGS: ['iframe'],
        ADD_ATTR: ['src', 'width', 'height', 'style', 'title', 'class', 'loading', 'allow', 'target', 'allowfullscreen', 'frameborder', 'onclick', 'data-post-slug', 'data-action']
      });
    }

    return { html, headings, graphsToMount };
  }

  /**
   * Mount all embedded interactive graphs found during rendering
   */
  static mountGraphs(graphsToMount) {
    graphsToMount.forEach(item => {
      const el = document.getElementById(item.id);
      if (!el) return;

      let graphData = null;
      if (item.type === 'json') {
        graphData = GraphParser.parseJSON(item.raw);
      } else if (item.type === 'dsl') {
        graphData = GraphParser.parseDSL(item.raw);
      }

      if (graphData) {
        GraphParser.mountGraph(el, graphData, {
          title: 'Interactive Network',
          enableParticles: true
        });
      }
    });
  }
}

window.MarkdownProcessor = MarkdownProcessor;
