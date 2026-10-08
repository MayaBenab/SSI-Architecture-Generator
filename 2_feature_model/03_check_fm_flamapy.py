"""Offline analysis of the generated FM_SSI.uvl with flamapy (Benavides et al.): satisfiable, dead, false-optional, core.
Runs from any current directory. Requires: pip install flamapy flamapy-fm flamapy-z3
usage: python 03_check_fm_flamapy.py"""
from flamapy.metamodels.fm_metamodel.transformations import UVLReader
from flamapy.metamodels.z3_metamodel.transformations import FmToZ3

from flamapy.metamodels.z3_metamodel.operations.z3_satisfiable import Z3Satisfiable
from flamapy.metamodels.z3_metamodel.operations.z3_dead_features import Z3DeadFeatures
from flamapy.metamodels.z3_metamodel.operations.z3_false_optional_features import Z3FalseOptionalFeatures
from flamapy.metamodels.z3_metamodel.operations.z3_core_features import Z3CoreFeatures


print("== FM_SSI : analyse Flamapy + Z3 ==")

# 1. Lire le même modèle que celui utilisé dans FlamapyIDE
import os
HERE = os.path.dirname(os.path.abspath(__file__))
fm = UVLReader(os.path.join(HERE, "FM_SSI.uvl")).transform()

print("features :", len(fm.get_features()))

# 2. Transformer le FM en modèle Z3
z3fm = FmToZ3(fm).transform()

# 3. Vérifier si le modèle est satisfiable
satisfiable = Z3Satisfiable().execute(z3fm).get_result()
print("satisfiable :", satisfiable)

# 4. Chercher les features mortes
dead_features = Z3DeadFeatures().execute(z3fm).get_result()
print("dead features :", dead_features)

# 5. Chercher les false-optional
false_optional = Z3FalseOptionalFeatures().execute(z3fm).get_result()
print("false optional features :", false_optional)

# 6. Chercher les features core
core_features = Z3CoreFeatures().execute(z3fm).get_result()
print("core features :", core_features)