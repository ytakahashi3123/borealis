#!/bin/bash

PYTHON=python3.9
LD=../../src/borealis.py
LOG=log_borealis

parallel=true

MPIP=mpirun
num_process=4

if $parallel ; then
  $MPIP -n $num_process $PYTHON $LD
else
  $PYTHON $LD
fi
  
