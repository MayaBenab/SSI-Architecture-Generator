"""The order of the refinement is a partial order (a DAG between the selected patterns). A pattern M = (R, F_R, f_R) can only
be applied once the components its R needs exist, so P must be applied before Q when Q needs a component that P adds:
P -> Q  iff  F_P ∩ R_Q ≠ ∅. The arc is labelled with that component. 'requires' (feature model) says which patterns are present, not in which order; the
script checks that it adds no precedence the anchors do not already give.
Each arc is then compared with the catalogue [1] (order_sources.json): an item of the Related Patterns of P or Q, or the
lifecycle figure (the state of P comes before the state of Q). Arcs with neither are drawn dashed.
Finally it enumerates every order of the DAG (up to a cap), applies the rules in each and checks they all give the same G_n.
usage: python 16_check_order.py [out_diploma] [--mark-catalogue]   -> order_dag.png, order_check.txt
(--mark-catalogue draws dashed the arcs the catalogue does not support; by default every arc has the same style)"""
import os, sys, json, shutil, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "lib"))
from fm import parse_uvl
from refine import refine, P, precedence, levels

MARK = "--mark-catalogue" in sys.argv; argv = [a for a in sys.argv[1:] if a != "--mark-catalogue"]
run = argv[0] if argv else os.path.join(HERE, "out_diploma")
res = json.load(open(os.path.join(run, "result.json"), encoding="utf-8"))
seq = [s.split("_")[0] for s in res["sequence"]]
names = {s.split("_")[0]: s.split("_", 1)[1].replace("_", " ") for s in res["sequence"]}
RULES = json.load(open(os.path.join(HERE, "..", "2_feature_model", "rules.json"), encoding="utf-8"))["rules"]
SRC = json.load(open(os.path.join(HERE, "..", "2_feature_model", "order_sources.json"), encoding="utf-8"))
label_of = lambda p: RULES[p]["name"] if p in RULES else names[p]
ctype = {c["id"]: c["type"] for r in RULES.values() for c in r["added"]["components"]}

# ---- the DAG (the same function the refinement uses)
anchor = precedence(seq)
edges = sorted(anchor)
lv = levels(seq, anchor)
before = {q: {p for p, q2 in edges if q2 == q} for q in seq}

def closure(es):
    reach = {p: set() for p in seq}
    changed = True
    for a, b in es: reach[a].add(b)
    while changed:
        changed = False
        for a in seq:
            new = set().union(*(reach[b] for b in reach[a])) - reach[a] if reach[a] else set()
            if new: reach[a] |= new; changed = True
    return reach
_, nodes, cons = parse_uvl(); nodes.pop("__justification__", None)
requires = {(bs[0].split("_")[0], a.split("_")[0]) for a, bs in cons
            if len(bs) == 1 and a.startswith("P") and bs[0].startswith("P")}
reach = closure(edges)
req_in = sorted((p, q) for p, q in requires if p in seq and q in seq)
req_new = [(p, q) for p, q in req_in if q not in reach[p]]

# ---- what the catalogue says about each arc
pairs = {}
for l in SRC["catalogue_links"]: pairs.setdefault(frozenset((l["p"], l["q"])), []).append(l["item"])
for a, b in SRC["variants"]: pairs.setdefault(frozenset((a, b)), []).append("variant")
nxt, pst = SRC["lifecycle_next"], SRC["pattern_states"]
def later(s, t):
    seen, stack = set(), list(nxt.get(s, []))
    while stack:
        x = stack.pop()
        if x == t: return True
        if x not in seen: seen.add(x); stack += nxt.get(x, [])
    return False
def lifecycle(p, q):
    return next((f"{s} → {t}" for s in pst.get(p, []) for t in pst.get(q, []) if later(s, t)), "")
support = {e: (pairs.get(frozenset(e), []), lifecycle(*e)) for e in edges}

