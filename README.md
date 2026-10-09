# SSI architecture generator

From the functional (FR) and non-functional requirements (NFR) of an SSI system to a traced architecture and a running
system. This folder follows the five steps of the poster (section 3); the numbers of the scripts say what to run.

```
 1 Read (by hand)      2 Write (script)                3 Select & order   4 Refine        5 Deploy & test
 knowledge base  ───►  FM_SSI.uvl, rules.json,   ───►  Z3 on the       ─► rules (R,F,f) ─► Aries agents,
 (Excel, sourced)      deployment.json                 feature model      from G0          Indy ledger
 1_knowledge_base/     2_feature_model/ 01, 02, 03     3_generator/ 10 ──────────────────────► 12
```

Each step reads one generated file, never the workbook.

## See it without running anything: `example_diploma/`

Every figure and table of the poster is a file of this folder, written by the scripts (`--draw`, `13_tables.py`); none is drawn by hand.

The diploma case of the poster (request FR13 VC issuance, FR17 VP presentation; NFR04 privacy, NFR07 security):

| file | what it shows | poster |
|---|---|---|
| `console.txt` | the run: 15 FR needed, the 4 choices among alternatives, the 9 patterns with their reasons, the 5 steps of the DAG, 9 rules applied | §5, §6 |
| `fm.png`, `fm_constraints.txt` | the feature tree seen from the request: the 15 FR needed (the 19 others folded), the 6 categories (2 not needed, folded), 16 of the 40 patterns with their attributes on the asked NFR (e.g. P25 [+2, +1]), selection in blue; and its 29 cross-tree constraints. Written by `15_draw_fm.py` from FM_SSI.uvl and result.json | §5 |
| `result.json` | the same as data: selection, order, every refinement step, the architecture (25 components incl. the 5 of G0, 20 connectors) | §5, §6 |
| `g0.png` | G0, the abstract SSI architecture (3 roles, registry, 5 interactions), drawn from rules.json | §1 |
| `architecture.png` | G9, each box tagged with the pattern that added it; what P25 added in orange (`--highlight P25`) | §6 |
| `selection_table.csv`, `.md` | the table of section 5, written by `13_tables.py` from result.json and FM_SSI.uvl | §5 |
| `TRACE.md`, `trace.csv` | FR → pattern → components → what it becomes in the Aries stack | §3 |
| `deploy/` | the generated `docker-compose.yml`, the options of each agent (`*.args`), `DEPLOY.md` | §7 |

`evidence/` holds the record exported from the verifier agent when the deployment was played on 5 Oct 2026
(`state: done`, `verified: true`, only `degree` revealed).

## The feature model, formally

`FM_SSI.uvl` is an extended (attributed) feature model [Benavides et al. 2010], written by `01_build_fm.py` from part A of the workbook:

- **Features** F: the root `SSI_system`; its two mandatory children `Functions` and `Patterns`; the 34 functions FR (optional
  children of `Functions`); the 6 categories of the catalogue (abstract features, optional children of `Patterns`); the 40
  patterns P (an or-group under their category).
- **Tree constraints** T: every feature implies its parent; `Functions` ⇔ `SSI_system`, `Patterns` ⇔ `SSI_system`;
  a category ⇔ (p1 ∨ … ∨ pk), its patterns (or-group: an abstract category is present iff one of its patterns is).
- **Attributes** A: a(p, n) ∈ {−2, −1, +1, +2} for a pattern p and a property n (sheet `affects`: ++ + − −−); `entities`,
  the roles a pattern involves. An attribute is a value of the feature itself, never a link to another feature.
