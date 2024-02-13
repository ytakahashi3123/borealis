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


if __name__ == '__main__':

  # Class orbital
  orbital = orbital()

  #設定ファイルの読み込み
  file_control_default = orbital.file_control_default
  arg          = orbital.argument(file_control_default)
  file_control = arg.file
  config       = orbital.read_config_yaml(file_control)

  # Class adapter_tacode
  adapter_tacode = adapter_tacode()

  # Initialize for trajectory analysis
  adapter_tacode.initial_settings(config)

  # Reference data for objective function
  adapter_tacode.reference_data_setting(config)

  # Define parameter boundaries
  parameter_boundary = adapter_tacode.boundary_setting(config)

  # Class optimization
  optimization = optimization()

  # Run Bayesian optimization
  optimization.run_optimization(config, adapter_tacode.objective_function, parameter_boundary)

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

# Output resu;ts
#  epoch             = np.linspace(1,len(error_bopt),len(error_bopt)).reshape(-1, 1)
#  filename_tmp      = output_dir+'/'+config['Bayes_optimization']['filename_output']
#  header_tmp        = config['Bayes_optimization']['header_output']
#  print_message_tmp = '--Writing output file... '
#  delimiter_tmp     = '\t'
#  comments_tmp      = ''
#  output_tmp        = np.c_[ velocity_lon_bopt,
#                             velocity_lat_bopt,
#                             velocity_alt_bopt,
#                             error_bopt,
#                             epoch
#                            ]
#  orbital.write_tecplotdata( filename_tmp, print_message_tmp, header_tmp, delimiter_tmp, comments_tmp, output_tmp )
