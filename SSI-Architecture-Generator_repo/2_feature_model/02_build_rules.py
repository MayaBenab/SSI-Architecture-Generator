"""Step 2 (offline, once per catalogue): parts B and C of the knowledge base -> rules.json and deployment.json.
Reads ../1_knowledge_base/SSI_Pattern_KnowledgeBase.xlsx (sheets 'G0 (abstract architecture)', 'Rules (R,F)',
'Interfaces (component types)', 'Connectors (standards)', 'Deployment (components)') and writes, next to FM_SSI.uvl:
  rules.json       G0 and the rule (R, D, F, refines) of each pattern         -> read by 3_generator/refine.py
  order_sources.json  Related Patterns of the catalogue and lifecycle states -> read by 16_check_order.py
  deployment.json  how each component type and connector protocol is realised on the stack, interfaces, standards
                   -> read by deploy.py, interfaces.py
Run it after any change of parts B or C.  usage: python 02_build_rules.py"""
import os, re, json, openpyxl
HERE = os.path.dirname(os.path.abspath(__file__))
KB = os.path.join(HERE, "..", "1_knowledge_base", "SSI_Pattern_KnowledgeBase.xlsx")
wb = openpyxl.load_workbook(KB, data_only=True)
L = lambda v, sep="\n": [x.strip() for x in str(v).split(sep) if x and x.strip()] if v else []

# ---------------- part B: G0 and rules ----------------
comps, conns = {}, []
for comp, typ_or_conn, container, proto in wb["G0 (abstract architecture)"].iter_rows(min_row=2, values_only=True):
    if comp: comps[comp] = {"type": typ_or_conn, "container": container or None}
    else:
        src, rest = typ_or_conn.split(" -> ", 1); dst, name = rest.split(": ", 1)
        pr, pl = (proto.split("] ", 1) if proto and proto.startswith("[") else ("", proto or ""))
        conns.append({"src": src.strip(), "dst": dst.strip(), "name": name.strip(), "protocol": pr.strip("[ "), "payload": pl.strip()})
hdrP = [c.value for c in wb["P"][1]]
short = {r[0]: r[hdrP.index("short name")] for r in wb["P"].iter_rows(min_row=2, values_only=True) if r[0]}   # one name per pattern
rules = {}
for p, name, R, D, Fc, Fk, Ref, src in wb["Rules (R,F)"].iter_rows(min_row=2, values_only=True):
    if not p: continue
    deleted = []
    for item in L(D, ","):
        n, ep = item.rsplit(" (", 1); s_, d_ = ep.rstrip(")").replace("→", "->").split("->")
        deleted.append({"src": s_.strip(), "dst": d_.strip(), "name": n.strip()})
    components = []
    for line in L(Fc):
        cid, rest = line.split(": ", 1); typ, container = rest.rsplit(" in ", 1); container = container.strip()
        components.append({"id": cid.strip(), "type": typ.strip(), "container": None if container in ("None", "", "external") else container})
    connectors = []
    for line in L(Fk):
        ep, rest = line.split(": ", 1); s_, d_ = ep.split(" -> ")
        n, tail = rest.split(" [", 1); proto, payload = (tail.split("] ", 1) if "] " in tail else (tail.rstrip("]"), ""))
        connectors.append({"src": s_.strip(), "dst": d_.strip(), "name": n.strip(), "protocol": proto.strip(), "payload": payload.strip()})
    refines = {c.strip(): t.strip() for line in L(Ref) if " -> " in line for c, t in [line.split(" -> ", 1)]}
    rules[p] = {"name": re.sub(r"[^A-Za-z0-9]+", " ", short.get(p) or name).strip(),   # as in FM_SSI.uvl
                "required": L(R, ","), "deleted": deleted, "added": {"components": components, "connectors": connectors, "refines": refines}, "source": src}
json.dump({"G0": {"components": comps, "connectors": conns}, "rules": rules}, open(os.path.join(HERE, "rules.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)

# ---------------- part C: realisation of the components and connectors of G_n, interfaces, standards ----------------
# What is deployed are the components and connectors of the generated graph, not the patterns: one row per component type
# and per connector protocol (sheet 'Deployment (components)').
ws = wb["Deployment (components)"]; hdr = [c.value for c in ws[1]]; realisation = {"components": {}, "connectors": {}}
for row in ws.iter_rows(min_row=2, values_only=True):
    r = dict(zip(hdr, row))
    if not r["element"]: continue
    agents = str(r["agents"] or "").strip()
    realisation["components" if r["kind"] == "component" else "connectors"][r["element"].strip()] = {
        "realised": str(r["realised"]).strip().lower() == "yes", "agents": agents, "note": r["note"] or "",
        "services": L(r["services"]), "options": L(r["options"]), "tests": L(r["tests"]),
        "indy": {"services": L(r["services_indy"]), "options": L(r["options_indy"]), "tests": L(r["tests_indy"])},
        "noledger_substitution": r["noledger_substitution"] or "", "source": r["source"] or ""}
types = {t: {"provides": L(prov, ","), "requires": L(req, ",")} for t, prov, req in wb["Interfaces (component types)"].iter_rows(min_row=2, values_only=True) if t}
connectors = {n: {"standard": std, "kind": kind, "interface": iface, "implementations": impl or ""} for n, std, kind, iface, impl in wb["Connectors (standards)"].iter_rows(min_row=2, values_only=True) if n}
json.dump({"realisation": realisation, "component_types": types, "connectors": connectors}, open(os.path.join(HERE, "deployment.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(f"rules.json: G0 {len(comps)} components, {len(conns)} connectors; {len(rules)} rules")
print(f"deployment.json: realisation of {len(realisation['components'])} component types and {len(realisation['connectors'])} connector protocols "
      f"({sum(v['realised'] for v in realisation['components'].values())} and {sum(v['realised'] for v in realisation['connectors'].values())} realised); "
      f"{len(types)} interface types, {len(connectors)} standards")

# ---------------- part D: what justifies the order (read by 3_generator/16_check_order.py) ----------------
# The order itself comes from the rules (an output of P is an anchor of Q); the catalogue's Related Patterns and the
# lifecycles of [1] are checked against it, they are not constraints.
links = [{"p": p, "q": q, "item": it} for p, _, q, _, it, _ in wb["related (catalogue)"].iter_rows(min_row=2, values_only=True) if p]
nxt = {s: [x for x in L(n, ",") if x != "end"] for s, _, n, _ in wb["lifecycle states"].iter_rows(min_row=2, values_only=True) if s}
pst = {p: L(st, ",") for p, _, st, _, _ in wb["lifecycle (patterns)"].iter_rows(min_row=2, values_only=True) if p}
hdr = [c.value for c in wb["requires"][1]]
variants = [[r[0], r[2]] for r in wb["requires"].iter_rows(min_row=2, values_only=True) if r[0] and "origin" in hdr and r[hdr.index("origin")] == "variant"]
json.dump({"catalogue_links": links, "variants": variants, "lifecycle_next": nxt, "pattern_states": pst},
          open(os.path.join(HERE, "order_sources.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(f"order_sources.json: {len(links)} catalogue links, {len(nxt)} lifecycle states, {len(pst)} patterns placed")
