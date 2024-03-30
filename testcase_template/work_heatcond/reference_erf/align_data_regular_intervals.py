#!/usr/bin/env python3

import numpy as np
import yaml as yaml
from scipy import special

def read_config_yaml(file_control):
  print("Reading control file...:", file_control)
  with open(file_control) as file:
    config = yaml.safe_load(file)
  return config


def error_function(x):
  from scipy import special
  return special.erf(x)


def main():

  # Read parameters
  file_control = 'align_data_regular_intervals.yml'
  config = read_config_yaml(file_control)

  x_min = config['x_min']
  x_max = config['x_max']
  num_div = config['num_div']
  bound_min = config['bound_min']
  bound_max = config['bound_max']

  # X
  x = np.linspace(x_min, x_max, num_div)
  print(' Min.:', x_min, '\n','Max.:',x_max, '\n', 'Num_div:',num_div)
  print(' x:', [ x[i] for i in range(0,num_div) ] )

  # Dummy
  dummy_value=10.0
  print(' dummy:', [ dummy_value for i in range(0,num_div) ] )

  # Function
  factor = 800.0
  offset_x = x_max
  x_bar = ( (2*x-offset_x)/(x_max-x_min) )*np.pi
  erf = factor*(error_function(x_bar)+1.0)
  print(' y:', [ round(erf[i],5) for i in range(0,num_div) ] )
  
  # For control file
  for n in range(0,num_div):
    print("- type: t"+str(round(x[n])).zfill(6)+'s')
    print("  bound_min: "+str(bound_min))
    print("  bound_max: "+str(bound_max))
    

  return


if __name__ == '__main__':

  main()