"""Draw the part of FM_SSI.uvl a request uses, with the solver's selection marked (Graphviz). Read from FM_SSI.uvl and result.json only.
usage: python 15_draw_fm.py [out_diploma]   (no argument: the run written by 10_generate.py without arguments) -> out_diploma/fm.png

Shown: the functions the request needs (the requested ones in bold, the others added by depends), the patterns they require
(F => P), the alternatives they need one of (F => (P1 | ... | Pn)), the prerequisites of those patterns (P => Q), and on each
pattern its attributes for the requested NFR. Filled = selected by the solver; white = allowed but not selected.
Optional complements (optional_patterns) are not drawn."""
import json, os, re, subprocess, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "lib"))
from fm import parse_uvl

run = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out_diploma")
res = json.load(open(os.path.join(run, "result.json"), encoding="utf-8"))
root, nodes, cons = parse_uvl()
need = set(res["required_functions"]); asked = {n for n in need if n.split("_")[0] in res["request"]["FR"]}
chosen = set(res.get("selection", []))
nfrs = [n.lower() for n in res["request"]["NFR"]]
NAMES = {"nfr04": "privacy", "nfr07": "security", "nfr09": "availability", "nfr11": "usability", "nfr18": "cost", "nfr02": "decentralization",
         "nfr08": "verifiability", "nfr10": "recoverability", "nfr13": "standard"}

single = [(a, bs[0]) for a, bs in cons if len(bs) == 1]
fr_p = [(a, b) for a, b in single if a in need and b.startswith("P")]
fr_any = [(a, bs) for a, bs in cons if len(bs) > 1 and a in need]
pats = {b for _, b in fr_p} | {b for _, bs in fr_any for b in bs}
p_q = [(a, b) for a, b in single if a.startswith("P") and b.startswith("P")]
changed = True
while changed:                                   # prerequisites of the patterns shown
    changed = False
    for a, b in p_q:
        if a in pats and b not in pats: pats.add(b); changed = True

lab = lambda n: n.split("_", 1)[0] + " " + n.split("_", 1)[1].replace("_", " ")
def plabel(p):
    a = nodes[p]["attrs"]
    eff = " · ".join(f"{NAMES.get(n, n.upper())} {a[n]:+d}" for n in nfrs if a.get(n))
    return lab(p) + (f"\\n{eff}" if eff else "")

L = ['digraph FM { rankdir=LR; nodesep=0.12; ranksep=0.9; splines=true; newrank=true; fontname=Helvetica;',
     'node [fontname=Helvetica, fontsize=15, shape=box, style="rounded,filled", fillcolor="white", color="#1f3864", penwidth=1.3, margin="0.1,0.04"];',
     'edge [color="#374151", penwidth=1.2, arrowsize=0.9];',
     'SSI_system [label="SSI_system", fillcolor="#1f3864", fontcolor="white", fontsize=17];',
     'Functions [fillcolor="#dce6f2"]; Patterns [fillcolor="#dce6f2"];',
     'SSI_system -> Functions [arrowhead=dot]; SSI_system -> Patterns [arrowhead=dot, constraint=false, color="#9aa5b5"];']
for f in sorted(need):
    L.append(f'"{f}" [label="{lab(f)}", fillcolor="#fde3c4", color="#c25e0c", penwidth={2.4 if f in asked else 1.0}, fontname="{"Helvetica-Bold" if f in asked else "Helvetica"}"];')
    L.append(f'Functions -> "{f}" [arrowhead=odot];')
for p in sorted(pats):
    sel = p in chosen
    L.append(f'"{p}" [label="{plabel(p)}", fillcolor="{"#dce6f2" if sel else "white"}", color="{"#1f3864" if sel else "#9aa5b5"}", fontcolor="{"#111827" if sel else "#6b7280"}", penwidth={2.2 if sel else 1.0}];')
    L.append(f'"{p}" -> Patterns [dir=back, arrowtail=odot];')
for a, b in fr_p:
    L.append(f'"{a}" -> "{b}" [style=dashed, color="#2e5aa8"];')
for i, (a, bs) in enumerate(fr_any):
    L.append(f'or{i} [label="one of", shape=ellipse, style="filled", fillcolor="#fff7ed", color="#c25e0c", fontsize=12, margin="0.02,0.01"];')
    L.append(f'"{a}" -> or{i} [style=dashed, color="#c25e0c"];')
    for b in bs: L.append(f'or{i} -> "{b}" [style=dashed, color="#c25e0c"];')
for a, b in p_q:
    if a in pats and b in pats: L.append(f'"{a}" -> "{b}" [style=dotted, color="#6b7280", constraint=false];')
L.append('label="orange: functions (bold: requested)    blue: selected patterns    white: allowed, not selected    - - - F => P  /  F => one of (P1 | P2 | ...)    · · · P => Q (requires)    -o optional   -● mandatory"; labelloc=b; fontsize=16;')
L.append("}")
out = os.path.join(run, "fm.dot"); open(out, "w", encoding="utf-8").write("\n".join(L))
if shutil.which("dot"):
    subprocess.run(["dot", "-Tpng", "-Gdpi=200", out, "-o", os.path.join(run, "fm.png")])
    print(f"written {os.path.join(run, 'fm.png')}: {len(need)} functions, {len(pats)} patterns ({len(chosen & pats)} selected), "
          f"{len(fr_p)} F => P, {len(fr_any)} F => one of, {sum(1 for a, b in p_q if a in pats and b in pats)} P => Q")
else:
    print(f"written {out} (install Graphviz for the PNG)")
