#!/bin/bash

PYTHON=python3.9
LD_DIR=../../../../src_helper
LOG=log_postprocess

# Delete files
LD_DEL=$LD_DIR/delete_nonoptimal_solution/delete_nonoptimal_solution.py
$PYTHON $LD_DEL > $LOG

# Make image optimal solution
LD_IMAGE=$LD_DIR/pickup_optimal_result/pickup_optimal_result.py
$PYTHON $LD_IMAGE >> $LOG
