"""One request, steps 3 to 5 of the poster: select and order (FM_SSI.uvl + Z3) -> refine (rules.json) -> deploy (deployment.json),
then the trace from each requirement to the deployment. Each step reads one generated file, never the workbook.
usage: python 10_generate.py FR13 FR17 --nfr NFR04 NFR07 [--forbid P07] [--out DIR] [--draw]"""
import os, sys, json, subprocess, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); os.chdir(os.path.join(HERE, ".."))
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
from fm import FM
from selection import select
from refine import refine, construction_order
from interfaces import check_interfaces
from deploy import deploy
from trace import trace


def run(fr, nfr, forbid=(), out="out", draw=False, profile="no-ledger"):
    os.makedirs(out, exist_ok=True)
    print(f"REQUEST  FR={fr}  NFR={nfr}" + (f"  forbid={list(forbid)}" if forbid else ""))

    # ---- step 3: select and order (feature model FM_SSI.uvl, solver Z3) ----
    fm = FM(); r = select(fm, fr, nfr, forbid)
    print(f"[3] SELECT  {len(r['required_functions'])} FR needed (closure by depends)  |  products (filter): {r['products']}")
    if r["status"] == "UNSAT":
        print("    no architecture satisfies the request - explanation:"); [print("     -", e) for e in r["explanation"]]
        json.dump(r, open(os.path.join(out, "result.json"), "w", encoding="utf-8"), indent=1); return r
    print(f"    optimization: {r['size']} patterns (smallest set), score {r['score']} on {', '.join(nfr)}")
    for t in r.get("tradeoffs", []): print("    trade-off:", t)
    for c in r["choices"]: print(f"    {', '.join(c['for'])} need one of {', '.join(c['among'])}: {', '.join(c['chosen'])}")

    # order: the requires relation (selection.order), then the rules' R: a pattern comes after the patterns that create what its R needs
    seq_ids = construction_order([fm.pid(p) for p in r["sequence"]])
    full = {fm.pid(p): p for p in r["sequence"]}; r["sequence"] = [full[p] for p in seq_ids]
    print("    order:")
    for i, p in enumerate(r["sequence"], 1): print(f"     {i:2d}. {p:38s} <- {'; '.join(r['reasons'][p])}")

    # ---- step 4: refine G0 with the rules (R, F_R, f_R) of rules.json ----
    reasons = {fm.pid(p): r["reasons"][p] for p in r["sequence"]}
    A, steps = refine(seq_ids, reasons)
    applied = [s["pattern"] for s in steps if s["status"] == "APPLIED"]
    skipped = [s["pattern"] for s in steps if s["status"].startswith("SKIPPED")]
    failed = [s for s in steps if s["status"] in ("VERIFY FAILED", "DELETE BLOCKED")]
    abstract = [k for k, v in A["connectors"].items() if v[0] == "abstract"]
    print(f"[4] REFINE  {len(applied)} rules applied, {len(skipped)} skipped{(' ' + str(skipped)) if skipped else ''}, {len(failed)} failed  ->  G{len(applied)}: "
          f"{len(A['components'])} components (incl. the 4 of G0), {len(A['connectors'])} connectors, {len(abstract)} abstract left")
    for s in failed: print("    FAILED", s)
    r["refinement"] = steps
    r["architecture"] = {"components": A["components"], "connectors": [list(k) + list(v) for k, v in A["connectors"].items()]}
    rep = check_interfaces(A); r["interfaces"] = rep
    print("    interfaces:", {k: v for k, v in rep.items() if v} or "every connector binds a provided interface; every required interface is satisfied")
    json.dump(r, open(os.path.join(out, "result.json"), "w", encoding="utf-8"), indent=1, default=list)

    # ---- step 5: deploy (deployment.json -> docker-compose.yml, agent options, smoke test) and trace ----
    dep, unsupported = deploy(os.path.join(out, "result.json"), profile)
    trace(os.path.join(out, "result.json"))
    print(f"[5] DEPLOY  {dep}/docker-compose.yml ({profile} profile)" + (f"  |  not realised by the Aries stack: {unsupported}" if unsupported else ""))
    if profile == "indy": print(f"    run it:  python 12_play_diploma.py {dep}   (ledger von-network on :9000 first)")
    else: print(f"    run it:  cd {dep} && docker compose up -d && bash smoke_test.sh")
    print(f"    trace:   {out}/TRACE.md")

    if draw:
        from draw_arch import to_dot
        from refine import A0
        figs = [("g0", to_dot(A0(), [], edge_labels="payload", rankdir="TB")), ("architecture", to_dot(A, steps, edge_labels=True))]
        for name, text in figs:
            dot = os.path.join(out, name + ".dot"); open(dot, "w", encoding="utf-8").write(text)
            if shutil.which("dot"): subprocess.run(["dot", "-Tpng", "-Gdpi=200", dot, "-o", os.path.join(out, name + ".png")], stderr=subprocess.DEVNULL)
        print(f"    drawn:   {out}/g0.png (G0), {out}/architecture.png (G{len(applied)})" + ("" if shutil.which("dot") else "  [.dot only: install Graphviz]"))
    return r


def main():
    args = sys.argv[1:]; nfr = []; forbid = []; out = "out"; draw = False; profile = "no-ledger"
    if not args:   # run without arguments (e.g. the Run button of VS Code): the diploma case of the poster
        args = ["FR13", "FR17", "--nfr", "NFR04", "NFR07", "--out", "out_diploma", "--indy", "--draw"]
    if "--draw" in args: args.remove("--draw"); draw = True
    if "--indy" in args: args.remove("--indy"); profile = "indy"
    if "--out" in args: i = args.index("--out"); out = args[i + 1]; args = args[:i] + args[i + 2:]
    if "--forbid" in args: i = args.index("--forbid"); forbid = args[i + 1:]; args = args[:i]
    if "--nfr" in args: i = args.index("--nfr"); nfr = args[i + 1:]; args = args[:i]
    run(args or ["FR13", "FR17"], nfr or ["NFR04", "NFR07"], forbid, out, draw, profile)


if __name__ == "__main__":
    main()
