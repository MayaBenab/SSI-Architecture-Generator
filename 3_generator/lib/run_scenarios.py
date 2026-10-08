"""The seven scenarios of the Experimentation section.  usage: python run_scenarios.py  -> out_scenarios/S1..S7"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); os.chdir(os.path.join(HERE, ".."))
from generate import run
S = [("S1", ["FR13","FR17"], ["NFR04","NFR07"], []), ("S2", ["FR13","FR17"], ["NFR09","NFR11"], []), ("S3", ["FR13","FR17"], ["NFR18"], []),
     ("S4", ["FR04","FR13","FR19","FR21","FR28","FR29"], ["NFR08","NFR13"], []), ("S5", ["FR06","FR08"], ["NFR02","NFR18"], []),
     ("S6", ["FR13","FR17","FR22","FR23"], ["NFR04","NFR10"], []), ("S7", ["FR13","FR17"], ["NFR04"], ["P07"])]
def main():
    for sid, fr, nfr, forbid in S:
        print("=" * 100); print(sid); run(fr, nfr, forbid, os.path.join("out_scenarios", sid))

if __name__ == "__main__":
    main()
