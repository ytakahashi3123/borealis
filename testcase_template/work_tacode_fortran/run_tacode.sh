#!/bin/bash

#source ~/.bashrc_intel
source /opt/intel/compilers_and_libraries/linux/bin/compilervars.sh intel64

DIR_BIN=/opt/tacode/tacode_ver1.12/bin
LD=${DIR_BIN}/tacode
LOG=log_tacode

$LD > $LOG
