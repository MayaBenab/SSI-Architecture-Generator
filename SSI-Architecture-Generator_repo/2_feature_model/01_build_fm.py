"""Step 2 (offline, once per catalogue): part A of the knowledge base -> FM_SSI.uvl.

Build SSI Feature Model in UVL format for Flamapy.

Input:
    ../1_knowledge_base/SSI_Pattern_KnowledgeBase.xlsx

Output:
    FM_SSI.uvl

The generated UVL intentionally does NOT use a namespace,
to maximize compatibility with FlamapyIDE.

The model contains:
- Functions
- Patterns
- Alternatives: a function needs one of several patterns (constraint f => (p1 | p2 | ...))
- Alternative / OR groups
- Feature cardinalities
- Cross-tree constraints (horizontal relationships)
"""

import os
import re
import openpyxl
from collections import defaultdict, OrderedDict


# ============================================================
# 1. Paths
# ============================================================

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)

KB = os.path.join(
    HERE,
    "..",
    "1_knowledge_base",
    "SSI_Pattern_KnowledgeBase.xlsx"
)

OUTPUT = os.path.join(HERE, "FM_SSI.uvl")


# ============================================================
# 2. Read Excel knowledge base
# ============================================================

print("Lecture du fichier :", os.path.abspath(KB))

wb = openpyxl.load_workbook(KB, data_only=True)


def rows(sheet_name):
    """
    Read a sheet as a list of dictionaries.
    """
    ws = wb[sheet_name]

    headers = [cell.value for cell in ws[1]]

    result = []

    for row in ws.iter_rows(
        min_row=2,
        values_only=True
    ):
        if row[0]:
            result.append(
                dict(zip(headers, row))
            )

    return result


# ============================================================
# 3. Load main entities
# ============================================================

fr = OrderedDict(
    (r["id"], r)
    for r in rows("FR")
)

patterns = OrderedDict(
    (r["id"], r)
    for r in rows("P")
)


# ============================================================
# 4. Relationships from knowledge base
# ============================================================

mandatory_patterns = defaultdict(list)
# realised_by: one pattern ("P24") or one of several alternatives ("P38 | P39 | P40")
mandatory_patterns = defaultdict(list)

for r in rows("realised_by"):
    mandatory_patterns[r["fr"]].append(
        [x.strip() for x in str(r["p"]).split("|") if x.strip()]
    )


# Optional complements: the pattern may complement the function (no constraint;
# kept as an attribute of the function feature, read by the selection's justification)
may_use_patterns = defaultdict(list)

for r in rows("may_use"):
    may_use_patterns[r["fr"]].append(r["p"])


pattern_requires = sorted(
    {
        (r["p"], r["requires q"])
        for r in rows("requires")
    }
)


# NFR influence
affects = defaultdict(dict)

rank = {
    "++": 2,
    "+": 1,
    "−": -1,
    "−−": -2
}

for r in rows("affects"):

    p = r["p"]
    nfr = r["nfr"]
    label = r["label"]

    current = affects[p].get(nfr)

    if current is None:
        affects[p][nfr] = rank[label]

    elif abs(rank[label]) > abs(current):
        affects[p][nfr] = rank[label]


# ============================================================
# 5. UVL identifiers
# ============================================================

def ident(value):
    """
    Convert Excel names into safe UVL identifiers.
    """

    value = str(value)

    value = re.sub(
        r"[^A-Za-z0-9_]+",
        "_",
        value
    )

    value = value.strip("_")

    if not value:
        value = "Feature"

    return value


def feature_name(feature_id):
    """
    Function feature name.
    """

    name = str(
        fr[feature_id]["name"]
    )

    return (
        f"{feature_id}_"
        f"{ident(name)}"
    )


def pattern_name(pattern_id):
    """
    Pattern feature name.
    """

    # the short name of the knowledge base (sheet P), the one name used in every figure
    name = str(patterns[pattern_id].get("short name") or str(patterns[pattern_id]["name"]).split("(")[0].strip())

    return (
        f"{pattern_id}_"
        f"{ident(name)}"
    )


