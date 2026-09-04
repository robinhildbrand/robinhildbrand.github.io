/**
 * Posts Data Store & Knowledge Graph Indexer
 * Manages post loading, caching, wikilink resolution, and graph synthesis
 */

class PostsStore {
  constructor() {
    this.posts = [];
    this.postContentCache = new Map();
    this.tagsMap = new Map(); // tag -> array of posts
    this.globalGraphData = { nodes: [], links: [] };
    this.isLoaded = false;
  }

  /**
   * Load post manifest (posts/index.json)
   */
  async loadIndex() {
    if (this.isLoaded) return this.posts;

    try {
      const response = await fetch('posts/index.json');
      if (response.ok) {
        this.posts = await response.json();
      } else {
        console.warn('posts/index.json not found, using fallback index');
        this.posts = this.getFallbackIndex();
      }
    } catch (e) {
      console.warn('Error loading posts/index.json:', e);
      this.posts = this.getFallbackIndex();
    }

    // Index tags
    this.tagsMap.clear();
    this.posts.forEach(post => {
      const tags = Array.isArray(post.tags) ? post.tags : (post.tags ? [post.tags] : []);
      tags.forEach(tag => {
        const cleanTag = tag.trim();
        if (!this.tagsMap.has(cleanTag)) {
          this.tagsMap.set(cleanTag, []);
        }
        this.tagsMap.get(cleanTag).push(post);
      });
    });

    try {
      const [nodesResponse, edgesResponse] = await Promise.all([
        fetch('week1_nodes.tsv'),
        fetch('week1_edges.tsv')
      ]);
      if (!nodesResponse.ok || !edgesResponse.ok) throw new Error('Graph dataset could not be loaded');

      const nodeData = GraphParser.parseTSV(await nodesResponse.text(), 'nodes');
      const edgeData = GraphParser.parseTSV(await edgesResponse.text(), 'edges');
      this.globalGraphData = {
        nodes: nodeData.nodes,
        links: edgeData.links
      };
    } catch (e) {
      console.error('Error loading the Marvel knowledge graph:', e);
    }

    this.isLoaded = true;
    return this.posts;
  }

  /**
   * Fetch markdown content for a single post
   */
  async getPostBySlug(slug) {
    await this.loadIndex();
    const postMeta = this.posts.find(p => p.slug === slug);
    if (!postMeta) return null;

    if (this.postContentCache.has(slug)) {
      return { ...postMeta, rawContent: this.postContentCache.get(slug) };
    }

    try {
      const fileUrl = postMeta.file || `posts/${slug}.md`;
      const response = await fetch(fileUrl);
      if (response.ok) {
        const rawContent = await response.text();
        this.postContentCache.set(slug, rawContent);
        return { ...postMeta, rawContent };
      }
    } catch (e) {
      console.error(`Error fetching post markdown for ${slug}:`, e);
    }

    return postMeta;
  }

  /**
   * Build the complete global knowledge graph (Posts + Tags + Wikilinks)
   */
  getGlobalGraphData() {
    if (this.globalGraphData.nodes.length > 0) {
      return {
        nodes: this.globalGraphData.nodes.map(node => ({ ...node })),
        links: this.globalGraphData.links.map(link => ({ ...link }))
      };
    }

    const nodes = [];
    const links = [];
    const nodeIds = new Set();

    // 1. Add post nodes
    this.posts.forEach(post => {
      const id = `post:${post.slug}`;
      nodeIds.add(id);
      nodes.push({
        id: id,
        slug: post.slug,
        type: 'post',
        label: post.title,
        group: 'article',
        size: 16,
        color: '#6366f1',
        description: post.summary || post.excerpt || '',
        date: post.date,
        tags: post.tags || []
      });
    });

    // 2. Add tag hub nodes and connect to posts
    this.tagsMap.forEach((taggedPosts, tag) => {
      const tagId = `tag:${tag}`;
      if (!nodeIds.has(tagId)) {
        nodeIds.add(tagId);
        nodes.push({
          id: tagId,
          type: 'tag',
          label: `#${tag}`,
          group: 'tag',
          size: Math.min(18, 8 + taggedPosts.length * 2),
          color: '#f59e0b',
          description: `Topic category with ${taggedPosts.length} post${taggedPosts.length !== 1 ? 's' : ''}`
        });
      }

      taggedPosts.forEach(post => {
        links.push({
          source: `post:${post.slug}`,
          target: tagId,
          weight: 1.2,
          directed: false,
          color: 'rgba(245, 158, 11, 0.4)'
        });
      });
    });

    // 3. Add explicit wikilinks between posts
    this.posts.forEach(post => {
      if (Array.isArray(post.wikilinks)) {
        post.wikilinks.forEach(targetSlug => {
          const targetPost = this.posts.find(p => p.slug === targetSlug);
          if (targetPost) {
            links.push({
              source: `post:${post.slug}`,
              target: `post:${targetPost.slug}`,
              weight: 2.2,
              directed: true,
              color: '#38bdf8',
              label: 'references'
            });
          }
        });
      }
    });

    return { nodes, links };
  }

