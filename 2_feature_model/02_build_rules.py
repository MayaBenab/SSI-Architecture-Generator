"""Step 2 (offline, once per catalogue): parts B and C of the knowledge base -> rules.json and deployment.json.
Reads ../1_knowledge_base/SSI_Pattern_KnowledgeBase.xlsx (sheets 'G0 (abstract architecture)', 'Rules (R,F)',
'Interfaces (component types)', 'Connectors (standards)', 'Deployment (Aries)') and writes, next to FM_SSI.uvl:
  rules.json       G0 and the rule (R, D, F, refines) of each pattern         -> read by 3_generator/refine.py
  deployment.json  what each pattern becomes in the stack, interfaces, standards -> read by deploy.py, interfaces.py
Run it after any change of parts B or C.  usage: python 02_build_rules.py"""
import os, json, openpyxl
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
    rules[p] = {"name": name, "required": L(R, ","), "deleted": deleted, "added": {"components": components, "connectors": connectors, "refines": refines}, "source": src}
json.dump({"G0": {"components": comps, "connectors": conns}, "rules": rules}, open(os.path.join(HERE, "rules.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)

# ---------------- part C: deployment mapping, interfaces, standards ----------------
ws = wb["Deployment (Aries)"]; hdr = [c.value for c in ws[1]]; mapping = {}
for row in ws.iter_rows(min_row=2, values_only=True):
    r = dict(zip(hdr, row))
    if not r["p"]: continue
    mapping[r["p"]] = {"name": r["pattern"], "realised": str(r["realised"]).strip().lower() == "yes", "note": r["note"] or "",
        "services": L(r["services"]), "options": {"all": L(r["options_all"]), "holder": L(r["options_holder"]), "issuer": L(r["options_issuer"]), "verifier": L(r["options_verifier"])},
        "tests": L(r["tests"]),
        "indy": {"services": L(r["services_indy"]), "options": {"all": L(r["options_indy_all"]), "issuer": L(r["options_indy_issuer"]), "verifier": L(r["options_indy_verifier"])}, "tests": L(r["tests_indy"])},
        "noledger_substitution": r["noledger_substitution"] or ""}
types = {t: {"provides": L(prov, ","), "requires": L(req, ",")} for t, prov, req in wb["Interfaces (component types)"].iter_rows(min_row=2, values_only=True) if t}
connectors = {n: {"standard": std, "kind": kind, "interface": iface, "implementations": impl or ""} for n, std, kind, iface, impl in wb["Connectors (standards)"].iter_rows(min_row=2, values_only=True) if n}
json.dump({"mapping": mapping, "component_types": types, "connectors": connectors}, open(os.path.join(HERE, "deployment.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(f"rules.json: G0 {len(comps)} components, {len(conns)} connectors; {len(rules)} rules")
print(f"deployment.json: {len(mapping)} patterns mapped, {len(types)} component types, {len(connectors)} connectors")
