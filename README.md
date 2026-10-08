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
| `console.txt` | the run: 15 FR needed, the 4 choices among alternatives, the 10 patterns in order with their reasons, 10 rules applied | §5, §6 |
| `fm.png` | the part of the feature model the request uses, selection marked, drawn by `15_draw_fm.py` from FM_SSI.uvl and result.json | §5 |
| `result.json` | the same as data: selection, order, every refinement step, the architecture (28 components incl. the 4 of G0, 22 connectors) | §5, §6 |
| `g0.png` | G0, the abstract SSI architecture (3 roles, registry, 5 interactions), drawn from rules.json | §1 |
| `architecture.png` | G10, each box tagged with the pattern that added it | §6 |
| `selection_table.csv`, `.md` | the table of section 5, written by `13_tables.py` from result.json and FM_SSI.uvl | §5 |
| `TRACE.md`, `trace.csv` | FR → pattern → components → what it becomes in the Aries stack | §3 |
| `deploy/` | the generated `docker-compose.yml`, the options of each agent (`*.args`), `DEPLOY.md` | §7 |

`evidence/` holds the record exported from the verifier agent when the deployment was played on 5 Oct 2026
(`state: done`, `verified: true`, only `degree` revealed).

## Run it

Requirements: Python 3.12 (flamapy has no wheels for 3.13 yet), `pip install -r requirements.txt`; Graphviz for `--draw`;
Docker and the von-network ledger for step 5.

```bash
# step 2 - after any change of the knowledge base (once per catalogue)
cd 2_feature_model
python 01_build_fm.py            # part A -> FM_SSI.uvl (features, constraints, attributes NFRxx)
python 02_build_rules.py         # parts B, C -> rules.json (G0 and the rule of each pattern), deployment.json (pattern -> Aries stack)
python 03_check_fm_flamapy.py    # independent check of FM_SSI.uvl with flamapy: satisfiable, dead, false-optional, core

# steps 3-4-5 - one request, about one second
cd ../3_generator
python 10_generate.py FR13 FR17 --nfr NFR04 NFR07 --out out_diploma --indy --draw
python 13_tables.py out_diploma/result.json
python 14_check_figure.py out_diploma     # the figure is an execution: re-runs the rules, compares with result.json and architecture.dot
python 15_draw_fm.py out_diploma          # the feature model the request uses, selection marked -> fm.png

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
   part A  FR, NFR, P, mandatory (a pattern, or one of several: P38 | P39 | P40), optional, requires, depends, affects   -> FM_SSI.uvl
   part B  G0 (abstract architecture), Rules (R,F)                                         -> rules.json
   part C  Deployment (Aries), Interfaces, Connectors                                      -> deployment.json
2_feature_model/   01_build_fm.py, 02_build_rules.py, 03_check_fm_flamapy.py and the three generated files
3_generator/       10_generate.py (steps 3-5; --draw writes g0.png and architecture.png), 11_run_scenarios.py (optional),
                   12_play_diploma.py (step 5, test), 13_tables.py (the poster's selection table),
                   14_check_figure.py (re-executes the refinement and checks the figure against it),
                   15_draw_fm.py (draws the part of FM_SSI.uvl a request uses)
   lib/fm.py          FM_SSI.uvl -> propositional formula (Benavides et al. 2010)
   lib/selection.py   step 3: request -> partial configuration; filter, optimization (smallest set, then best NFR score), explanation
   lib/refine.py      step 4: match R by name, f_R = add / replace an abstract edge of G0 / refine a type; order of application
   lib/interfaces.py  well-formedness: every connector binds an existing interface
   lib/deploy.py      step 5: pattern -> services, agent options, tests of the Aries stack (no-ledger or Indy profile)
   lib/trace.py       FR -> pattern -> components -> deployment
   lib/draw_arch.py   optional drawing of the architecture (--draw)
example_diploma/   output of the diploma case;   evidence/   record of the deployed run
```

## Limits (as on the poster)

Rules are written for 20 of the 35 patterns (a pattern without a rule is reported as skipped, never dropped silently);
deployment mappings exist for the same 20; one scenario was played end to end, on one stack (Hyperledger Aries).