# ---- every order of the DAG gives the same G_n
CAP = 5000; orders = []
def rec(done, out):
    if len(orders) >= CAP: return
    if len(out) == len(seq): orders.append(list(out)); return
    for p in seq:
        if p not in done and before[p] <= done:
            done.add(p); out.append(p); rec(done, out); out.pop(); done.remove(p)
rec(set(), [])
norm = lambda G: (sorted(G["components"].items()), sorted(G["connectors"].items()))
ref = norm(refine(seq)[0]); same = failed = 0
for o in orders:
    G, steps = refine(o)
    if any(s["status"] != "APPLIED" for s in steps): failed += 1
    elif norm(G) == ref: same += 1
rev_failed = [s["pattern"] for s in refine(list(reversed(seq)))[1] if s["status"] != "APPLIED"]

lines = [f"precedence arcs ({len(edges)}), P -> Q when Q needs a component P adds:"]
for e in edges:
    cat, lc = support[e]
    lines.append(f"  {e[0]} -> {e[1]}  needs: {', '.join(anchor[e])}"
                 f" | catalogue: {'; '.join(cat) if cat else '-'} | lifecycle: {lc or '-'}")
n_sup = sum(1 for e in edges if support[e][0] or support[e][1])
lines += ["steps: " + " | ".join(f"{k}: {', '.join(l)}" for k, l in enumerate(lv, 1)),
          f"arcs supported by the catalogue [1] (Related Patterns or lifecycle): {n_sup} of {len(edges)}",
          f"requires between selected patterns: {len(req_in)}; precedence they add beyond what the rules need: {len(req_new)} {req_new or ''}",
          f"orders respecting the DAG: {len(orders)}{' (capped)' if len(orders) >= CAP else ''}",
          f"same G_n: {same}; rule failed: {failed}; different G_n: {len(orders) - same - failed}",
          f"reversed sequence: {len(rev_failed)} rules fail ({', '.join(rev_failed)})"]
open(os.path.join(run, "order_check.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("\n".join(lines))

# ---- drawing: every arc labelled with the component Q needs and P adds; one row = one step of the DAG
short = lambda c: ctype.get(c, c).split(" (")[0].split(" +")[0]
hi = "P25"
L = ['digraph O { rankdir=TB; nodesep=0.15; ranksep=0.5; fontname=Helvetica;',
     'node [fontname=Helvetica, fontsize=22, shape=box, style="rounded,filled", fillcolor="#f7ebdd", color="#5b2a12", penwidth=1.6, margin="0.12,0.06"];',
     'edge [color="#5b2a12", penwidth=1.6, arrowsize=1.0, fontname=Helvetica, fontsize=19, fontcolor="#2e4a62"];']
for p in seq:
    extra = ', fillcolor="#fde3c4", color="#c25e0c", penwidth=3' if p == hi else ""
    L.append(f'"{p}" [label="{p}\\n{label_of(p)}"{extra}];')
for k, level in enumerate(lv, 1):
    L.append(f'"step{k}" [label="step {k}", shape=plaintext, style="", fontsize=22, fontcolor="#2e4a62"];')
    L.append("{ rank=same; " + f'"step{k}"; ' + " ".join(f'"{p}";' for p in level) + " }")
for k in range(1, len(lv)): L.append(f'"step{k}" -> "step{k + 1}" [style=invis];')
for e in edges:
    lab = "\\n".join(sorted({short(c) for c in anchor[e]}))
    st = ', style=dashed' if MARK and not (support[e][0] or support[e][1]) else ""
    L.append(f'"{e[0]}" -> "{e[1]}" [label=" {lab}"{st}];')
L.append("}")
dot = os.path.join(run, "order_dag.dot"); open(dot, "w", encoding="utf-8").write("\n".join(L))
if shutil.which("dot"):
    subprocess.run(["dot", "-Tpng", "-Gdpi=200", dot, "-o", os.path.join(run, "order_dag.png")])
    print(f"written {os.path.join(run, 'order_dag.png')}")
