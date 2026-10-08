"""Activity 3: request -> partial configuration (+ justification, support) -> filter / optimization / explanation -> ordered sequence.
Single source of knowledge: the feature model FM_SSI.uvl written by build_fm.py (functions, patterns, constraints incl. F => (P1 | ... | Pn),
attributes NFRxx and optional_patterns).
usage: python selection.py FR13 FR17 --nfr NFR04 NFR07 [--forbid P07]"""
import sys, json
from z3 import And, Or, Not, Implies, Solver, Optimize, Sum, If, sat
from fm import FM

def optional_pairs(fm):
    """(function, pattern) pairs from the attribute optional_patterns of the function features: the pattern may complement
    the function; admitted by the justification (no constraint in the model)."""
    pairs = []
    for f in fm.FR:
        for p in fm.nodes[f].get("optional", []):
            try: pairs.append((f, fm.full(p)))
            except StopIteration: pass
    return pairs

def select(fm, fr_req, nfr_req, forbid=()):
    V = fm.V
    req = [fm.full(f) for f in fr_req]; nfrs = ["nfr" + n[3:] for n in nfr_req]
    # closure of the requested functions under the lifecycle constraints f => g
    closure = set(req); changed = True
    while changed:
        changed = False
        for a, b in fm.FRtoFR:
            if a in closure and b not in closure: closure.add(b); changed = True
    partial = [V[f] for f in closure] + [Not(V[f]) for f in fm.FR if f not in closure] + [Not(V[fm.full(p)]) for p in forbid]
    # justification: nothing the request does not call for
    just = []; opt = optional_pairs(fm)
    for p in fm.PAT:
        reasons = [V[f] for f, q in fm.FRtoP if q == p] + [V[f] for f, qs in fm.FRtoAny if p in qs] \
                  + [V[q] for q, r in fm.PtoP if r == p] + [V[f] for f, q in opt if q == p]
        just.append(Implies(V[p], Or(reasons) if reasons else False))
    # support: every requested property is strongly supported by some selected pattern (+2) ...
    # ... and strongly hindered (-2) by no AVOIDABLE pattern (one of several alternatives, optional complement).
    # A -2 pattern the request itself forces (mandatory for a required function or prerequisite of one) is allowed,
    # weighs negatively in the score, and is reported as a trade-off (NFR framework: conflicts are weighed, not vetoed).
    forced = {p for p in fm.PAT if not fm.check(Not(V[p]), *partial, *just)}
    support = [And(Or([V[p] for p in fm.PAT if fm.nodes[p]["attrs"].get(n) == 2] or [False]),
                   *[Not(V[p]) for p in fm.PAT if fm.nodes[p]["attrs"].get(n) == -2 and p not in forced]) for n in nfrs]
    tradeoffs = [f"{n}: strongly hindered by {fm.pid(p)} {' '.join(p.split('_')[1:])}, forced by the requested functions" for n in nfrs for p in forced if fm.nodes[p]["attrs"].get(n) == -2]
    res = {"request": {"FR": list(fr_req), "NFR": list(nfr_req), "forbid": list(forbid)}, "required_functions": sorted(closure)}
    res["valid_partial_configuration"] = fm.check(*partial, *just); res["tradeoffs"] = tradeoffs
    # filter: products of the request (projected on patterns)
    s = Solver(); s.add(fm.formula, *partial, *just); prods = set()
    while s.check() == sat and len(prods) < 10000:
        m = s.model(); prod = frozenset(p for p in fm.PAT if m.eval(V[p], model_completion=True)); prods.add(prod)
        s.add(Not(And([V[p] == m.eval(V[p], model_completion=True) for p in fm.PAT])))
    res["products"] = len(prods); res["commonality"] = sorted(frozenset.intersection(*prods)) if prods else []
    # optimization: minimize size, then maximize score of the requested properties
    o = Optimize(); o.add(fm.formula, *partial, *just, *support)
    size = Sum([If(V[p], 1, 0) for p in fm.PAT]); score = Sum([If(V[p], sum(fm.nodes[p]["attrs"].get(n, 0) for n in nfrs), 0) for p in fm.PAT])
    o.minimize(size); o.maximize(score)
    if o.check() != sat:
        s = Solver(); s.set(unsat_core=True); s.add(fm.formula, *just)
        s.assert_and_track(And(partial), "request")
        for n, c in zip(nfrs, support): s.assert_and_track(c, "support_" + n)
        s.check(); res["status"] = "UNSAT"; res["unsat_core"] = [str(c) for c in s.unsat_core()]
        res["explanation"] = explain(fm, closure, nfrs, forbid); return res
    m = o.model(); S = sorted(p for p in fm.PAT if m.eval(V[p], model_completion=True))
    res.update(status="SAT", size=len(S), score=m.eval(score).as_long(), selection=S)
    # where the request had a choice: the functions that need one of several patterns, and the patterns kept
    groups = {}
    for f, qs in fm.FRtoAny:
        if f in closure: groups.setdefault(tuple(qs), []).append(f.split("_")[0])
    res["choices"] = [{"for": frs, "among": [fm.pid(q) for q in qs], "chosen": [fm.pid(q) for q in qs if q in S]} for qs, frs in groups.items()]
    # reasons (traceability) and ordering
    res["reasons"] = {p: reasons_of(fm, p, S, closure, nfrs) for p in S}
    res["sequence"] = order(fm, S, closure); return res

