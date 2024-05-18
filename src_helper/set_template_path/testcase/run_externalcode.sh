#!/bin/bash

PYTHON_RUN=python3.9
EXCODE_HOME=$HOME/research/repository/borealis/borealis_ver1.1.0/example_externalcode/curve
LD=$EXCODE_HOME/curve.py
LOG=log_curve

export OMP_NUM_THREADS=1

$PYTHON_RUN $LD > $LOG
#$PYTHON_RUN  $LD 2>&1 | tee $LOG
