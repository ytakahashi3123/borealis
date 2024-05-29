#!/bin/bash

PYTHON_RUN=python3.9
TACODE_HOME=$HOME/research/calc/code/orbit_edl/tacode_ver2.1.0/src
LD=$TACODE_HOME/tacode.py
LOG=log_tacode

export OMP_NUM_THREADS=1

$PYTHON_RUN $LD > $LOG
#$PYTHON_RUN  $LD 2>&1 | tee $LOG
