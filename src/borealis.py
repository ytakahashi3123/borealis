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

  # Define parameter boundaries
  parameter_boundary = optimize.boundary_setting(config)

  # Run Bayesian optimization
  optimize.run_optimization(config, objective_function, parameter_boundary)

# 予測・グラフ化
#bopt.model.model #ベイズ最適化で使っているガウス過程のモデル(GPyのオブジェクト）
#bopt.model.model.predict #ガウス過程の回帰の関数
#bopt.X,myBopt.Y #サンプリングしたxとy

# ガウス過程回帰モデル
#  gprmodel = bopt.model.model

#予測（第一成分：mean、第二成分：std)
#  num_div_optfunction = config['Bayes_optimization']['num_div_optfunction'] 
#  x_lat = np.linspace(bound_lat_min, bound_lat_max, num_div_optfunction).reshape(-1, 1)
#  x_alt = np.linspace(bound_alt_min, bound_alt_max, num_div_optfunction).reshape(-1, 1)
#  x_func = np.meshgrid(x_lat,x_alt)
#  pred_mean, pred_std = gprmodel.predict(x_func)
#  pred_var = pred_std**2

#  mean = pred_mean[:, 0]
#  var  = pred_var[:, 0]
#  std  = pred_std[:, 0]

# Plot
#  bopt.plot_acquisition() 
#  bopt.plot_convergence()

  return


if __name__ == '__main__':

  main()

  exit()

