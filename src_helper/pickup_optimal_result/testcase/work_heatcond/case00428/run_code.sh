#!/bin/bash

EXCODE_HOME=/opt/heatconduction/heatcond_membraneaeroshell/heatcond_membraneaeroshell_ver1.30/bin
LD=$EXCODE_HOME/heatcond
LOG=log_heatcond

export OMP_NUM_THREADS=1

$LD | tee $LOG