def reasons_of(fm, p, S, closure, nfrs):
    r = [f"realizes {f.split('_')[0]}" for f, q in fm.FRtoP if q == p and f in closure]
    alts = {}
    for f, qs in fm.FRtoAny:
        if p in qs and f in closure: alts.setdefault(tuple(qs), []).append(f.split("_")[0])
    r += [f"chosen for {', '.join(frs)} among {'/'.join(fm.pid(q) for q in qs)}" for qs, frs in alts.items()]
    r += [f"required by {q.split('_')[0]}" for q, t in fm.PtoP if t == p and q in S]
    r += [f"supports {n.upper().replace('NFR', 'NFR')}" for n in nfrs if fm.nodes[p]["attrs"].get(n) == 2]
    return r

def explain(fm, closure, nfrs, forbid):
    out = []
    for n in nfrs:
        neg = [p for p in fm.PAT if fm.nodes[p]["attrs"].get(n) == -2]
        if not [p for p in fm.PAT if fm.nodes[p]["attrs"].get(n) == 2]: out.append(f"{n}: no pattern of the catalogue strongly supports it")
        elif not fm.check(Or([fm.V[p] for p in fm.PAT if fm.nodes[p]["attrs"].get(n) == 2]), *[fm.V[f] for f in closure]): out.append(f"{n}: no pattern that strongly supports it is compatible with the requested functions")
    for p in forbid:
        if not fm.check(Not(fm.V[fm.full(p)]), *[fm.V[f] for f in closure]): out.append(f"forbidden {p} is forced by the requested functions")
    return out

def order(fm, S, closure):
    fr_rank = {f: i for i, f in enumerate(fm.FR)}
    rank = {p: min([fr_rank[f] for f, q in fm.FRtoP if q == p and f in closure] + [fr_rank[f] for f, qs in fm.FRtoAny if p in qs and f in closure] or [99]) for p in S}
    seq, seen = [], set()
    def visit(p):
        if p in seen: return
        seen.add(p)
        for q, t in fm.PtoP:
            if q == p and t in S: visit(t)
        seq.append(p)
    for p in sorted(S, key=lambda p: (rank[p], p)): visit(p)
    return seq

if __name__ == "__main__":
    args = sys.argv[1:]; nfr = []; forbid = []
    if "--forbid" in args: i = args.index("--forbid"); forbid = args[i + 1:]; args = args[:i]
    if "--nfr" in args: i = args.index("--nfr"); nfr = args[i + 1:]; args = args[:i]
    r = select(FM(), args or ["FR13", "FR17"], nfr or ["NFR04", "NFR07"], forbid)
    print(json.dumps(r, indent=1))
