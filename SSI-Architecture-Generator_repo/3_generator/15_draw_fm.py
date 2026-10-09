"""Draw the feature model of a request as a feature tree (notation of Czarnecki et al.; Benavides et al. 2010), from FM_SSI.uvl and
result.json only.
usage: python 15_draw_fm.py [out_diploma]   (no argument: the run written by 10_generate.py without arguments) -> out_diploma/fm.png

The tree is FM_SSI.uvl seen from the request: SSI_system, its two mandatory subtrees, the 15 functions the request needs
(requested ones in bold; the 19 others folded in one grey box) and the 6 categories of the catalogue; under each category, the
patterns these functions require, their alternatives and prerequisites (the others counted, e.g. "2 of 9 shown"; a category
the request does not use is folded in grey). The NFR are attributes of the pattern features (extended feature model,
Benavides et al. 2010): each pattern shows its score on the requested NFR, e.g. P25 [+2, +1] for [NFR04, NFR07].
Filled circle = mandatory child, empty circle = optional child. Blue = pattern selected by the solver, white = allowed but not
selected. The cross-tree constraints that link the features shown are written to out_diploma/fm_constraints.txt."""
import json, os, re, subprocess, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "lib"))
from fm import parse_uvl

run = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out_diploma")
res = json.load(open(os.path.join(run, "result.json"), encoding="utf-8"))
root, nodes, cons = parse_uvl(); nodes.pop("__justification__", None)
need = set(res["required_functions"]); asked = {n for n in need if n.split("_")[0] in res["request"]["FR"]}
chosen = set(res.get("selection", []))

# features shown: the functions the request needs, the patterns they require (one or one of several), their prerequisites
single = [(a, bs[0]) for a, bs in cons if len(bs) == 1]
fr_p = [(a, b) for a, b in single if a in need and re.match(r"P\d\d_", b)]
fr_any = [(a, bs) for a, bs in cons if len(bs) > 1 and a in need]
p_q = [(a, b) for a, b in single if re.match(r"P\d\d_", a) and re.match(r"P\d\d_", b)]
pats = {b for _, b in fr_p} | {b for _, bs in fr_any for b in bs}
changed = True
while changed:
    changed = False
    for a, b in p_q:
        if a in pats and b not in pats: pats.add(b); changed = True
cats = [c["name"] for c in nodes["Patterns"]["children"]]            # the 6 categories, used or not
nfr_req = res["request"]["NFR"]
all_fr = [k["name"] for k in nodes["Functions"]["children"]]


def label(n):
    pid, name = n.split("_", 1)
    return pid + "  " + name.replace("_", " ")


def html_label(p):
    """pattern feature with its attributes on the requested NFR (0 when the knowledge base gives no effect)."""
    at = nodes[p]["attrs"]
    sc = ", ".join(f"{at.get(q.lower(), 0):+d}".replace("+0", "0") for q in nfr_req)
    return f'<{label(p)}&nbsp;&nbsp;<FONT POINT-SIZE="18" COLOR="#374151">[{sc}]</FONT>>'


def sh_list(names):
    ids = [n.split("_")[0] for n in names]
    return ", ".join(ids) if len(ids) <= 3 else ", ".join(ids[:2]) + " … " + ids[-1]


L = ['digraph FM { rankdir=LR; splines=line; nodesep=0.08; ranksep=0.3; newrank=true; fontname=Helvetica;',
     'node [fontname=Helvetica, fontsize=20, shape=box, style="filled", fillcolor="white", color="#5b2a12", penwidth=1.2, margin="0.05,0.03"];',
     'edge [color="#5b2a12", penwidth=1.2, arrowsize=0.9, dir=forward];',
     'SSI_system [label="SSI_system", fillcolor="#5b2a12", fontcolor="white", fontsize=22];',
     'Functions [fillcolor="#f3f4f6", color="#374151", fontsize=21]; Patterns [fillcolor="#f7ebdd", fontsize=21];',
     # Functions to the left of the root, Patterns to the right: the two subtrees side by side
     'Functions -> SSI_system [dir=back, arrowtail=dot, tailport=e, headport=w]; SSI_system -> Patterns [arrowhead=dot, tailport=e, headport=w];']
