"""Phase 2 in COMPONENT-AND-CONNECTOR terms (Guth & Leymann: architecture = graph of components and connectors).
A pattern adds components (inside an actor, or in the registry), connectors (between components, with the data that
flows on them) and possibly refines an abstract component. Data (keys, DIDs, VCs) are not nodes: they are either
stores (components) or payloads on connectors.
Architecture A = {components: {id: (type, parent)}, connectors: {(src, dst, name): (protocol, payload)}}
Pattern = (R, F): R = components / connectors that must exist ; F = components / connectors added."""
from copy import deepcopy

import os, json
from networkx import DiGraph
from networkx.algorithms.isomorphism import DiGraphMatcher   # VF2 (Cordella et al. 2004)
RULES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "2_feature_model", "rules.json")

def _load_kb():
    """Part B of the knowledge base as written by 2_feature_model/build_rules.py (rules.json): G0 and the rule of each pattern."""
    d = json.load(open(RULES_PATH, encoding="utf-8"))
    g0 = {"components": {c: (v["type"], v["container"]) for c, v in d["G0"]["components"].items()},
          "connectors": {(k["src"], k["dst"], k["name"]): (k["protocol"], k["payload"]) for k in d["G0"]["connectors"]}, "tags": {}}
    rules = {}
    for p, r in d["rules"].items():
        rules[p] = {"R": (list(r["required"]), []), "D": [(k["src"], k["dst"], k["name"]) for k in r["deleted"]],
                    "F": {"components": {c["id"]: (c["type"], c["container"]) for c in r["added"]["components"]},
                          "connectors": {(k["src"], k["dst"], k["name"]): (k["protocol"], k["payload"]) for k in r["added"]["connectors"]},
                          "refines": dict(r["added"]["refines"])}}
    return g0, rules

_G0, P = _load_kb()
def A0():
    return {"components": dict(_G0["components"]), "connectors": dict(_G0["connectors"]), "tags": {},
            "base": {c: t for c, (t, _) in _G0["components"].items()}}

# DECL: where each named element of the rules is declared (G0 or the F of a rule): id -> (type, container).
# The names in R only say WHICH KIND of element is required (its type and the role it lies in); the match is by type.
DECL = dict(_G0["components"])
for _r in P.values(): DECL.update(_r["F"]["components"])

def _chain(c):
    """ancestors of a declared element, nearest first"""
    out = []
    while c in DECL and DECL[c][1] is not None: c = DECL[c][1]; out.append(c)
    return out

def signature(c):
    """(type, root): the kind of element R requires — its declared type and the role (or registry) it belongs to"""
    ch = _chain(c); return (DECL[c][0], ch[-1] if ch else c)

def pattern_graph(p):
    """R of pattern p as a typed graph: one node per required element (typed), plus the role / registry that contains it,
    and an 'inside' edge from every container to what it contains (transitively)."""
    R = DiGraph()
    for c in P[p]["R"][0]:
        R.add_node(c, t=DECL[c][0])
        for a in _chain(c):
            if a in P[p]["R"][0] or a == _chain(c)[-1]: R.add_node(a, t=DECL[a][0]); R.add_edge(a, c)
    return R

def arch_graph(G):
    """the architecture as a typed graph: every component with its type (and its base type before refinement), 'inside'
    edges from every container to all it contains"""
    X = DiGraph(); base = G.get("base", {})
    for c, (t, parent) in G["components"].items(): X.add_node(c, t=t, base=base.get(c, t))
    for c, (t, parent) in G["components"].items():
        a = parent
        while a is not None: X.add_edge(a, c); a = G["components"][a][1] if a in G["components"] else None
    return X

# =====================================================================================================================
# Pattern application as in Guth & Leymann (2020): an architecture is a graph G = (V, E, type); a pattern is (R, F_R, f_R).
#   match(R, G)   : finds an injective, type- and containment-preserving match of the required fragment R in G by subgraph
#                   isomorphism (VF2, Cordella et al. 2004); the names written in R only stand for their kind (type, role)
#   f_R(G, m, F)  : the local operator; inserts the modification fragment F at the match (and removes the abstract
#                   interaction the pattern makes concrete, the "rewrite" case)
#   refine(G0, s) : applies the sequence s from G0:  G_i = f_R(G_{i-1}, m_i)  whenever m_i = match(R_i, G_{i-1}) exists
# =====================================================================================================================

def match(p, G):
    """Guth & Leymann, Def. applicability: R is applicable to G iff there is a subgraph Ĝ ⊑ G with Ĝ ≅ R. Found by subgraph
    monomorphism (VF2) on types and containment. Returns (mapping R-node -> G-node, number of matches) or (None, a
    required element with no candidate)."""
    R = pattern_graph(p); X = arch_graph(G)
    gm = DiGraphMatcher(X, R, node_match=lambda g, r: r["t"] in (g["t"], g["base"]))
    found = sorted(({r: g for g, r in m.items()} for m in gm.subgraph_monomorphisms_iter()), key=lambda m: sorted(m.items()))
    if not found:
        miss = next((c for c in R if not any(R.nodes[c]["t"] in (X.nodes[g]["t"], X.nodes[g]["base"]) for g in X)), "a typed fragment")
        return None, miss
    return found[0], len(found)

