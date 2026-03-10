#!/usr/bin/env python3

import numpy as np
import os as os
import shutil as shutil
import yaml as yaml


def read_config_yaml(file_control):
  print("Reading control file...:", file_control)
  try:
    with open(file_control) as file:
      config = yaml.safe_load(file)
  except Exception as e:
    import sys as sys
    print('Exception occurred while loading YAML...', file=sys.stderr)
    print(e, file=sys.stderr)
    sys.exit(1)
  return config


def main():

  # Read parameters
  file_control = 'delete_nonoptimal_solution_shapeopt.yml'
  config = read_config_yaml(file_control)

  #file_control_borealis = 'borealis.yml'
  #config_bor =  read_config_yaml(file_control_borealis)

  # Initial settings
  work_dir = config['work_dir']
  case_dir = config['case_dir']
  step_digit = config['step_digit']
  num_rank = config['num_rank']

  # Optimal solution files
  data_extract = np.genfromtxt( config['filename_extract_list'], 
                                dtype=int, 
                                comments='#',
                                delimiter=',', 
                                skip_header=1 )
  index_local_to_global = data_extract[:,1].astype(int)
  step = data_extract[:,0].astype(int)
  id_optimal_case = index_local_to_global[-1] - step[-1]*num_rank + 1

  print(f'Case rank including optimal solution {id_optimal_case}')

  # Data deleting
  for n in range(0,num_rank):
    work_dir_case = work_dir + '/' + case_dir + str(n+1).zfill(step_digit)
    if n+1 != id_optimal_case :
      print(f'--Deleting directory...{work_dir_case} of rank {n+1} in all ranks {num_rank}')
      shutil.rmtree(work_dir_case)

  return


if __name__ == '__main__':

  main()