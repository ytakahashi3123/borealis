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
  file_control = 'pickup_optimal_result_shapeopt.yml'
  config = general.read_config_yaml(file_control)

  # Initial settings
  work_dir = config['work_dir']
  case_dir = config['case_dir']
  step_digit = config['step_digit']
  num_rank = config['num_rank']


  # Extracting reading files
  data_extract = np.genfromtxt( config['filename_extract_list'], 
                                dtype=int, 
                                comments='#',
                                delimiter=',', 
                                skip_header=1 )
  index_local_to_global = data_extract[:,1].astype(int)
  step = data_extract[:,0].astype(int)
  id_optimal_case = index_local_to_global[-1] - step[-1]*num_rank + 1

  print(f'Case rank including optimal solution {id_optimal_case}')

  # Copy data
  work_dir_copyfrom = work_dir + '/' + case_dir + str(id_optimal_case).zfill(step_digit)
  work_dir_copyto  = config['copy_dir'] + '/' + case_dir + str(id_optimal_case).zfill(step_digit)
  print(f'Copy optimal solution from {work_dir_copyfrom} to {work_dir_copyto}')
 
  general.make_directory(config['copy_dir'])
  shutil.copytree(work_dir_copyfrom, work_dir_copyto, dirs_exist_ok=True)


if __name__ == '__main__':

  main()