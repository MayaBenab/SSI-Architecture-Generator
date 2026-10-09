"""Optional: the seven requests of the paper's evaluation (S1 = the diploma case of the poster) -> out_scenarios/S1..S7.
usage: python 11_run_scenarios.py"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
import run_scenarios
run_scenarios.main()
