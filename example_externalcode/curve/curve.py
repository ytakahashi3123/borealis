#!/usr/bin/env python3

# Script to make a curve
# Version 1.00
# Date: 2024/02/18

# Author: Yusuke Takahashi, Hokkaido University
# Contact: ytakahashi@eng.hokudai.ac.jp

import numpy as np
import yaml as yaml


def read_config_yaml(file_control):

  with open(file_control) as file:
    config = yaml.safe_load(file)

  return config


def initialization(config):

  # Difinition range
  x_div = config['curve']['function_discrete']
  x_min = config['curve']['function_bound_min']
  x_max = config['curve']['function_bound_max']
  x = np.linspace(x_min, x_max, x_div)

  # Coefficients setting
  a = config['curve']['coefficient']['a']
  b = config['curve']['coefficient']['b']
  c = config['curve']['coefficient']['c']

  return a,b,c,x


def function(a,b,c,x):

  val = a*np.sin(x) + b*np.cos(2*x) + c*np.sin(7/8*x)

  return val


def output(config, x, y):

  a = config['curve']['coefficient']['a']
  b = config['curve']['coefficient']['b']
  c = config['curve']['coefficient']['c']

  filename  = config['curve']['filename_output']
  header = '# Comment: coefficinets: a='+str(a)+', b='+str(b)+', c='+str(c)+'\n'+'Variables = x, y'
  delimiter = '\t'
  comments  = ''
  output    = np.c_[x, y]
  np.savetxt(filename, output, header=header, delimiter=delimiter, comments=comments )

  return


def main():

  # Read control file
  file_control = 'curve.yml'
  config = read_config_yaml(file_control)

  # Initial setting
  a,b,c,x = initialization(config)

  # Calling function
  y = function(a,b,c,x)

  # Output data
  output(config, x, y)

  return


if __name__ == '__main__':

  print('Initialize code to make a curve')

  main()

  print('Finalize code to make a curve')

  exit()

