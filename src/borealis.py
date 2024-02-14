#!/usr/bin/env python3

# Borealis: Bayesian optimization for finding a realizable solution for a discretized equation
# Version 1.00
# Date: 2024/02/29

# Author: Yusuke Takahashi, Hokkaido University
# Contact: ytakahashi@eng.hokudai.ac.jp

import numpy as np
from orbital.orbital import orbital
from adapter_tacode.adapter_tacode import adapter_tacode
from optimization.optimization import optimization


def main():

  # Class orbital
  orbit = orbital()

  # Read control file
  file_control_default = orbit.file_control_default
  arg          = orbit.argument(file_control_default)
  file_control = arg.file
  config       = orbit.read_config_yaml(file_control)

  # Class adapter_tacode
  adapter = adapter_tacode()

  # Initialize for trajectory analysis
  adapter.initial_settings(config)

  # Reference data for objective function
  adapter.reference_data_setting(config)

  # Objective function
  objective_function = adapter.objective_function

  # Class optimization
  optimize = optimization()

  # Initial setting
  optimize.initial_setting(config)

  # Define parameter boundaries
  parameter_boundary = optimize.boundary_setting(config)

  # Run Bayesian optimization
  optimize.run_optimization(config, objective_function, parameter_boundary)

  return


if __name__ == '__main__':

  main()

  exit()

