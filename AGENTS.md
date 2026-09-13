# Project Conventions

## Terminology: heavy-tailed, not scale-free

Never describe an *observed* degree distribution (in particular the Marvel
character network) as "scale-free" or "follows a power law".

- **Heavy-tailed**: the tail decays slower than a random (Poisson) network's.
  This is what the Marvel data show. Use *heavy-tail* / *heavy-tailed*.
- **Scale-free / power law**: one *specific* kind of heavy tail, P(k) ~ k^-gamma.
  It is a strong, model-level claim that requires formal statistical testing
  and far more data than 303 nodes.
- The **Barabási–Albert** model *is* scale-free by construction (its degree
  distribution tends to a power law in the infinite-size limit) and may be
  described as such — but only about the model, never about the real dataset.

Apply this to article text, frontmatter summaries/tags, and code/data comments.

## Build / verify

- Regenerate `posts/index.json` from the markdown frontmatter:
  `python3 tools/build_index.py`
- Applet 1 and 2 are hand-edited HTML in `assets/applets/`.
- Applet 3 is generated: `python3 tools/generate_applet3.py`
  (writes `assets/applets/network-models-comparison.html` +
  `assets/model_comparison.json`).
- No `node` runtime on this machine. Validate applet JS syntax with:
  `/System/Library/Frameworks/JavaScriptCore.framework/Versions/A/Helpers/jsc`