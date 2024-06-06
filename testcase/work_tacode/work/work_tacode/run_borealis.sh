#!/bin/bash

parallel=false

PYTHON=python3.9
LD=../../../../src/borealis.py
LOG=log_borealis
MPIP=mpirun
num_process=4

touch timestamp_start_$(date "+%Y%m%d-%H%M%S")
if $parallel ; then
  $MPIP -n $num_process $PYTHON $LD > $LOG
else
  $PYTHON $LD > $LOG
fi
touch timestamp_end_$(date "+%Y%m%d-%H%M%S")
