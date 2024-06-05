#!/bin/bash

EXCODE_HOME=$HOME/research/calc/code/heatconduction/heatcond_membraneaeroshell/heatcond_membraneaeroshell-v1.3.0/bin
LD=$EXCODE_HOME/heatcond
LOG=log_heatcond

export OMP_NUM_THREADS=1

$LD | tee $LOG