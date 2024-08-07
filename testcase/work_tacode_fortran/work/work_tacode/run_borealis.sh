#!/bin/bash

parallel=true

PYTHON=python3.9
LD=../../../../src/borealis.py
LOG=log_borealis
MPIP=mpirun.openmpi
num_process=4

touch timestamp_start_$(date "+%Y%m%d-%H%M%S")
if $parallel ; then
  $MPIP -n $num_process $PYTHON $LD
else
  $PYTHON $LD
fi
touch timestamp_end_$(date "+%Y%m%d-%H%M%S")