order_fr = sorted(need, key=lambda f: (f not in asked, f))        # the 15 functions the request needs
for f in order_fr:
    L.append(f'"{f}" [label="{label(f)}", width=4.2, fillcolor="#f3f4f6", color="#374151", penwidth={2.6 if f in asked else 1.0}, '
             f'fontname="{"Helvetica-Bold" if f in asked else "Helvetica"}"];')
    L.append(f'"{f}" -> Functions [dir=back, arrowtail=odot, tailport=e, headport=w];')
others = [f for f in all_fr if f not in need]
L.append(f'"other_FR" [label="{len(others)} other functions, not needed\\n({sh_list(others)})", width=4.2, style="dashed", '
         f'color="#b8a89a", fontcolor="#6b7280", fontsize=17];')
L.append('"other_FR" -> Functions [dir=back, arrowtail=odot, tailport=e, headport=w, color="#b8a89a"];')
for c in cats:
    kids = [k["name"] for k in nodes[c]["children"]]; shown = [k for k in kids if k in pats]
    name = c.replace("_", " ")
    if shown:
        L.append(f'"{c}" [label="{name}  (or)\\n{len(shown)} of {len(kids)} shown", width=2.6, style="dashed", fontname="Helvetica-Oblique", color="#b8a89a", fontsize=18];')
    else:
        L.append(f'"{c}" [label="{name}  ({sh_list(kids)})\\nnot needed", width=2.6, style="dashed", fontname="Helvetica-Oblique", '
                 f'color="#b8a89a", fontcolor="#6b7280", fontsize=16];')
    L.append(f'Patterns -> "{c}" [arrowhead=odot, tailport=e, headport=w];')
    for k in nodes[c]["children"]:
        p = k["name"]
        if p not in pats: continue
        sel = p in chosen
        L.append(f'"{p}" [label={html_label(p)}, width=4.0, fillcolor="{"#f7ebdd" if sel else "white"}", color="{"#5b2a12" if sel else "#b8a89a"}", '
                 f'fontcolor="{"#111827" if sel else "#6b7280"}", penwidth={2.4 if sel else 1.0}];')
        L.append(f'"{c}" -> "{p}" [arrowhead=none, tailport=e, headport=w];')   # or-group: no circle, at least one

# cross-tree constraints, listed under the tree as in the literature
sh = lambda n: n.split("_")[0]
lines = []
lines += [f"{sh(a)} ⇒ {' ∨ '.join(sh(b) for b in bs)}" for a, bs in fr_any]
lines += [f"{sh(a)} ⇒ {sh(b)}" for a, b in fr_p]
lines += [f"{sh(a)} ⇒ {sh(b)}" for a, b in p_q if a in pats and b in pats]
open(os.path.join(run, "fm_constraints.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
legend = ("●  mandatory     ○  optional     bold: requested     filled, thick border: selected pattern     white: allowed, not selected     "
          f"dashed: category (abstract, or-group: at least one pattern)     [{', '.join(nfr_req)}]: attributes, score of the pattern on the requested NFR")
legend = legend.replace("     dashed:", "\\ldashed:")
L.append(f'label="{legend}\\l"; labelloc=b; labeljust=l; fontsize=18;')
L.append("}")
out = os.path.join(run, "fm.dot"); open(out, "w", encoding="utf-8").write("\n".join(L))
if shutil.which("dot"):
    subprocess.run(["dot", "-Tpng", "-Gdpi=200", out, "-o", os.path.join(run, "fm.png")])
    print(f"written {os.path.join(run, 'fm.png')}: feature tree with the {len(order_fr)} functions needed (+{len(others)} folded), {len(cats)} categories, "
          f"{len(pats)} of the {sum(len(nodes[c]['children']) for c in cats)} patterns ({len(chosen & pats)} selected), attributes on {', '.join(nfr_req)}; "
          f"{len(lines)} cross-tree constraints in fm_constraints.txt")
else:
    print(f"written {out} (install Graphviz for the PNG)")
