"""Shared: read FM_SSI.uvl and translate it into a propositional formula (Benavides et al. 2010, Table 3; Batory 2005).
root true; mandatory P <=> C; optional C => P; or P <=> (C1 v ... v Cn); alternative: same + not(Ci ^ Cj); requires A => B;
a function that needs one of several patterns: F => (P1 v ... v Pn)."""
import re, itertools, os
HERE = os.path.dirname(os.path.abspath(__file__))

FM_PATH = os.path.join(HERE, "..", "..", "2_feature_model", "FM_SSI.uvl")
KB_PATH = os.path.join(HERE, "..", "..", "1_knowledge_base", "SSI_Pattern_KnowledgeBase.xlsx")
def parse_uvl(path=FM_PATH):
    text = open(path, encoding="utf-8").read()
    feat_part = text.split("features\n", 1)[1].split("\nconstraints", 1)[0]
    cons_part = text.split("constraints", 1)[1]
    nodes, stack, rel_at, root = {}, [], {}, None
    for line in feat_part.splitlines():
        if not line.strip(): continue
        ind = len(line) - len(line.lstrip()); tok = line.strip()
        if tok in ("mandatory", "optional", "alternative", "or"): rel_at[ind] = tok; continue
        name = tok.split(" ")[0].split("{")[0]
        node = {"name": name, "children": [], "rel": None, "parent": None,
                "attrs": {k.lower(): int(v) for k, v in re.findall(r"(?i)(nfr\d\d) (-?\d)", tok)},
                "entities": (re.search(r"""entities ['"]([^'"]*)['"]""", tok) or [None, ""])[1],
                "optional": [x.strip() for x in (re.search(r"""(?:may_use|optional_patterns) ['"]([^'"]*)['"]""", tok) or [None, ""])[1].split(",") if x.strip()]}
        while stack and stack[-1][0] >= ind: stack.pop()
        if stack: node["rel"] = rel_at.get(ind - 4); node["parent"] = stack[-1][1]["name"]; stack[-1][1]["children"].append(node)
        else: root = node
        stack.append((ind, node)); nodes[name] = node
    cons, just, section = [], [], ""   # (a, [b]) for a => b, (a, [b1, b2, ...]) for a => (b1 | b2 | ...)
    for l in cons_part.splitlines():
        if l.strip().startswith("//"):
            if "JUSTIFICATION" in l: section = "justification"
            elif "->" in l: section = ""
            continue
        if "=>" not in l: continue
        a, b = (x.strip() for x in l.split("=>", 1))
        (just if section == "justification" else cons).append((a, [x.strip() for x in b.strip("() ").split("|") if x.strip()]))
    nodes["__justification__"] = just     # P => (its reasons), kept apart from the relations of the workbook
    return root, nodes, cons

class FM:
    def __init__(self, path=FM_PATH):
        from z3 import Bool, And, Or, Not, Implies
        self.root, self.nodes, self.constraints = parse_uvl(path)
        self.justification = self.nodes.pop("__justification__")
        self.FR = sorted(n for n in self.nodes if n.startswith("FR"))
        self.PAT = sorted(n for n in self.nodes if re.match(r"P\d\d_", n))
        self.DEC = []   # no decision features: alternatives are constraints F => (P1 | ... | Pn)
        self.V = {n: Bool(n) for n in self.nodes}
        V = self.V; clauses = [V[self.root["name"]]]
        def encode(n):
            kids = n["children"]; groups = [k for k in kids if k["rel"] in ("alternative", "or")]
            for k in kids:
                if k["rel"] == "mandatory": clauses.append(V[n["name"]] == V[k["name"]])
                else: clauses.append(Implies(V[k["name"]], V[n["name"]]))
            if groups:
                clauses.append(V[n["name"]] == Or([V[k["name"]] for k in groups]))
                if groups[0]["rel"] == "alternative":
                    for a, b in itertools.combinations(groups, 2): clauses.append(Not(And(V[a["name"]], V[b["name"]])))
            for k in kids: encode(k)
        encode(self.root)
        for a, bs in self.constraints + self.justification: clauses.append(Implies(V[a], V[bs[0]] if len(bs) == 1 else Or([V[b] for b in bs])))
        self.formula = And(clauses)
        one = [(a, bs[0]) for a, bs in self.constraints if len(bs) == 1]
        self.FRtoP = [(a, b) for a, b in one if a in self.FR and b in self.PAT]
        self.FRtoAny = [(a, bs) for a, bs in self.constraints if len(bs) > 1 and a in self.FR]   # one of several patterns
        self.FRtoFR = [(a, b) for a, b in one if a in self.FR and b in self.FR]
        self.PtoP = [(a, b) for a, b in one if a in self.PAT and b in self.PAT]
        # may_use, recovered from the justification: the functions that justify P without realising it
        realising = {(a, b) for a, b in self.FRtoP} | {(a, b) for a, bs in self.FRtoAny for b in bs}
        self.MayUse = [(f, p) for p, rs in self.justification for f in rs if f in self.FR and (f, p) not in realising]
    def full(self, x):            # "FR13" -> "FR13_VC_issuance", "P07" -> "P07_DID_Registry"
        return x if x in self.nodes else next(n for n in self.nodes if n.startswith(x + "_"))
    def pid(self, name): return name.split("_")[0]
    def check(self, *extra):
        from z3 import Solver, sat
        s = Solver(); s.add(self.formula, *extra); return s.check() == sat