- **Cross-tree constraints** C (every link between two features):
  - `realised_by`  f ⇒ p, or f ⇒ (p1 ∨ … ∨ pk) when the function has alternatives (at least one of them);
  - `requires`     p1 ⇒ p2 (a pattern needs another pattern);
  - `depends`      f ⇒ g (presence only: the lifecycle order is used later, by the refinement);
  - justification  p ⇒ ∨ reasons(p), with reasons(p) = {f | p in realised_by(f)} ∪ {f | f may_use p} ∪ {p2 | p2 requires p}:
    a pattern is present only if a function or a pattern calls for it. `may_use` exists only here: it allows a pattern,
    never imposes it. One constraint per pattern, with all its reasons.
- **Products**: ⟦FM⟧ = { S ⊆ F | S satisfies T and C }.

A request (FR_req, NFR_req) is a partial configuration: f ∈ S for the functions of FR_req closed under `depends`,
f ∉ S for the others. The selection keeps the products of the request where every n ∈ NFR_req is strongly supported
(∃ p ∈ S, a(p, n) = +2) and not strongly hindered by an avoidable pattern (no a(p, n) = −2 unless the request forces p),
and returns S* = argmin |S ∩ P|, then argmax Σ_{p ∈ S ∩ P} Σ_{n ∈ NFR_req} a(p, n) (Z3, `lib/selection.py`).

## Run it

Requirements: Python 3.12 (flamapy has no wheels for 3.13 yet), `pip install -r requirements.txt`; Graphviz for `--draw`;
Docker and the von-network ledger for step 5.

```bash
# step 1 - once per catalogue: the Related Patterns of the catalogue's own workbook -> sheet 'related (catalogue)'
cd 1_knowledge_base && python 00_catalogue_links.py && cd ..

# step 2 - after any change of the knowledge base (once per catalogue)
cd 2_feature_model
python 01_build_fm.py            # part A -> FM_SSI.uvl (features, constraints, attributes NFRxx)
python 02_build_rules.py         # parts B, C, D -> rules.json (G0, rules), deployment.json (component / connector -> Aries stack), order_sources.json (catalogue links, lifecycles)
python 03_check_fm_flamapy.py    # analysis of the feature model with flamapy: void, dead, false-optional, core features
python 04_analyse_fm.py          # the same analysis on our own encoding (lib/fm.py, Z3), cross-check -> fm_analysis.json

# steps 3-4-5 - one request, about one second
cd ../3_generator
python 10_generate.py FR13 FR17 --nfr NFR04 NFR07 --out out_diploma --indy --draw --highlight P25   # P25 in orange in G9
python 13_tables.py out_diploma/result.json
python 14_check_figure.py out_diploma     # the figure is an execution: re-runs the rules, compares with result.json and architecture.dot
python 15_draw_fm.py out_diploma          # the feature tree the request uses, selection marked -> fm.png, fm_constraints.txt
python 16_check_order.py out_diploma      # the order is a DAG of insertions: P -> Q when an output of P is an anchor (R) of Q; arcs
                                          # compared with the catalogue (Related Patterns, lifecycles); every order gives the same G_n -> order_dag.png

# step 5 - test: the ledger first, then the scenario on the generated deployment
git clone https://github.com/bcgov/von-network && cd von-network && ./manage build && ./manage start && cd -
python 12_play_diploma.py out_diploma/deploy
```

`12_play_diploma.py` registers the issuer's and verifier's public DIDs on the ledger, starts the three agents, creates the
diploma schema and credential definition, connects the holder to both (one pairwise did:peer each), issues the diploma,
asks for `degree` only and prints `verified: true`; the verifier's record is exported next to the deployment.

Other requests: `python 10_generate.py <FR...> --nfr <NFR...> [--forbid P07]` (without `--indy`: a deployment with no
ledger, runnable at once with `docker compose up -d && bash smoke_test.sh`). `python 11_run_scenarios.py` runs the seven
requests of the paper (S7 shows an impossible request returned with its explanation).

## What is where

