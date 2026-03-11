#!/bin/bash

source $HOME/venvs/myenv/bin/activate
source ${HOME}/.dir_opt_bashrc/.bashrc_precice-v320
source ${HOME}/.dir_opt_bashrc/.bashrc_precice-v320_su2
source ${HOME}/.dir_opt_bashrc/.bashrc_precice-v320_borealis

PYTHON=python3
filename_jobrequests="job_requests"

# Optimizer
# Initial settings
LD_BORE=$HOME_BORE/src/borealis.py
LOG_BORE=log_borealis
MPIP_BORE=mpirun.openmpi
num_process_bore=6

# Delete old files
if [ -f "$filename_jobrequests" ]; then
  rm "$filename_jobrequests"
  if [ $? -eq 0 ]; then
    echo "$filename_jobrequests has been deleted."
  else
    echo "Failed to delete $filename_jobrequests." >&2
    exit 1
  fi
else
  echo "$filename_jobrequests does not exist."
fi

# Run Borealis
parallel_bore=true
if $parallel_bore ; then
  $MPIP_BORE -n $num_process_bore $PYTHON $LD_BORE > $LOG_BORE &
else
  $PYTHON $LD_BORE > $LOG_BORE &
fi


# Aerodynamic simulations for optimization

# Initial settings
fluid=false
# Common
DIR_FLUID=./fluid
DIR_OPT=./optimization

# Parallel
MPIP=mpirun
ncpu_f=2
ncpu_o=1

# Fluid
if ! $fluid ; then # Coupled
  LD_F=${HOME_BORE}/src_helper/src_tmp/SU2_preCICE_FSI.py
  LOG_F=log_su2
  INP_F=sphere.cfg
else
  LD_F=${SU2_HOME}/bin/SU2_CFD
  LOG_F=log_su2.fluid
  INP_F=sphere.fluid.cfg
fi

# Optimization
LD_O=${HOME_BORE}/src/adapter_shapeoptimizer/shapeoptimizer_preCICE.py
LOG_O=log_shapeoptimization

# ファイルが出現するまで待つ
echo "Waiting for $filename_jobrequests to appear..."
while [ ! -f "$filename_jobrequests" ]; do
  sleep 1
done
echo "$filename_jobrequests found."

# 中身を読み込んでディレクトリ作成
#   最初の行 "Directories for subprocesses:" はスキップ
count=0
tail -n +2 "$filename_jobrequests" | while read -r dir; do
    # 空行やスペースのみの行をスキップ
    [ -z "$dir" ] && continue
    #mkdir -p "$(basename "$dir")"
    #echo "Created directory: $(basename "$dir")"
    #mkdir -p "$dir"
    #echo "Created directory: $dir"

    # 作成したディレクトリに移動してコマンド実行
    (
        cd "$dir" || { 
            echo "ディレクトリ移動に失敗しました: $dir" >&2
            exit 1
        }

        echo "Changed directory: $(pwd)"
        current_dir=$(pwd)
        echo $count

        # Start coupling routines
        #touch timestamp_start_$(date "+%Y%m%d-%H%M%S")

        # --Fluid
        # Make directory
        cd ${DIR_FLUID}
        DIR_OUTPUT=("output_restart" "output_flow" "output_surface_flow")
        for (( i = 0; i < ${#DIR_OUTPUT[*]}; i++ ))
        {
          if [[ ! -e $DIR_OUTPUT[i] ]]; then
            mkdir ${DIR_OUTPUT[i]}
          fi
        }

        # 割り当てるコアID計算
        core_start=$(( ncpu_f * count ))
        core_end=$(( ncpu_f * (count+1) - 1 ))
        cpu_set=$(seq -s, $core_start $core_end)
        echo "Iteration $i: CPU set = $cpu_set"

        if ! $fluid ; then # Coupled
          if $parallel ; then
            #$MPIP -np $ncpu_f -npernode $ncpu_f --report-bindings --bind-to core --map-by core:PE=1 ${PYTHON} ${LD_F} -f ${INP_F} --parallel > $LOG_F 2>&1 &
            $MPIP -np $ncpu_f \
                  --bind-to core --cpu-set "$cpu_set" \
                  --report-bindings \
                  ${PYTHON} ${LD_F} -f ${INP_F} --parallel > $LOG_F 2>&1 &
          else
            ${LD_F} -f ${INP_F} -p SU2_CFD --parallel > $LOG_F 2>&1 &
          fi
        else # Uncoupled
          if $parallel ; then
            $MPIP -np $ncpu_f ${LD_F} ${INP_F} > $LOG_F 2>&1 &
          else
            ${LD_F} ${INP_F} > $LOG_F 2>&1 &
          fi
        fi
        PIDParticipant1=$!
        cd ${current_dir}

        # --Optimization
        cd ${DIR_OPT}
        if ! $fluid ; then
          if $parallel ; then
            export OMP_NUM_THREADS=$ncpu_o
          else
            export OMP_NUM_THREADS=1
          fi
          $PYTHON $LD_O > $LOG_O 2>&1 &
          PIDParticipant2=$!
        fi
        cd ${current_dir}


        # Wait...
        if $fluid ; then
          echo "Waiting for the participants to exit..., PIDs: ${PIDParticipant1}"
        else
          echo "Waiting for the participants to exit..., PIDs: ${PIDParticipant1} ${PIDParticipant2}"
        fi
        echo "(you may run 'tail -f ${Participant1}.log' in another terminal to check the progress)"

    )
    count=$((count+1))
done

wait &

echo "All directories created."

