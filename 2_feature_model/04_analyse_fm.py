"""Analysis of the extended feature model itself, before any request (automated analysis of feature models, Benavides et al.
2010): the same four operations as 03_check_fm_flamapy.py, computed on our own propositional encoding of FM_SSI.uvl (lib/fm.py,
Z3), as an independent cross-check.
  void        does the model have at least one product?
  dead        features that are in no product: a pattern that can never be selected, whatever the request
  core        features that are in every product
  false-opt.  optional features that are in every product where their parent is
usage: python 04_analyse_fm.py   -> fm_analysis.json"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "3_generator", "lib"))
from fm import FM
from z3 import Not

fm = FM()
V = fm.V
feats = [n for n in fm.nodes]
print(f"features: {len(feats)} ({len(fm.FR)} functions, {len(fm.PAT)} patterns); constraints: {len(fm.constraints)} + {len(fm.justification)} justification")
sat = fm.check()
print("void (no product):", not sat)
dead = [f for f in feats if not fm.check(V[f])]
core = [f for f in feats if not fm.check(Not(V[f]))]
parent = {n: fm.nodes[n]["parent"] for n in feats}
false_opt = [f for f in feats if fm.nodes[f]["rel"] in ("optional", "or") and parent[f] and f not in core
             and not fm.check(V[parent[f]], Not(V[f]))]
print("dead features:", dead or "none")
print("core features:", core)
print("false-optional features:", false_opt or "none")
import json
json.dump({"void": not sat, "dead": dead, "core": core, "false_optional": false_opt, "features": len(feats)},
          open(os.path.join(HERE, "fm_analysis.json"), "w", encoding="utf-8"), indent=1)
print("written fm_analysis.json")
