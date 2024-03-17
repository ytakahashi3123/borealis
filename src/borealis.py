#!/usr/bin/env python3

# Borealis: Bayesian optimization for finding a realizable solution for a discretized equation
# Version 1.00
# Date: 2024/02/29

# Author: Yusuke Takahashi, Hokkaido University
# Contact: ytakahashi@eng.hokudai.ac.jp

code_name = "Borealis"
version = "1.00"

import numpy as np
from orbital.orbital import orbital

def main():

  # Class orbital
  orbit = orbital()

  # Read control file
  file_control_default = orbit.file_control_default
  arg          = orbit.argument(file_control_default)
  file_control = arg.file
  config       = orbit.read_config_yaml(file_control)

  # Select adapter
  if config['adapter']['kind_adapter'] == 'tacode':
    from adapter_tacode.adapter_tacode import adapter_tacode
    adapter = adapter_tacode()
  elif config['adapter']['kind_adapter'] == 'simple_function':
    from adapter_template.adapter_simple_function import adapter_simple_function
    adapter = adapter_simple_function()
  elif config['adapter']['kind_adapter'] == 'example_externalcode':
    from adapter_template.adapter_example_externalcode import adapter_example_externalcode
    adapter = adapter_example_externalcode()
  elif config['adapter']['kind_adapter'] == 'heatcond':
    from adapter_heatcond.adapter_heatcond import adapter_heatcond
    adapter = adapter_heatcond()
  elif config['adapter']['kind_adapter'] == 'user':
    from adapter_user.adapter_user import adapter_user
    adapter = adapter_user()
  else:
    print('Error, invalid adapter is selected. Check adapter.kind_adapter in',file_control,':', config['adapter']['kind_adapter'])
    print('Program stopped.')
    exit()

  # Initialize for trajectory analysis
  adapter.initial_settings(config)

  # Reference data for objective function
  adapter.reference_data_setting(config)

  # Objective function
  objective_function = adapter.objective_function

  # Class optimization
  if config['optimizer']['kind_optimizer'] == 'Bayesian_optimization':
    from Bayesian_optimization.Bayesian_optimization import Bayesian_optimization
    optimizer = Bayesian_optimization()
  elif config['optimizer']['kind_optimizer'] == 'PSO':
    from optimizer_pso.optimizer_pso import optimizer_pso
    optimizer = optimizer_pso()
  elif config['optimizer']['kind_optimizer'] == 'ABC':
    from optimizer_abc.optimizer_abc import optimizer_abc
    optimizer = optimizer_abc()
  else:
    print('Error, invalid optimizer is selected. Check optimizer.kind_optimizer in',file_control,':', config['optimizer']['kind_optimizer'])
    print('Program stopped.')
    exit()

  # Initial setting
  optimizer.initial_setting(config)

  # Define parameter boundaries
  parameter_boundary = optimizer.boundary_setting(config)

  # Run Bayesian optimization
  optimizer.drive_optimization(config, objective_function, parameter_boundary)

  return


if __name__ == '__main__':

  print('Program name:',code_name, 'version:', version)
  print('Initialize optimization process')

  main()

  print('Finalize optimization process')
  exit()

