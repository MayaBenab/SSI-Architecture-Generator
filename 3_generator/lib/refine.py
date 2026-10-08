"""Phase 2 in COMPONENT-AND-CONNECTOR terms (Guth & Leymann: architecture = graph of components and connectors).
A pattern adds components (inside an actor, or in the registry), connectors (between components, with the data that
flows on them) and possibly refines an abstract component. Data (keys, DIDs, VCs) are not nodes: they are either
stores (components) or payloads on connectors.
Architecture A = {components: {id: (type, parent)}, connectors: {(src, dst, name): (protocol, payload)}}
Pattern = (R, F): R = components / connectors that must exist ; F = components / connectors added."""
from copy import deepcopy

import os, json
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
    return {"components": dict(_G0["components"]), "connectors": dict(_G0["connectors"]), "tags": {}}

# =====================================================================================================================
# Pattern application as in Guth & Leymann (2020): an architecture is a graph G = (V, E, type); a pattern is (R, F_R, f_R).
#   match(R, G)   : finds an injective, type-preserving match of the required fragment R in G (here: by component / connector
#                   identity, since the rules are written on the named elements the earlier patterns create)
#   f_R(G, m, F)  : the local operator; inserts the modification fragment F at the match (and removes the abstract
#                   interaction the pattern makes concrete, the "rewrite" case)
#   refine(G0, s) : applies the sequence s from G0:  G_i = f_R(G_{i-1}, m_i)  whenever m_i = match(R_i, G_{i-1}) exists
# =====================================================================================================================

def match(R, G):
    """Match of the required fragment R = (components, connectors) in G. Returns the match (the elements of G matched by R)
    or None, with the first missing element."""
    comps, conns = R
    for c in comps:
        if c not in G["components"]: return None, c
    for k in conns:
        if k not in G["connectors"]: return None, k[2]
    return {"components": list(comps), "connectors": list(conns)}, None

def f_R(G, F, deleted=(), refines=None, tag=None):
    """Local operator: G' = f_R(G). Removes the connectors in `deleted`, adds the components and connectors of F (with
    their type, container, protocol, payload), refines the type of existing components; tags every change with the pattern."""
    G2 = {"components": dict(G["components"]), "connectors": dict(G["connectors"]), "tags": dict(G.get("tags", {}))}
    log = {"components_added": [], "connectors_added": [], "connectors_deleted": [], "refines": {}}
    for k in deleted:
        if k in G2["connectors"]: del G2["connectors"][k]; log["connectors_deleted"].append(f"{k[2]} ({k[0]}→{k[1]})")
    for c, (typ, container) in F.get("components", {}).items():
        G2["components"][c] = (typ, container); G2["tags"][c] = tag; log["components_added"].append(c)
    for c, typ in (refines or {}).items():
        if c in G2["components"]:
            G2["components"][c] = (typ, G2["components"][c][1]); G2["tags"][c] = tag; log["refines"][c] = typ
    for k, (proto, payload) in F.get("connectors", {}).items():
        G2["connectors"][k] = (proto, payload); G2["tags"][k] = tag; log["connectors_added"].append(k[2])
    return G2, log

def refine(sequence, reasons=None, G0=None):
    """Refinement: apply the ordered sequence of pattern ids from G0. For each pattern: match R (verify), check that no
    deletion removes what an applied pattern required, then f_R (apply). Returns the final graph and the step log."""
    G = G0 or A0(); G.setdefault("tags", {}); applied = []; steps = []
    for p in sequence:
        reason = (reasons or {}).get(p, [])
        if p not in P: steps.append({"pattern": p, "status": "SKIPPED (no rule yet)", "reason": reason}); continue
        rule = P[p]; m, missing = match(rule["R"], G)
        if m is None: steps.append({"pattern": p, "status": "VERIFY FAILED", "missing": missing, "reason": reason}); continue
        blocked = [k for k in rule.get("D", []) if any(k in P[q]["R"][1] for q in applied)]
        if blocked: steps.append({"pattern": p, "status": "DELETE BLOCKED", "blocked": [k[2] for k in blocked], "reason": reason}); continue
        G, log = f_R(G, rule["F"], rule.get("D", []), rule["F"].get("refines"), tag=(p, reason))
        steps.append({"pattern": p, "status": "APPLIED", **log, "reason": reason}); applied.append(p)
    return G, steps

def construction_order(sequence):
    """Order for the refinement: keep the given order (requires relation, from the selection) but place each pattern after
    the patterns of the sequence that create a component its R needs (R is matched by name). Stable topological sort."""
    creators = {}
    for q in sequence:
        for c in (P[q]["F"]["components"] if q in P else {}): creators.setdefault(c, set()).add(q)
    before = {p: {q for c in (P[p]["R"][0] if p in P else []) for q in creators.get(c, ()) if q != p} for p in sequence}
    out, done = [], set()
    while len(out) < len(sequence):
        p = next((p for p in sequence if p not in done and before[p] <= done), None)
        if p is None: p = next(p for p in sequence if p not in done)   # cycle: keep the given order
        out.append(p); done.add(p)
    return out

