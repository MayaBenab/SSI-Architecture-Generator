"""Interfaces and standards of the component types and connectors (grounding of the logical components).
Each component TYPE declares the interfaces it provides and requires; each connector NAME is bound to the standard that
implements it and to its kind (local / network / registry). A connector binds a required interface of its source to a provided
interface of its target. This table is the architect's grounding: a component 'exists' when a standard and at least one
implementation realise its interfaces."""

import os, json
DEPLOY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "2_feature_model", "deployment.json")

def _load():
    """Part C of the knowledge base as written by 2_feature_model/build_rules.py (deployment.json): interfaces and standards."""
    d = json.load(open(DEPLOY_PATH, encoding="utf-8"))
    types = {t: (v["provides"], v["requires"]) for t, v in d["component_types"].items()}
    conns = {n: (v["standard"], v["kind"], v["interface"]) for n, v in d["connectors"].items()}
    impls = {v["standard"]: v["implementations"] for v in d["connectors"].values()}
    return types, conns, impls

TYPES, CONNECTORS, IMPLEMENTATIONS = _load()

def check_interfaces(G):
    """Well-formedness: every connector binds a required interface of its source to a provided interface of its target,
    and every required interface of a component is bound by some connector (or satisfied inside its container)."""
    report = {"unknown_type": [], "unbound_connector": [], "unsatisfied": []}
    prov = {}; req = {}
    for c, (t, par) in G["components"].items():
        if t not in TYPES: report["unknown_type"].append((c, t)); continue
        prov[c], req[c] = TYPES[t]
    bound = {c: set() for c in G["components"]}
    for (s, d, name), (proto, payload) in G["connectors"].items():
        if name not in CONNECTORS: report["unbound_connector"].append(name); continue
        iface = CONNECTORS[name][2]
        if iface not in prov.get(d, []) and iface not in prov.get(s, []): report["unbound_connector"].append(f"{name}: {iface} provided by neither {s} nor {d}")
        bound[s].add(iface); bound[d].add(iface)
    def container_chain(c):
        chain = []; x = G["components"][c][1]
        while x: chain.append(x); x = G["components"][x][1]
        return chain
    for c in G["components"]:
        for iface in req.get(c, []):
            desc = [k for k in G["components"] if c in container_chain(k)]
            ok = iface in bound[c] or any(iface in bound[a] for a in container_chain(c)) or any(iface in bound[k] for k in desc) \
                 or any(iface in prov.get(k, []) for k in G["components"] if G["components"][k][1] == c or c in container_chain(k) or G["components"][k][1] == G["components"][c][1])
            if not ok: report["unsatisfied"].append((c, iface))
    return report