```
1_knowledge_base/SSI_Pattern_KnowledgeBase.xlsx   the only source (sheet README lists the others); every row cites its source
   sources/SSIpatternsCatalog23.xlsx   the catalogue's own workbook [1]
   00_catalogue_links.py   its 'Related Patterns' items -> sheet 'related (catalogue)' (196 items, 129 pairs)
   draw_kb.py   draws the knowledge base (sources, FR / P / NFR, relations with their counts) -> kb.png (poster section 4)
   part A  FR, NFR, P, realised_by (FR -> a pattern, or one of several: P38 | P39 | P40), may_use (FR -> P, read as part of the justification P => reasons), requires (P -> P), depends (FR -> FR), affects (P -> NFR)   -> FM_SSI.uvl
   part B  G0 (abstract architecture), Rules (R,F)                                         -> rules.json
   part C  Deployment (components), Interfaces, Connectors                                 -> deployment.json
   part D  related (catalogue), lifecycle states, lifecycle (patterns) [figure of [1]]     -> order_sources.json
           (not constraints: they justify the order; requires.origin = catalogue / proposed / variant)
2_feature_model/   01_build_fm.py, 02_build_rules.py, 03_check_fm_flamapy.py and the three generated files
3_generator/       10_generate.py (steps 3-5; --draw writes g0.png and architecture.png), 11_run_scenarios.py (optional),
                   12_play_diploma.py (step 5, test), 13_tables.py (the poster's selection table),
                   14_check_figure.py (re-executes the refinement and checks the figure against it),
                   15_draw_fm.py (draws the part of FM_SSI.uvl a request uses),
                   16_check_order.py (the precedence DAG: P -> Q when F_P ∩ R_Q ≠ ∅, arc = anchor; 9 of 13 arcs backed by [1]; all orders give the same G_n)
   lib/fm.py          FM_SSI.uvl -> propositional formula (Benavides et al. 2010)
   lib/selection.py   step 3: request -> partial configuration; filter, optimization (smallest set, then best NFR score), explanation; returns a set of patterns (no order)
   lib/refine.py      step 4: match R by subgraph isomorphism on types and containment (VF2); precedence (P -> Q when Q needs, in R, a component P adds, in F), rows of the DAG, refine_dag (row by row);
                      match R by name, f_R = add / replace an abstract edge of G0 / refine a type
   lib/interfaces.py  well-formedness: every connector binds an existing interface
   lib/deploy.py      step 5: what is deployed are the components and connectors of G_n (a pattern is a graph transformation):
                      each component in the agent of its role, as the row of its type says; each connector by its protocol
   lib/trace.py       FR -> pattern -> components -> deployment
   lib/draw_arch.py   optional drawing of the architecture (--draw)
example_diploma/   output of the diploma case;   evidence/   record of the deployed run
```

## Complexity

- Select (step 3): NP-hard in general (feature-model analysis reduces to SAT, Benavides et al. 2010); here 83 Boolean
  variables and 146 constraints, solved by Z3 (optimisation: smallest set, then best NFR score) in about a second.
- Order (step 4): Kahn's topological sort by levels (Kahn 1962) on the DAG P -> Q iff F_P ∩ R_Q ≠ ∅: O(n + e)
  after building the DAG in O(n² k) (n patterns, k = largest R or F).
- Refine (step 4): as in Guth & Leymann, R is a typed fragment (each required element with its type and the role or
  container it lies in) and is found in G by subgraph isomorphism (VF2, Cordella et al. 2004, via networkx):
  NP-complete in general, here |R| ≤ 7 nodes in |G| ≤ 30; every rule of the diploma case has exactly one match.
  f_R then inserts F at the match, O(|F| + |D|).
- 16_check_order.py enumerates every order of the DAG (exponential, a verification only).

## Limits (as on the poster)

The catalogue has 35 patterns, 40 with their variants in the knowledge base. Rules are written for 20 of the 40 (a pattern
without a rule is reported as skipped, never dropped silently); the deployment realises 28 of the 37 component types and 11 of the 14
connector protocols on the Aries stack; one scenario was played end to end, on one stack (Hyperledger Aries).
