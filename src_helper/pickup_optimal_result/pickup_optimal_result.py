#!/usr/bin/env python3

# Script to copy the optimal solution

import numpy as np
import yaml as yaml
import os as os
import shutil as shutil


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


def make_directory(dir_path):
  if not os.path.exists(dir_path):
    os.mkdir(dir_path)
  return


def main():

  # Read parameters
  file_control = 'pickup_optimal_result.yml'
  config = read_config_yaml(file_control)

  #file_control_borealis = 'borealis.yml'
  #config_bor =  read_config_yaml(file_control_borealis)

  # Initial settings
  work_dir = config['work_dir']
  case_dir = config['case_dir']
  filename_result = config['filename_result']

  step_start = config['step_start']
  step_end   = config['step_end']
  step_digit = config['step_digit']


  # Extracting reading files
  if config['flag_filereading_extracted']:
    data_extract = np.genfromtxt( config['filename_extract_list'], 
                                  dtype=int, 
                                  comments='#',
                                  delimiter=',', 
                                  skip_header=1 )
    index_local_to_global = data_extract[:,1]
    index_last = index_local_to_global[-1]
  else:
    index_last = step_end
  
  print('Index of optimal solution:', index_last)

  # Copy data
  n = index_last+1
  dirname_optimal = case_dir + str(n).zfill(step_digit)
  work_dir_copyfrom = work_dir + '/' + dirname_optimal
  work_dir_copyto   = config['copy_dir'] + '/' + dirname_optimal
  print('Copy optimal solution from',work_dir_copyfrom,'to',work_dir_copyto)
 
  make_directory(config['copy_dir'])
  shutil.copytree(work_dir_copyfrom, work_dir_copyto, dirs_exist_ok=True)


if __name__ == '__main__':

  main()