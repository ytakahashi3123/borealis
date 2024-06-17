#!/bin/bash

PYTHON_RUN=python3.8
EXCODE_HOME=$HOME/source/cage/cage-v1.1.0/src
LD=$EXCODE_HOME/cage.py
LOG=log_cage

export OMP_NUM_THREADS=1

$PYTHON_RUN $LD > $LOG
#$PYTHON_RUN  $LD 2>&1 | tee $LOG
