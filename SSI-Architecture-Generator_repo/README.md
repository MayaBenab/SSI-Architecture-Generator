# SSI Architecture Generator

Generates a deployable Self-Sovereign Identity (SSI) architecture from a request (functional requirements FR + non-functional requirements NFR), using the SSI pattern catalogue of Čučko et al. (2023) and pattern-based refinement as in Guth & Leymann (2020).

## Pipeline

| Step | What | Where |
|---|---|---|
| 1. Knowledge base | FR, patterns, NFR, rules (R, F) built by hand from the catalogue | `1_knowledge_base/SSI_Pattern_KnowledgeBase.xlsx` |
| 2. Feature model | KB → extended feature model (UVL), rules, deployment, order sources | `2_feature_model/01_build_fm.py`, `02_build_rules.py` |
| 3. Select | Z3: minimal set of patterns covering the FR, then best NFR score | `3_generator/lib/selection.py` |
| 4. Order & refine | DAG P → Q iff F_P ∩ R_Q ≠ ∅, levels by Kahn's sort; R matched by subgraph isomorphism (VF2); G_i = f_R(G_{i-1}) | `3_generator/lib/refine.py` |
| 5. Deploy | Aries agents (ACA-Py), Indy ledger profile | `3_generator/lib/deploy.py` |

## Run

```bash
pip install -r requirements.txt          # Graphviz is also needed for the figures
cd 2_feature_model && python 01_build_fm.py && python 02_build_rules.py && cd ..
python 3_generator/10_generate.py --draw   # diploma case -> 3_generator/out_diploma/
python 3_generator/16_check_order.py       # DAG of the order, checked against the catalogue
```

Optional: `11_run_scenarios.py` (7 evaluation scenarios), `03_check_fm_flamapy.py` / `04_analyse_fm.py` (FM analysis),
`12_play_diploma.py` (plays the diploma case on a running Indy deployment), `13_tables.py`, `14_check_figure.py`, `15_draw_fm.py`.

## Example: diploma case (`example_diploma/`)

Request FR13 FR17, NFR04 NFR07.
- Selected: 10 patterns (P05, P07, P12, P17, P24, P25, P27, P29, P32, P38), NFR score 17.
- Order: 13 arcs in 5 steps (`order_dag.png`, `order_check.txt`); all 426 valid orders give the same architecture.
- Result G10: 30 components, 25 connectors (`architecture.png`), from G0 (`g0.png`).
- Deployment files in `deploy/`; execution evidence in `evidence/`.

## Complexity

Select: NP-hard (SAT). Order: O(n + e) (Kahn 1962). Matching: NP-complete in general (Cordella et al. 2004), small here (|R| ≤ 7, |G| ≤ 30).

## Catalogue

The catalogue workbook of [1] is not redistributed. To rebuild the "related (catalogue)" sheet, get it from its authors and run
`python 1_knowledge_base/00_catalogue_links.py <path to SSIpatternsCatalog23.xlsx>`.

## References

1. Čučko Š. et al., catalogue of SSI patterns, 2023.
2. Guth J., Leymann F., Pattern-based rewrite and refinement of architectures using graph theory, 2020.
3. Kahn A. B., Topological sorting of large networks, CACM 5(11), 1962.
4. Cordella L. P. et al., A (sub)graph isomorphism algorithm for matching large graphs (VF2), IEEE TPAMI, 2004.
