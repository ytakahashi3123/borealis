#!/bin/bash

#source ~/.bashrc_intel
source /opt/intel/compilers_and_libraries/linux/bin/compilervars.sh intel64

TACODE_HOME=/opt/tacode/tacode_ver1.12/bin
LD=$TACODE_HOME/tacode
LOG=log_tacode

$LD > $LOG
