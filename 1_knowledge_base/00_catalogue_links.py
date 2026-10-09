"""Step 0 (offline, once per catalogue): the 'Related Patterns' field of every pattern of the catalogue [1]
(the catalogue's own workbook, published by its authors; it is not redistributed here) -> sheet 'related (catalogue)' of the knowledge base.
Each numbered item 'n. Name: text' of a pattern's Related Patterns is matched to our pattern ids by name; one row per
(pattern, related pattern, item). The links are undirected in the catalogue ('these two patterns are related'); they are
used to justify the order of the refinement (3_generator/16_check_order.py), never as constraints of the feature model.
usage: python 00_catalogue_links.py <path to the catalogue workbook (SSIpatternsCatalog23.xlsx)>
The sheet 'related (catalogue)' it produced is already in the knowledge base: this script is only needed to rebuild it."""
import os, re, sys, openpyxl
HERE = os.path.dirname(os.path.abspath(__file__))
if len(sys.argv) < 2: sys.exit("usage: python 00_catalogue_links.py <path to SSIpatternsCatalog23.xlsx> (the catalogue's workbook, from its authors)")
CAT = sys.argv[1]
KB = os.path.join(HERE, "SSI_Pattern_KnowledgeBase.xlsx")

ALIAS = [  # (substring of the item title or pattern name, lower case) -> id ; the most specific first
    ("linking onboarding", "P11"), ("onboarding or did registration", "P10"), ("onboarding service registry", "P02"),
    ("trusted registration authority registry", "P02"), ("trusted accreditation registry", "P03"),
    ("trusted issuer registry", "P04"), ("trusted schema", "P05"), ("public institution registry", "P01"),
    ("status registry", "P06"), ("revocation and endorsement registry", "P06"), ("identifier-attribute", "P08"),
    ("did registry", "P07"), ("identifier registry", "P07"), ("blockchain anchor", "P09"),
    ("verifiable id", "P12"), ("verifiable attestation", "P13"), ("verifiable mandate", "P14"),
    ("verifiable accreditation", "P15"), ("verifiable authorization", "P16"), ("selective content", "P17"),
    ("time-constrained", "P18"), ("one-off", "P19"), ("expiration time", "P20"), ("effective time", "P21"),
    ("validity time", "P21"), ("multiple registration", "P22"), ("social media", "P23"), ("public did", "P24"),
    ("public/anywise", "P24"), ("anywise did", "P24"), ("pairwise", "P25"), ("static did", "P26"),
    ("delegate list", "P30"), ("did controller", "P31"), ("master and sub", "P32"), ("key shards", "P33"),
    ("key sharding", "P33"), ("qualified verifiable credentials", "P34"), ("binding vcs", "P35"),
    ("binding dids", "P36"), ("hot and cold", "P37"), ("local (private) storage", "P38"), ("local storage", "P38"),
    ("cloud storage", "P39"), ("identity hub", "P40")]
VC = {"v-id": "P12", "va": "P13", "vm": "P14", "vacc": "P15", "vauth": "P16"}


def ids(title, body=""):
    t = title.lower().strip()
    if t in ("onboarding",): return ["P10"]
    if t in ("qualified electronic certificates",): return ["P34"]
    if "resolution" in t:
        return ["P28"] if "on-chain" in t else ["P29"] if "off-chain" in t else ["P27"]
    out = []
    for a, p in ALIAS:
        if a in t and p not in out:
            if a == "trusted issuer registry" and "trusted issuers" in t: pass
            out.append(p)
    if not out and t.startswith("verifiable credential"):          # generic 'Verifiable Credentials (V-ID, VA, ...)'
        out = [VC[x] for x in re.findall(r"v-id|vacc|vauth|va|vm", (t + " " + body).lower()) if VC.get(x)]
        out = list(dict.fromkeys(out))
    return out


wb = openpyxl.load_workbook(CAT, data_only=True)
names = {r[0]: r[1] for r in openpyxl.load_workbook(KB, read_only=True)["P"].iter_rows(min_row=2, values_only=True) if r[0]}
rows, unmatched = [], []
for ws in wb.worksheets[1:]:
    data = list(ws.iter_rows(values_only=True)); h = list(data[0])
    ci, ni = h.index("Related Patterns"), h.index("Name")
    prev = 0.0
    for r in data[1:]:
        if not r[ni] or not r[ci]: continue
        if isinstance(r[0], float):                     # the workbook stores 3.10 as the number 3.1
            rid = f"{r[0]}0" if r[0] < prev else str(r[0]); prev = float(rid.split("/")[0]); r = (rid,) + tuple(r[1:])
        me = ids(str(r[ni]).split("\n")[0])
        if len(me) != 1: unmatched.append(("pattern", str(r[ni]).split("\n")[0])); continue
        fiche = " ".join(str(r[0]).split()).replace(" ", "/") if r[0] not in (None, "None") else str(r[ni]).split("\n")[0].strip()
        if "." not in fiche and len(fiche) <= 2: fiche = f"{ws.title.split('.')[0]}.{fiche}"   # sheet 6 numbers 1, 2, 3, X
        for m in re.finditer(r"(?m)^\s*(\d+)\.\s*(.+?)(?=^\s*\d+\.\s|\Z)", str(r[ci]), re.S):
            num, item = m.group(1), " ".join(m.group(2).split())
            title, _, body = item.partition(":")
            qs = [q for q in ids(title, body) if q != me[0]]
            if not qs: unmatched.append((me[0], item[:70])); continue
            for q in qs: rows.append((me[0], q, f"{fiche} #{num}", item))

kb = openpyxl.load_workbook(KB)
if "related (catalogue)" in kb.sheetnames: del kb["related (catalogue)"]
ws = kb.create_sheet("related (catalogue)", kb.sheetnames.index("requires") + 1)
ws.append(["p", "p name", "related q", "q name", "catalogue item", "quotation (Related Patterns of p)"])
for p, q, ref, item in rows: ws.append([p, names[p], q, names[q], ref, item])
for col, w in zip("ABCDEF", (6, 34, 9, 34, 22, 120)): ws.column_dimensions[col].width = w
kb.save(KB)
pairs = {frozenset((p, q)) for p, q, _, _ in rows}
print(f"related (catalogue): {len(rows)} items, {len(pairs)} distinct pairs of patterns")
print("items not matched to a pattern of ours (oracles, digital wallet, generic DIDs, ...):")
for u in unmatched: print("  ", u)
