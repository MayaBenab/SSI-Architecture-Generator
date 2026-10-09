"""Check that the architecture figure is the output of an execution, not a drawing.
usage: python 14_check_figure.py [out_diploma]   (no argument: the run written by 10_generate.py without arguments)

1. re-executes the refinement: G0 and the rules of rules.json, applied in the order stored in result.json (no solver needed);
2. compares the re-executed graph with the architecture stored in result.json by 10_generate.py;
3. compares it with every node and arrow of architecture.dot, the file Graphviz turns into architecture.png;
4. prints each connector with the rule that created it, its protocol and the line style it receives in the figure."""
import json, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
from refine import refine, P as RULES
from draw_arch import kind_style

run = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "out_diploma")
res = json.load(open(os.path.join(run, "result.json"), encoding="utf-8"))
seq = [p.split("_")[0] for p in res["sequence"]]

# 1. execution of the rules, step by step, with the pattern that adds each connector
G, steps = refine(seq)
added_by = {}
for p in seq:
    if p in RULES:
        for k in RULES[p]["F"]["connectors"]: added_by[k] = p
print(f"1. refinement re-executed from G0 with {len(seq)} rules of rules.json: {len(G['components'])} components, {len(G['connectors'])} connectors")

# 2. same graph as the one 10_generate.py stored?
stored_c = set(res["architecture"]["components"])
stored_k = {(c[0], c[1], c[2]) for c in res["architecture"]["connectors"]}
ok2 = stored_c == set(G["components"]) and stored_k == set(G["connectors"])
print(f"2. identical to result.json: {ok2}")

# 3. every arrow of the figure is a connector of the graph, and every connector is drawn
dot = open(os.path.join(run, "architecture.dot"), encoding="utf-8").read()
arrows = {(s, d, n) for s, d, n in re.findall(r'"([^"]+)" -> "([^"]+)" \[[^\]]*label="([^"\\]+)', dot)}
ok3 = arrows == set(G["connectors"])
print(f"3. architecture.dot: {len(arrows)} arrows, one per connector, none added by hand: {ok3}")

# 4. the connectors, as the figure shows them
print("\n4. connector (source -> target: name)                              protocol                   line    added by")
for (s, d, n), (proto, payload) in sorted(G["connectors"].items(), key=lambda x: (kind_style(x[1][0]), x[0])):
    print(f"   {s + ' -> ' + d + ': ' + n:62s} {proto:26s} {kind_style(proto):7s} {added_by.get((s, d, n), 'G0')}")
sys.exit(0 if ok2 and ok3 else 1)