  /**
   * Build local ego-network for a single post view
   */
  getLocalGraphForPost(slug) {
    const post = this.posts.find(p => p.slug === slug);
    if (!post) return { nodes: [], links: [] };

    const nodes = [];
    const links = [];
    const nodeIds = new Set();

    // Center node (Current post)
    const centerId = `post:${post.slug}`;
    nodeIds.add(centerId);
    nodes.push({
      id: centerId,
      slug: post.slug,
      type: 'post',
      label: post.title,
      group: 'article',
      size: 20,
      color: '#38bdf8',
      description: 'Current Article'
    });

    // Related tags
    const tags = Array.isArray(post.tags) ? post.tags : [];
    tags.forEach(tag => {
      const tagId = `tag:${tag}`;
      if (!nodeIds.has(tagId)) {
        nodeIds.add(tagId);
        nodes.push({
          id: tagId,
          type: 'tag',
          label: `#${tag}`,
          group: 'tag',
          size: 10,
          color: '#f59e0b'
        });
      }
      links.push({
        source: centerId,
        target: tagId,
        weight: 1.5,
        color: 'rgba(245, 158, 11, 0.5)'
      });

      // Add 1-2 sibling posts under the same tag
      const siblings = (this.tagsMap.get(tag) || []).filter(p => p.slug !== slug);
      siblings.slice(0, 3).forEach(sib => {
        const sibId = `post:${sib.slug}`;
        if (!nodeIds.has(sibId)) {
          nodeIds.add(sibId);
          nodes.push({
            id: sibId,
            slug: sib.slug,
            type: 'post',
            label: sib.title,
            group: 'article',
            size: 12,
            color: '#6366f1'
          });
        }
        links.push({
          source: tagId,
          target: sibId,
          weight: 1.0,
          color: 'rgba(99, 102, 241, 0.3)'
        });
      });
    });

    // Direct Wikilinks
    if (Array.isArray(post.wikilinks)) {
      post.wikilinks.forEach(targetSlug => {
        const targetPost = this.posts.find(p => p.slug === targetSlug);
        if (targetPost) {
          const tId = `post:${targetPost.slug}`;
          if (!nodeIds.has(tId)) {
            nodeIds.add(tId);
            nodes.push({
              id: tId,
              slug: targetPost.slug,
              type: 'post',
              label: targetPost.title,
              group: 'article',
              size: 14,
              color: '#a855f7'
            });
          }
          links.push({
            source: centerId,
            target: tId,
            weight: 2.5,
            directed: true,
            color: '#38bdf8',
            label: 'links to'
          });
        }
      });
    }

    return { nodes, links };
  }

  /**
   * Search posts and knowledge entities
   */
  search(query) {
    if (!query || !query.trim()) return [];
    const q = query.toLowerCase().trim();

    const results = [];

    this.posts.forEach(post => {
      let score = 0;
      if (post.title.toLowerCase().includes(q)) score += 10;
      if (post.summary && post.summary.toLowerCase().includes(q)) score += 5;
      if (post.tags && post.tags.some(t => t.toLowerCase().includes(q))) score += 4;
      if (post.slug.toLowerCase().includes(q)) score += 2;

      if (score > 0) {
        results.push({
          type: 'post',
          id: post.slug,
          title: post.title,
          url: `#/post/${post.slug}`,
          snippet: post.summary || post.excerpt || '',
          tags: post.tags || [],
          score
        });
      }
    });

    // Match tags
    this.tagsMap.forEach((posts, tag) => {
      if (tag.toLowerCase().includes(q)) {
        results.push({
          type: 'tag',
          id: tag,
          title: `#${tag}`,
          url: `#/tag/${tag}`,
          snippet: `Topic with ${posts.length} articles`,
          score: 8
        });
      }
    });

    return results.sort((a, b) => b.score - a.score);
  }

  getFallbackIndex() {
    return [
      {
        slug: 'exploring-degrees-marvel-dataset',
        title: 'Exploring Degrees in the Marvel Dataset',
        date: '2026-09-04',
        author: 'Robin Hildbrand',
        readTime: '8 min read',
        tags: ['marvel', 'network-analysis', 'degree-distribution', 'complex-networks'],
        summary: 'An empirical analysis of node degrees, in/out-degree asymmetries, power-law distributions, and central superhero hubs across the Wikipedia Marvel Comics network.',
        wikilinks: [],
        file: 'posts/exploring-degrees-marvel-dataset.md'
      }
    ];
  }
}

window.PostsStore = PostsStore;
