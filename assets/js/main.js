/**
 * Main Academic Blog Script
 * Handles theme toggling, table of contents scrollspy, and code block utilities.
 */

(function () {
  'use strict';

  // --- Theme Management ---
  const THEME_KEY = 'academic_blog_theme';
  const themeToggleBtn = document.getElementById('theme-toggle');

  function getPreferredTheme() {
    const savedTheme = localStorage.getItem(THEME_KEY);
    if (savedTheme) {
      return savedTheme;
    }
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(THEME_KEY, theme);
    // Dispatch custom event so graph renderers can adjust colors
    window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme } }));
  }

  // Initialize theme
  setTheme(getPreferredTheme());

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', function () {
      const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
      const newTheme = currentTheme === 'light' ? 'dark' : 'light';
      setTheme(newTheme);
    });
  }

  // --- Table of Contents Generation & Scrollspy ---
  document.addEventListener('DOMContentLoaded', function () {
    const articleBody = document.getElementById('article-body');
    const tocNav = document.getElementById('article-toc');

    if (articleBody && tocNav) {
      const headings = articleBody.querySelectorAll('h2, h3');
      if (headings.length > 0) {
        const ul = document.createElement('ul');

        headings.forEach(function (heading, index) {
          if (!heading.id) {
            heading.id = 'section-' + (index + 1) + '-' + heading.textContent.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-');
          }

          const li = document.createElement('li');
          if (heading.tagName.toLowerCase() === 'h3') {
            li.classList.add('toc-h3');
          }

          const a = document.createElement('a');
          a.href = '#' + heading.id;
          a.textContent = heading.textContent.replace(/^#+\s*/, '');
          li.appendChild(a);
          ul.appendChild(li);
        });

        tocNav.appendChild(ul);

        // Scrollspy
        const tocLinks = tocNav.querySelectorAll('a');
        const observer = new IntersectionObserver(
          function (entries) {
            entries.forEach(function (entry) {
              if (entry.isIntersecting) {
                const id = entry.target.getAttribute('id');
                tocLinks.forEach(function (link) {
                  if (link.getAttribute('href') === '#' + id) {
                    link.classList.add('active');
                  } else {
                    link.classList.remove('active');
                  }
                });
              }
            });
          },
          { rootMargin: '-80px 0px -60% 0px' }
        );

        headings.forEach(function (heading) {
          observer.observe(heading);
        });
      } else {
        const sidebar = document.getElementById('toc-sidebar');
        if (sidebar) sidebar.style.display = 'none';
      }
    }

    // --- Add Copy Button to Code Blocks ---
    document.querySelectorAll('pre').forEach(function (pre) {
      // Don't add to graph blocks
      if (pre.closest('.network-graph-block') || pre.closest('.function-plot-block') || pre.closest('.plotly-block')) {
        return;
      }

      const wrapper = document.createElement('div');
      wrapper.className = 'code-block-wrapper';

      const header = document.createElement('div');
      header.className = 'code-header-bar';

      const langSpan = document.createElement('span');
      const code = pre.querySelector('code');
      let lang = 'code';
      if (code) {
        const classes = code.className.split(' ');
        for (let c of classes) {
          if (c.startsWith('language-')) {
            lang = c.replace('language-', '');
            break;
          }
        }
      }
      langSpan.textContent = lang.toUpperCase();

      const copyBtn = document.createElement('button');
      copyBtn.className = 'copy-code-btn';
      copyBtn.textContent = 'Copy';
      copyBtn.addEventListener('click', function () {
        const text = pre.textContent;
        navigator.clipboard.writeText(text).then(function () {
          copyBtn.textContent = 'Copied!';
          setTimeout(function () {
            copyBtn.textContent = 'Copy';
          }, 2000);
        });
      });

      header.appendChild(langSpan);
      header.appendChild(copyBtn);

      pre.parentNode.insertBefore(wrapper, pre);
      wrapper.appendChild(header);
      wrapper.appendChild(pre);
    });
  });
})();

// Global BibTeX Copy
window.copyBibtex = function () {
  const code = document.getElementById('bibtex-block');
  const btn = document.querySelector('.copy-bibtex-btn');
  if (code) {
    navigator.clipboard.writeText(code.innerText.trim()).then(function () {
      if (btn) {
        btn.innerText = 'Copied!';
        setTimeout(function () {
          btn.innerText = 'Copy BibTeX';
        }, 2000);
      }
    });
  }
};
