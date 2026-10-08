"""Tables of a run, as they appear on the poster (section 5): every cell is read from result.json and FM_SSI.uvl, nothing typed.
usage: python 13_tables.py [out_diploma/result.json]   (no argument: the run written by 10_generate.py without arguments)   -> selection_table.csv and selection_table.md next to result.json"""
import csv, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
from fm import parse_uvl

path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "out_diploma", "result.json")
r = json.load(open(path, encoding="utf-8"))
_, nodes, _ = parse_uvl()
nfrs = r["request"]["NFR"]
rows = []
for p in r["sequence"]:
    attrs = nodes[p]["attrs"]
    effect = ", ".join(f"{n} {attrs[n.lower()]:+d}" for n in nfrs if attrs.get(n.lower()))
    rows.append({"pattern": p.split("_")[0] + " " + " ".join(p.split("_")[1:]), "why (generator's reasons)": "; ".join(r["reasons"][p]),
                 f"effect on {', '.join(nfrs)}": effect})
out = os.path.dirname(path)
with open(os.path.join(out, "selection_table.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
md = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * len(rows[0])] + ["| " + " | ".join(x.values()) + " |" for x in rows]
open(os.path.join(out, "selection_table.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
print("\n".join(md))