# ============================================================
# 6. Pattern entities
# ============================================================

def pattern_entities(pattern_id):

    value = patterns[pattern_id]["entities"]

    if value is None:
        return []

    return [
        x.strip()
        .replace("→", "->")
        .replace("–", "-")
        .replace("|", "/")
        for x in str(value).split(",")
        if x.strip()
    ]


# ============================================================
# 7. Pattern attributes
# ============================================================

def pattern_attributes(pattern_id):

    entities = pattern_entities(pattern_id)

    attributes = []

    # Keep entities as an informational UVL attribute.
    if entities:
        entity_string = ", ".join(entities)

        attributes.append(
            f"entities '{entity_string}'"
        )

    # NFR values are stored as informational attributes.
    for nfr, value in sorted(
        affects[pattern_id].items()
    ):

        attributes.append(
            f"{nfr} {value}"
        )

    if not attributes:
        return ""

    return " {" + ", ".join(attributes) + "}"


# ============================================================
# 8. Feature cardinality
# ============================================================

def pattern_cardinality(pattern_id):

    entities = pattern_entities(pattern_id)

    # Keep the original project logic:
    # patterns involving several entities receive
    # a feature cardinality.
    if len(entities) > 1:
        return f" cardinality [1..{len(entities)}]"

    return ""


def pattern_definition(pattern_id):

    attributes = pattern_attributes(pattern_id)

    return (
        f"{pattern_name(pattern_id)}"
        f"{attributes}"
    )


# ============================================================
# 10. Build UVL
# ============================================================

L = []


# ------------------------------------------------------------
# Header
# ------------------------------------------------------------

L.append(
    "// FM_SSI - SSI Feature Model"
)

L.append(
    "// Generated automatically from "
    "SSI_Pattern_KnowledgeBase.xlsx"
)

L.append(
    "// Compatible with FlamapyIDE"
)

L.append("")


# ------------------------------------------------------------
# FEATURES
# ------------------------------------------------------------

L.append("features")

L.append("    SSI_system")

L.append("        mandatory")


# ------------------------------------------------------------
# FUNCTIONS
# ------------------------------------------------------------

L.append("            Functions")

L.append("                optional")

for f in fr:

    L.append(
        f"                    {feature_name(f)}"
    )


# ------------------------------------------------------------
# PATTERNS, grouped by the catalogue's categories (abstract features); the alternatives of a function are constraints
# ------------------------------------------------------------

L.append(
    "            Patterns"
)

L.append(
    "                optional"
)

categories = OrderedDict()
for p in patterns:
    categories.setdefault(str(patterns[p]["category"]), []).append(p)

for category, members in categories.items():

    L.append(
        f"                    {ident(category)} {{abstract}}"
    )

    # or-group: the (abstract) category is present iff at least one of its patterns is
    L.append(
        "                        or"
    )

    for p in members:
        L.append(
            "                            "
            + pattern_definition(p)
        )


# ============================================================
# CROSS-TREE CONSTRAINTS
# ============================================================

L.append("")

L.append("constraints")

L.append(
    "    // ==================================================="
)

L.append(
    "    // FUNCTION -> PATTERN"
)

L.append(
    "    // Horizontal requires relationships"
)

L.append(
    "    // ==================================================="
)


# ------------------------------------------------------------
# Function requires mandatory pattern
# ------------------------------------------------------------

for f in fr:

    for group in mandatory_patterns[f]:

        group = [p for p in group if p in patterns]

        if not group:
            continue

        # one pattern, or one of several alternatives (at least one of them)
        rhs = pattern_name(group[0]) if len(group) == 1 else "(" + " | ".join(pattern_name(p) for p in group) + ")"

        L.append(
            f"    {feature_name(f)} "
            f"=> "
            f"{rhs}"
        )

# ------------------------------------------------------------
# Function lifecycle dependencies
# ------------------------------------------------------------

L.append("")

L.append(
    "    // ==================================================="
)