def f_R(G, F, deleted=(), refines=None, tag=None, m=None):
    """Local operator: G' = f_R(G). Removes the connectors in `deleted`, adds the components and connectors of F (with
    their type, container, protocol, payload), refines the type of existing components; tags every change with the pattern."""
    m = m or {}; at = lambda x: m.get(x, x)          # names of R are replaced by the elements of G they matched
    G2 = {"components": dict(G["components"]), "connectors": dict(G["connectors"]), "tags": dict(G.get("tags", {})),
          "base": dict(G.get("base", {}))}
    deleted = [(at(a), at(b), n) for a, b, n in deleted]
    log = {"components_added": [], "connectors_added": [], "connectors_deleted": [], "refines": {}}
    for k in deleted:
        if k in G2["connectors"]: del G2["connectors"][k]; log["connectors_deleted"].append(f"{k[2]} ({k[0]}→{k[1]})")
    for c, (typ, container) in F.get("components", {}).items():
        G2["components"][c] = (typ, at(container) if container else container); G2["base"][c] = typ; G2["tags"][c] = tag; log["components_added"].append(c)
    for c, typ in (refines or {}).items():
        c = at(c)
        if c in G2["components"]:
            G2["components"][c] = (typ, G2["components"][c][1]); G2["tags"][c] = tag; log["refines"][c] = typ
    for (a, b, n), (proto, payload) in F.get("connectors", {}).items():
        k = (at(a), at(b), n); G2["connectors"][k] = (proto, payload); G2["tags"][k] = tag; log["connectors_added"].append(n)
    return G2, log

def refine(sequence, reasons=None, G0=None):
    """Refinement: apply the ordered sequence of pattern ids from G0. For each pattern: match R (verify), check that no
    deletion removes what an applied pattern required, then f_R (apply). Returns the final graph and the step log."""
    G = G0 or A0(); G.setdefault("tags", {}); applied = []; steps = []
    for p in sequence:
        reason = (reasons or {}).get(p, [])
        if p not in P: steps.append({"pattern": p, "status": "SKIPPED (no rule yet)", "reason": reason}); continue
        rule = P[p]; m, n_or_missing = match(p, G)
        if m is None: steps.append({"pattern": p, "status": "VERIFY FAILED", "missing": n_or_missing, "reason": reason}); continue
        blocked = [k for k in rule.get("D", []) if any(k in P[q]["R"][1] for q in applied)]
        if blocked: steps.append({"pattern": p, "status": "DELETE BLOCKED", "blocked": [k[2] for k in blocked], "reason": reason}); continue
        G, log = f_R(G, rule["F"], rule.get("D", []), rule["F"].get("refines"), tag=(p, reason), m=m)
        steps.append({"pattern": p, "status": "APPLIED", "matches": n_or_missing, **log, "reason": reason}); applied.append(p)
    return G, steps

def precedence(patterns):
    """The DAG of the refinement. Q can only be applied once the components its R needs exist; so P comes before Q when Q
    needs a component that P adds:  P -> Q  iff  F_P ∩ R_Q ≠ ∅.  Returns {(P, Q): [the components P adds and Q needs]}."""
    # by kind, not by name: Q needs an element of type t in role r (signature), P adds an element of that signature
    need = {q: {signature(c) for c in P[q]["R"][0]} if q in P else set() for q in patterns}
    arcs = {}
    for p in patterns:
        for q in patterns:
            if p == q or p not in P: continue
            a = sorted(c for c in P[p]["F"]["components"] if signature(c) in need[q])
            if a: arcs[(p, q)] = a
    return arcs

def levels(patterns, arcs=None):
    """Rows (steps) of the DAG: Kahn's topological sort by levels (Kahn 1962, CACM 5(11):558-562), O(n + e). Row 1 = the patterns that need only components of G0; row k = those whose predecessors are all in
    rows < k. Inside a row the patterns do not depend on each other (any order gives the same graph)."""
    arcs = precedence(patterns) if arcs is None else arcs
    before = {q: {p for p, q2 in arcs if q2 == q} for q in patterns}
    out, done = [], set()
    while len(done) < len(patterns):
        ready = sorted(q for q in patterns if q not in done and before[q] <= done)
        if not ready: raise ValueError(f"cycle in the precedence graph between {sorted(set(patterns) - done)}")
        out.append(ready); done |= set(ready)
    return out

def refine_dag(patterns, reasons=None, G0=None):
    """Refinement driven by the DAG: from G0, apply row by row; a pattern is applied as soon as the components its R needs
    exist (its predecessors have been applied). Each step records its row and what it needs from which earlier pattern.
    Returns G_n, the steps, the rows and the arcs of the DAG."""
    arcs = precedence(patterns); lv = levels(patterns, arcs)
    G, steps = refine([p for level in lv for p in level], reasons, G0)
    level_of = {p: k for k, level in enumerate(lv, 1) for p in level}
    for st in steps:
        q = st["pattern"]; st["row"] = level_of[q]
        st["needs"] = {p: a for (p, q2), a in arcs.items() if q2 == q}
    return G, steps, lv, arcs
