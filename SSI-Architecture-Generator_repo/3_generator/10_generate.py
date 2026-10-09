"""Steps 3-5 of the poster for one request: select and order (Z3 on FM_SSI.uvl), refine (rules.json), deploy (deployment.json), trace.
usage: python 10_generate.py FR13 FR17 --nfr NFR04 NFR07 --out out_diploma [--draw] [--indy] [--forbid P07]
without arguments (Run button): the diploma case, written to 3_generator/out_diploma with the figures"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
import generate
generate.main()
