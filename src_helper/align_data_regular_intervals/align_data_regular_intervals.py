#!/usr/bin/env python3

import numpy as np
import yaml as yaml

def read_config_yaml(file_control):
  print("Reading control file...:", file_control)
  with open(file_control) as file:
    config = yaml.safe_load(file)
  return config

def main():

  # Read parameters
  file_control = 'align_data_regular_intervals.yml'
  config = read_config_yaml(file_control)

  x_min = config['x_min']
  x_max = config['x_max']
  num_div = config['num_div']

  x = np.linspace(x_min, x_max, num_div)
  print(' Min.:', x_min, '\n','Max.:',x_max, '\n', 'Num_div:',num_div)
  print(' x:', [ x[i] for i in range(0,num_div) ] )

  return


if __name__ == '__main__':

  main()