"""Traceability of one run, from the request to the deployment: writes out_X/trace.csv and out_X/TRACE.md
usage: python trace.py out_S1/result.json"""
import os, sys, json, csv
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from refine import P as RULES
from deploy import MAPPING

def trace(result_path):
    r = json.load(open(result_path, encoding="utf-8")); out = os.path.dirname(result_path)
    pid = lambda s: s.split("_")[0]
    rows = []
    for p in r.get("sequence", []):
        p_id = pid(p); reasons = r["reasons"][p]
        frs = [x.split()[1] for x in reasons if x.startswith("realizes")]
        dec = [x.split(" among ")[1] for x in reasons if x.startswith("chosen for")]
        req = [x.split()[2] for x in reasons if x.startswith("required by")]
        sup = [x.split()[1] for x in reasons if x.startswith("supports")]
        rule = RULES.get(p_id); comps = ", ".join(rule["F"].get("components", {}).keys()) if rule else "(no rule)"
        conns = ", ".join(k[2] for k in rule["F"].get("connectors", {}).keys()) if rule else ""
        m = MAPPING.get(p_id); dep = "NOT REALISED" if m is None else (m.get("note", "") if m != "missing" else "(no mapping)")
        rows.append({"pattern": p, "realizes FR": " ".join(frs), "chosen among": " ".join(dec), "required by": " ".join(req),
                     "supports NFR": " ".join(sup), "components added (Phase 2)": comps, "connectors added": conns, "deployment (Aries)": dep})
    with open(os.path.join(out, "trace.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    md = [f"# Trace: {r['request']['FR']} / {r['request']['NFR']}", "", f"Required functions ({len(r['required_functions'])}): " + ", ".join(x.split('_')[0] for x in r["required_functions"]), "",
          "| # | pattern | realizes | chosen among | required by | supports | components (Phase 2) | deployment |", "|---|---|---|---|---|---|---|---|"]
    for i, x in enumerate(rows, 1):
        md.append(f"| {i} | {x['pattern']} | {x['realizes FR']} | {x['chosen among']} | {x['required by']} | {x['supports NFR']} | {x['components added (Phase 2)']} | {x['deployment (Aries)']} |")
    if r.get("tradeoffs"): md += ["", "Trade-offs: " + "; ".join(r["tradeoffs"])]
    open(os.path.join(out, "TRACE.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(f"trace written: {out}/trace.csv, {out}/TRACE.md")

def main():
    trace(sys.argv[1] if len(sys.argv) > 1 else "out_S1/result.json")

if __name__ == "__main__":
    main()
