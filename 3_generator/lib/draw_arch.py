"""Drawing of the generated architecture G_n (Graphviz DOT), in the style of the poster's G10 figure.
Separate from the refinement: f_R is an operator on graphs (refine.py); this module only renders a graph.
Boxes are components (nested in their container), arrows are connectors; each box carries the pattern that added it."""


KINDS = [("solid", "message between two agents (network)"),
         ("dashed", "local call inside one agent"),
         ("dotted", "registry access (write or read)")]


def kind_style(proto):
    """Line style of a connector, from its protocol: registry access dotted (abstract interactions too), local call dashed,
    message between agents solid."""
    if proto == "abstract" or proto.startswith("registry"): return "dotted"
    return "dashed" if proto == "local" else "solid"


def to_dot(A, steps, edge_labels=False, rankdir="LR", legend=True):
    prov = {}
    for s in steps:
        for c in s.get("components_added", []): prov[c] = s["pattern"]
        for c in s.get("refines", {}): prov.setdefault(c, s["pattern"])
    kids = {}
    for cid, (t, parent) in A["components"].items(): kids.setdefault(parent, []).append(cid)
    L = [f'digraph A {{ rankdir={rankdir}; compound=true; nodesep=0.3; ranksep=0.5; pad=0.1; fontname=Helvetica;',
         'node [fontname=Helvetica, fontsize=20, shape=box, style="rounded,filled", margin="0.12,0.05", fillcolor="#dce6f2", color="#1f3864", penwidth=1.6];',
         'edge [fontname=Helvetica, fontsize=16, color="#374151", fontcolor="#1f3864", penwidth=1.6, arrowsize=1.1];']

    def tag(cid): return f"\\n← {prov[cid]}" if cid in prov else ""

    def emit(cid, depth):
        t, parent = A["components"][cid]
        if kids.get(cid):
            label = (cid if depth == 0 and t.startswith("Actor") else t) + tag(cid)
            L.append(f'subgraph "cluster_{cid}" {{ label="{label}"; style="rounded,filled"; fontname=Helvetica; '
                     + ('fillcolor="#f3f6fa"; color="#1f3864"; penwidth=2; fontsize=22;' if depth == 0 else 'fillcolor="#ffffff"; color="#8a99b3"; fontsize=18;'))
            L.append(f'"{cid}" [label="", shape=point, style=invis];')
            for k in kids[cid]: emit(k, depth + 1)
            L.append("}")
        else:
            L.append(f'"{cid}" [label="{(cid + chr(92) + "n") if parent is None else ""}{t}{tag(cid)}"];')

    for cid in kids.get(None, []): emit(cid, 0)
    for (s, d, name), (proto, payload) in A["connectors"].items():
        style = kind_style(proto)
        attrs = [f"style={style}"]
        if edge_labels == "payload": attrs.append(f'label="{name}' + (f' ({payload})' if payload else '') + '"')
        elif edge_labels: attrs.append(f'label="{name}\\n[{proto}]"')
        if kids.get(d): attrs.append(f'lhead="cluster_{d}"')
        if kids.get(s): attrs.append(f'ltail="cluster_{s}"')
        L.append(f'"{s}" -> "{d}" [{", ".join(attrs)}];')
    used = {kind_style(p) for (_, _, _), (p, _) in A["connectors"].items()}
    if legend and not all(p == "abstract" for (p, _) in A["connectors"].values()):
        L.append('subgraph cluster_legend { label="connectors"; fontsize=18; fontname=Helvetica; style="rounded"; color="#8a99b3";')
        for i, (st, text) in enumerate(k for k in KINDS if k[0] in used):
            L.append(f'lg{i}a [label="", shape=point, width=0.05]; lg{i}b [label="{text}", shape=plaintext, style="", fontsize=17];')
            L.append(f'lg{i}a -> lg{i}b [style={st}, arrowhead=normal, minlen=1];')
        L.append("}")
    L.append("}")
    return "\n".join(L)
