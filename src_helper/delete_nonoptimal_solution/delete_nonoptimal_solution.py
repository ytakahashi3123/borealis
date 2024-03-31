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
  file_control = 'delete_nonoptimal_solution.yml'
  config = read_config_yaml(file_control)

  #file_control_borealis = 'borealis.yml'
  #config_bor =  read_config_yaml(file_control_borealis)

  # Initial settings
  work_dir = config['work_dir']
  case_dir = config['case_dir']
  step_digit = config['step_digit']

  # Optimal solution files
  data_extract = np.genfromtxt( config['filename_extract_list'], 
                                dtype=int, 
                                comments='#',
                                delimiter=',', 
                                skip_header=1 )
  index_local_to_global = data_extract[:,1]
  num_optimal = len(index_local_to_global)

  # Data deleting
  n_count = 0
  n = 0
  is_dir = True
  while is_dir:
    # Directory name
    work_dir_case = work_dir + '/' + case_dir + str(n+1).zfill(step_digit)
    # If directory can not be found, beak the loop.
    if not os.path.isdir(work_dir_case) :
      break

    if n+1 != index_local_to_global[n_count]+1 :
      # Non-optimal solution at each step
      print('--Deleting directory...:',work_dir_case)
      shutil.rmtree(work_dir_case)
    else:
      # Optimal solution 
      n_count += 1
      print('--Remaining optimal solution...:',work_dir_case)
    print(n,n_count, num_optimal)
    
    if n_count >= num_optimal:
      n_count = num_optimal-1

    n += 1

  return


if __name__ == '__main__':

  main()