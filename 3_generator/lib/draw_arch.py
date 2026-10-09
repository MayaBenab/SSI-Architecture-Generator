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


def to_dot(A, steps, edge_labels=False, rankdir="LR", legend=True, highlight=None):
    """highlight: a pattern id (e.g. P25); what its rule added is drawn in orange, to follow one pattern in G_n."""
    prov = {}
    hi_c, hi_e = set(), set()
    for s in steps:
        if s["pattern"] == highlight: hi_c = set(s.get("components_added", [])); hi_e = set(s.get("connectors_added", []))
    for s in steps:
        for c in s.get("components_added", []): prov[c] = s["pattern"]
        for c in s.get("refines", {}): prov[c] = (prov[c] + ", " + s["pattern"]) if c in prov else s["pattern"]   # created by, refined by
    kids = {}
    for cid, (t, parent) in A["components"].items(): kids.setdefault(parent, []).append(cid)
    L = [f'digraph A {{ rankdir={rankdir}; compound=true; nodesep=0.3; ranksep=0.5; pad=0.1; fontname=Helvetica;',
         'node [fontname=Helvetica, fontsize=20, shape=box, style="rounded,filled", margin="0.12,0.05", fillcolor="#f7ebdd", color="#5b2a12", penwidth=1.6];',
         'edge [fontname=Helvetica, fontsize=16, color="#374151", fontcolor="#5b2a12", penwidth=1.6, arrowsize=1.1];']

    def tag(cid): return f"\\n← {prov[cid]}" if cid in prov else ""

    def emit(cid, depth):
        t, parent = A["components"][cid]
        if kids.get(cid):
            label = (cid if depth == 0 and t.startswith("Actor") else t) + tag(cid)
            L.append(f'subgraph "cluster_{cid}" {{ label="{label}"; style="rounded,filled"; fontname=Helvetica; '
                     + ('fillcolor="#fbf6f0"; color="#5b2a12"; penwidth=2; fontsize=22;' if depth == 0 else
                        'fillcolor="#fde3c4"; color="#c25e0c"; penwidth=3; fontsize=18;' if cid in hi_c else 'fillcolor="#ffffff"; color="#b8a89a"; fontsize=18;'))
            L.append(f'"{cid}" [label="", shape=point, style=invis];')
            for k in kids[cid]: emit(k, depth + 1)
            L.append("}")
        else:
            hi = ', fillcolor="#fde3c4", color="#c25e0c", penwidth=3' if cid in hi_c else ''
            L.append(f'"{cid}" [label="{(cid + chr(92) + "n") if parent is None else ""}{t}{tag(cid)}"{hi}];')

    for cid in kids.get(None, []): emit(cid, 0)
    for (s, d, name), (proto, payload) in A["connectors"].items():
        style = kind_style(proto)
        attrs = [f"style={style}"]
        if name in hi_e and (s in hi_c or d in hi_c): attrs += ['color="#c25e0c"', 'fontcolor="#c25e0c"', "penwidth=3.5"]
        if edge_labels == "payload": attrs.append(f'label="{name}' + (f' ({payload})' if payload else '') + '"')
        elif edge_labels: attrs.append(f'label="{name}\\n[{proto}]"')
        if kids.get(d): attrs.append(f'lhead="cluster_{d}"')
        def inside(c, anc):
            while c is not None:
                c = A["components"][c][1] if c in A["components"] else None
                if c == anc: return True
            return False
        if kids.get(s) and not inside(d, s): attrs.append(f'ltail="cluster_{s}"')   # from a container to its own content: start inside it
        L.append(f'"{s}" -> "{d}" [{", ".join(attrs)}];')
    used = {kind_style(p) for (_, _, _), (p, _) in A["connectors"].items()}
    if legend and not all(p == "abstract" for (p, _) in A["connectors"].values()):
        L.append('subgraph cluster_legend { label="connectors"; fontsize=18; fontname=Helvetica; style="rounded"; color="#b8a89a";')
        for i, (st, text) in enumerate(k for k in KINDS if k[0] in used):
            L.append(f'lg{i}a [label="", shape=point, width=0.05]; lg{i}b [label="{text}", shape=plaintext, style="", fontsize=17];')
            L.append(f'lg{i}a -> lg{i}b [style={st}, arrowhead=normal, minlen=1];')
        L.append("}")
    L.append("}")
    return "\n".join(L)
