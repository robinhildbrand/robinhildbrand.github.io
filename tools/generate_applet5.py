import json
from pathlib import Path
import networkx as nx

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets/applets/infection-source.html"


def make_data():
    names, graph = {}, nx.Graph()
    with open(ROOT / "week1_nodes.tsv", encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("#") or not line.strip():
                continue
            row = line.rstrip().split("\t")
            if row[0] != "node_id":
                graph.add_node(row[0])
                names[row[0]] = row[1]
    with open(ROOT / "week1_edges.tsv", encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("#") or not line.strip():
                continue
            source, target = line.rstrip().split("\t")[:2]
            if source != target:
                graph.add_edge(source, target)
    graph = graph.subgraph(max(nx.connected_components(graph), key=len)).copy()

    def ranking(values):
        ordered = sorted(values.items(), key=lambda item: (-item[1], names[item[0]]))
        return [{"id": node, "name": names[node], "value": round(value, 6)} for node, value in ordered]

    return {
        "nodes": [{"id": node, "name": names[node], "degree": graph.degree(node)} for node in sorted(graph, key=lambda item: names[item])],
        "links": [{"source": source, "target": target} for source, target in graph.edges()],
        "rankings": {
            "closeness": ranking(nx.closeness_centrality(graph)),
            "betweenness": ranking(nx.betweenness_centrality(graph)),
            "eigenvector": ranking(nx.eigenvector_centrality(graph, max_iter=2000)),
        },
        "stats": {"nodes": graph.number_of_nodes(), "edges": graph.number_of_edges()},
    }


HTML = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Choose the Infection Source</title>
<style>
:root{color-scheme:dark;--bg:#0a0a1a;--fg:#e0e0e0;--header:#fff;--muted:#777;--badge-bg:#1e1e3a;--badge-border:#2a2a44;--badge-fg:#bbb;--hl:#fbbf24;--panel:#111;--panel-border:#222;--edge:#343451;--node:#5e81ac;--node-hot:#fbbf24;--btn-bg:#16162a;--btn-border:#2a2a44;--btn-fg:#bbb;--btn-hover:#20203a;--btn-hover-fg:#fff;--ref-fg:#555}
*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--fg);min-height:100vh;overflow-y:auto;padding:1rem}main{width:100%;max-width:1180px;margin:auto}h1{font-family:'Bangers','Impact','Arial Black',sans-serif;font-size:2rem;font-weight:400;font-style:italic;letter-spacing:.06em;color:var(--header);text-transform:uppercase;text-align:center;line-height:1.1;text-shadow:0 3px 0 #02020a}.sub{font-size:.88rem;color:var(--muted);margin:.3rem auto .9rem;text-align:center;max-width:720px;line-height:1.4}.hud{display:flex;gap:1.2rem;align-items:center;flex-wrap:wrap;justify-content:center;margin-bottom:.9rem;font-size:.84rem}.badge{font-family:'Bangers','Impact','Arial Black',sans-serif;background:var(--badge-bg);border:2px solid var(--badge-border);border-radius:6px;padding:.3rem .8rem;color:var(--badge-fg);font-weight:400;letter-spacing:.04em}.badge .hl{color:var(--hl)}.layout{display:grid;grid-template-columns:minmax(0,1fr) 280px;gap:1rem;align-items:start}.panel{background:var(--panel);border:2px solid var(--panel-border);border-radius:10px;padding:.7rem}.panel-title{font-family:'Bangers','Impact','Arial Black',sans-serif;letter-spacing:.04em;color:var(--header);font-size:1.15rem;font-weight:400}.panel-sub{color:var(--muted);font-size:.72rem;margin:.15rem 0 .55rem}.stage-head{display:flex;justify-content:space-between;align-items:center;gap:.5rem;border-bottom:1px solid var(--panel-border);padding:.1rem .2rem .55rem}.hint{font-size:.65rem;color:var(--muted);text-align:right}#network{display:block;width:100%;aspect-ratio:1.55;min-height:360px;background:#0d0d20;border-radius:6px;margin-top:.55rem}.edge{stroke:var(--edge);stroke-opacity:.55;stroke-width:1}.node{stroke:#0a0a1a;stroke-width:1.4;cursor:pointer}.node:hover{stroke:#fff;stroke-width:2.5}.node.source{stroke:var(--hl);stroke-width:4}.node.infected{fill:var(--node-hot)!important}.message{min-height:1.2rem;color:var(--hl);font-size:.75rem;text-align:center;margin:.45rem 0 .2rem;font-weight:500}.toolbar{display:flex;gap:.55rem;align-items:center;flex-wrap:wrap}.btn,.tab{background:var(--btn-bg);color:var(--btn-fg);border:1px solid var(--btn-border);border-radius:6px;padding:.35rem .75rem;font-size:.72rem;cursor:pointer;font-weight:600}.btn:hover,.tab:hover{background:var(--btn-hover);color:var(--btn-hover-fg)}.btn.primary{background:#b91c1c;border-color:#b91c1c;color:#fff}.btn.primary:hover{background:#991b1b}.btn:disabled{opacity:.35;cursor:default}.status{color:var(--muted);font-size:.68rem;margin-left:auto}.tabs{display:flex;gap:.3rem;flex-wrap:wrap;margin:.55rem 0}.tab{padding:.3rem .5rem}.tab.active{background:var(--hl);border-color:var(--hl);color:#111}.search{width:100%;background:var(--btn-bg);color:var(--fg);border:1px solid var(--btn-border);border-radius:6px;padding:.4rem .5rem;font-size:.72rem}.rank-row{display:grid;grid-template-columns:20px 1fr 42px;align-items:center;gap:.35rem;width:100%;padding:.38rem 0;border:0;border-bottom:1px solid var(--panel-border);background:none;text-align:left;color:var(--fg);cursor:pointer;font-size:.68rem}.rank-row:hover{color:#fff}.rank-row em{font-style:normal;color:var(--muted);text-align:right}.bar{display:block;height:3px;background:#24243b;border-radius:3px;margin-top:3px;overflow:hidden}.bar i{display:block;height:100%;background:var(--node)}.rank-row:first-child .bar i{background:var(--hl)}.foot,.ref{color:var(--ref-fg);font-size:.6rem;line-height:1.35;margin-top:.6rem}.ref{text-align:center}@media(max-width:760px){body{padding:.75rem}.layout{grid-template-columns:1fr}#network{min-height:300px}.status{width:100%;margin-left:0}.panel{padding:.55rem}}
</style>
</head>
<body><main>
<h1>Where Should the Infection Begin?</h1>
<p class="sub">Choose one character in the giant component. Every infected character passes the disease to all neighbors in the next round. Reach everyone as fast as possible.</p>
<div class="hud"><div class="badge">Heroes <span class="hl" id="node-count"></span></div><div class="badge">Links <span class="hl" id="edge-count"></span></div><div class="badge">Rounds <span class="hl" id="round-count">-</span></div></div>
<div class="layout"><section class="panel"><div class="stage-head"><strong class="panel-title" id="stage-title">Select a source</strong><span class="hint">Click a node to inspect it</span></div><svg id="network" viewBox="0 0 900 580" role="img" aria-label="Marvel character network"></svg><div class="message" id="message">The best source is not necessarily the most famous character.</div><div class="toolbar"><button class="btn primary" id="start" disabled>Start spread</button><button class="btn" id="reset">Reset</button><span class="status" id="status">Choose a node.</span></div></section><aside class="panel"><h2 class="panel-title">Centrality shortlist</h2><p class="panel-sub">Use the rankings as clues, then test your own hunch.</p><div class="tabs"><button class="tab active" data-metric="closeness">Closeness</button><button class="tab" data-metric="betweenness">Betweenness</button><button class="tab" data-metric="eigenvector">Eigenvector</button></div><input class="search" id="search" type="search" placeholder="Filter characters..."><div id="ranking-list"></div><p class="foot">Click a ranked character to select it. Metrics use the giant component; the simulation uses synchronous rounds.</p></aside></div><p class="ref">Network data: Marvel Comics Wikipedia &middot; giant component of the 303-character snapshot</p>
</main>
<script>const D=__DATA__,S=document.getElementById('network'),N=D.nodes,A=new Map(N.map(n=>[n.id,[]])),P=new Map(),C=new Map();D.links.forEach(e=>{A.get(e.source).push(e.target);A.get(e.target).push(e.source)});document.getElementById('node-count').textContent=D.stats.nodes;document.getElementById('edge-count').textContent=D.stats.edges;const M=Math.max(...N.map(n=>n.degree));N.forEach((n,i)=>{const a=i*2.4,r=70+Math.sqrt(i/N.length)*220;P.set(n.id,{x:450+Math.cos(a)*r,y:290+Math.sin(a)*r*.78})});D.links.forEach(e=>{const a=P.get(e.source),b=P.get(e.target),x=document.createElementNS('http://www.w3.org/2000/svg','line');x.setAttribute('x1',a.x);x.setAttribute('y1',a.y);x.setAttribute('x2',b.x);x.setAttribute('y2',b.y);x.setAttribute('class','edge');S.append(x)});const g=document.createElementNS('http://www.w3.org/2000/svg','g');S.append(g);let selected=null,busy=false;N.forEach(n=>{const p=P.get(n.id),x=document.createElementNS('http://www.w3.org/2000/svg','circle');x.setAttribute('cx',p.x);x.setAttribute('cy',p.y);x.setAttribute('r',3+Math.sqrt(n.degree/M)*7);x.setAttribute('fill',`hsl(${195-n.degree/M*165} 57% ${48+n.degree/M*12}%)`);x.setAttribute('class','node');x.setAttribute('aria-label',n.name);x.onclick=()=>choose(n.id);g.append(x);C.set(n.id,x)});function choose(id){if(busy)return;selected=id;C.forEach((x,k)=>x.classList.toggle('source',k===id));const n=N.find(x=>x.id===id);document.getElementById('stage-title').textContent=n.name+' is selected';document.getElementById('start').disabled=false;document.getElementById('status').textContent=n.degree+' direct connections';document.getElementById('message').textContent='Ready? Start the spread and watch the frontier expand.'}function reset(){busy=false;C.forEach(x=>x.classList.remove('infected'));document.getElementById('round-count').textContent='-';document.getElementById('start').disabled=!selected}function spread(){if(!selected||busy)return;busy=true;let infected=new Set([selected]),front=new Set([selected]),round=0;document.getElementById('start').disabled=true;function tick(){front.forEach(id=>C.get(id).classList.add('infected'));document.getElementById('round-count').textContent=round;document.getElementById('status').textContent=infected.size+' / '+N.length+' infected';if(infected.size===N.length){busy=false;document.getElementById('message').textContent='Complete in '+round+' rounds. Compare that with the rankings.';return}const next=new Set;front.forEach(id=>A.get(id).forEach(x=>{if(!infected.has(x))next.add(x)}));next.forEach(x=>infected.add(x));front=next;round++;setTimeout(tick,110)}tick()}document.getElementById('start').onclick=spread;document.getElementById('reset').onclick=reset;let metric='closeness';function rankings(){const q=document.getElementById('search').value.toLowerCase(),rows=D.rankings[metric].filter(x=>x.name.toLowerCase().includes(q)).slice(0,12),m=D.rankings[metric][0].value;document.getElementById('ranking-list').innerHTML=rows.map((x,i)=>'<button class="rank-row" data-id="'+x.id+'"><span>'+(i+1)+'</span><span>'+x.name+'<i class="bar"><i style="width:'+x.value/m*100+'%"></i></i></span><em>'+x.value.toFixed(3)+'</em></button>').join('');document.querySelectorAll('.rank-row').forEach(x=>x.onclick=()=>choose(x.dataset.id))}document.querySelectorAll('.tab').forEach(x=>x.onclick=()=>{document.querySelectorAll('.tab').forEach(y=>y.classList.remove('active'));x.classList.add('active');metric=x.dataset.metric;rankings()});document.getElementById('search').oninput=rankings;rankings();</script>
</body></html>'''


def enhance(html):
    html = html.replace(
        '</style>',
        '.transmission{display:flex;align-items:center;gap:.45rem}.transmission input{width:84px;accent-color:var(--hl)}.rate-value{color:var(--hl);min-width:2.4rem}</style>',
        1,
    )
    html = html.replace(
        '<div class="hud"><div class="badge">Heroes',
        '<div class="hud"><div class="badge transmission">Transmission <input id="transmission-rate" type="range" min="0" max="100" value="100"><span class="rate-value" id="rate-value">100%</span></div><div class="badge">Heroes',
        1,
    )
    old_start = "document.getElementById('start').onclick=spread;"
    new_start = """function spreadWithRate(){if(!selected||busy)return;busy=true;let rate=Number(document.getElementById('transmission-rate').value)/100,infected=new Set([selected]),front=new Set([selected]),round=0;document.getElementById('start').disabled=true;function tick(){front.forEach(id=>C.get(id).classList.add('infected'));document.getElementById('round-count').textContent=round;document.getElementById('status').textContent=infected.size+' / '+N.length+' infected';if(infected.size===N.length){busy=false;document.getElementById('message').textContent='Complete in '+round+' rounds at p = '+rate.toFixed(2)+'. Try another source or rate.';return}const next=new Set;front.forEach(id=>A.get(id).forEach(x=>{if(!infected.has(x)&&Math.random()<rate)next.add(x)}));if(!next.size){busy=false;document.getElementById('message').textContent='The spread stalled at '+infected.size+' of '+N.length+' characters. Increase p or try again.';return}next.forEach(x=>infected.add(x));front=next;round++;setTimeout(tick,110)}tick()}document.getElementById('start').onclick=spreadWithRate;document.getElementById('transmission-rate').oninput=e=>{document.getElementById('rate-value').textContent=e.target.value+'%';if(!busy)document.getElementById('message').textContent='Ready at p = '+(Number(e.target.value)/100).toFixed(2)+'. Start the spread and compare sources.'};"""
    return html.replace(old_start, new_start, 1)


if __name__ == '__main__':
    generated = HTML.replace('__DATA__', json.dumps(make_data(), separators=(',', ':')))
    OUT.write_text(enhance(generated), encoding='utf-8')
    print(f'Wrote {OUT}')
