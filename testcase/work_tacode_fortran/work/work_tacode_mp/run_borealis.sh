#!/bin/bash

#source $HOME/.bashrc_intel 
source $HOME/venvs/myenv/bin/activate
source /opt/intel/oneapi/setvars.sh

parallel_mpi=false

PYTHON=python
#HOME_BORE=/opt/Borealis/borealis-v1.5.0
HOME_BORE=$HOME/source/borealis/borealis-v1.5.0
LD=$HOME_BORE/src/borealis.py
LOG=log_borealis

MPIP=mpirun.openmpi
num_process=8

touch timestamp_start_$(date "+%Y%m%d-%H%M%S")
if $parallel_mpi ; then
  $MPIP -n $num_process $PYTHON $LD > $LOG
else
  $PYTHON $LD > $LOG
fi
touch timestamp_end_$(date "+%Y%m%d-%H%M%S")
