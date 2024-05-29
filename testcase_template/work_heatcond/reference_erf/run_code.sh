#!/bin/bash

EXCODE_HOME=$HOME/research/calc/code/heatconduction/heatcond_membraneaeroshell/heatcond_membraneaeroshell_ver1.3.0/bin
LD=$EXCODE_HOME/heatcond
LOG=log_heatcond

export OMP_NUM_THREADS=1

$LD > $LOG

