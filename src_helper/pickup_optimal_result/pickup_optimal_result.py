#!/usr/bin/env python3

# Script to copy the optimal solution

import numpy as np
import sys
import os
import shutil as shutil

# Add ath of parent directory to Python path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
  sys.path.insert(0, parent_dir)  
from general import general


def main():

  # Read parameters
  file_control = 'pickup_optimal_result.yml'
  config = general.read_config_yaml(file_control)

  #file_control_borealis = 'borealis.yml'
  #config_bor =  general.read_config_yaml(file_control_borealis)

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
 
  general.make_directory(config['copy_dir'])
  shutil.copytree(work_dir_copyfrom, work_dir_copyto, dirs_exist_ok=True)


if __name__ == '__main__':

  main()