L.append(
    "    // FUNCTION -> FUNCTION"
)

L.append(
    "    // Lifecycle dependencies"
)

L.append(
    "    // ==================================================="
)


for r in rows("depends"):

    f = r["f"]
    g = r["depends on g"]

    if f in fr and g in fr:

        L.append(
            f"    {feature_name(f)} "
            f"=> "
            f"{feature_name(g)}"
        )


# ------------------------------------------------------------
# Pattern -> Pattern dependencies
# ------------------------------------------------------------

L.append("")

L.append(
    "    // ==================================================="
)

L.append(
    "    // PATTERN -> PATTERN"
)

L.append(
    "    // Pattern requires relationships"
)

L.append(
    "    // ==================================================="
)


for p, q in pattern_requires:

    if p in patterns and q in patterns:

        L.append(
            f"    {pattern_name(p)} "
            f"=> "
            f"{pattern_name(q)}"
        )


# ------------------------------------------------------------
# Pattern -> its reasons (justification)
#   P => (F1 | ... | Q1 | ...): a pattern is present only if a function or a pattern calls for it.
#   The reasons of P are read backwards from three relations of the workbook:
#   realised_by (F => P, or F => (... | P | ...)), may_use (F may use P), requires (Q => P).
#   One constraint per pattern, with all its reasons (one constraint per reason would demand all of them).
# ------------------------------------------------------------

L.append("")
L.append("    // ===================================================")
L.append("    // JUSTIFICATION: PATTERN -> ITS REASONS")
L.append("    // realised_by and requires read backwards, and may_use")
L.append("    // ===================================================")

reasons = OrderedDict((p, []) for p in patterns)
for f in fr:
    for group in mandatory_patterns[f]:
        for p in group:
            if p in reasons and f not in reasons[p]: reasons[p].append(f)
for f in fr:
    for p in may_use_patterns[f]:
        if p in reasons and f not in reasons[p]: reasons[p].append(f)
for q, p in pattern_requires:
    if p in reasons and q in patterns and q not in reasons[p]: reasons[p].append(q)

n_justification = 0
for p, rs in reasons.items():
    if not rs:
        continue          # no reason at all: the pattern stays free (reported below)
    names = [feature_name(r) if r in fr else pattern_name(r) for r in rs]
    rhs = names[0] if len(names) == 1 else "(" + " | ".join(names) + ")"
    L.append(f"    {pattern_name(p)} => {rhs}")
    n_justification += 1
no_reason = [p for p, rs in reasons.items() if not rs]


# ============================================================
# 11. Write file
# ============================================================

with open(
    OUTPUT,
    "w",
    encoding="utf-8"
) as file:

    file.write(
        "\n".join(L) + "\n"
    )


# ============================================================
# 12. Statistics
# ============================================================

feature_lines = 0
constraint_lines = 0

inside_constraints = False

for line in L:

    if line.strip() == "constraints":
        inside_constraints = True
        continue

    if inside_constraints:

        if "=>" in line:
            constraint_lines += 1

    elif line.strip() and not line.strip().startswith("//"):

        # Approximate count of feature lines
        if (
            not line.strip()
            in {
                "features",
                "mandatory",
                "optional",
                "alternative",
                "or"
            }
        ):
            feature_lines += 1


print()
print("=" * 60)
print("FM_SSI.uvl généré avec succès")
print("=" * 60)

print(
    "Fichier      :",
    os.path.abspath(OUTPUT)
)
print("Justification: " + str(n_justification) + " constraints P => reasons" + (f"; patterns with no reason: {no_reason}" if no_reason else ""))

print(
    "Functions    :",
    len(fr)
)

print(
    "Alternatives :",
    sum(1 for f in fr for g in mandatory_patterns[f] if len(g) > 1),
    "(function => one of several patterns)"
)

print(
    "Patterns     :",
    len(patterns)
)

print(
    "Constraints  :",
    constraint_lines
)

print("=" * 60)
print()
print(
    "Le fichier est prêt pour FlamapyIDE."
)