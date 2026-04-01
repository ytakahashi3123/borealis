#!/bin/bash

# Python
PYTHON=python3
# NRLMSISE
NRLMSISE_HOME=$HOME/source/tacode/nrlmsise/NRLMSISE-00/tacode_work
# Tacode
TACODE_HOME=$HOME/source/tacode/tacode-v1.2.1/bin

LD_MSIS=$NRLMSISE_HOME/NRLMSISE-00_readctl_2fequal_global.exe
LOG_MSIS=log_msis
$LD_MSIS > $LOG_MSIS

LD=$TACODE_HOME/tacode
LOG=log_tacode
$LD > $LOG

file_path="./restart.dat"

if [ -f "$file_path" ]; then
  rm "$file_path"
fi
