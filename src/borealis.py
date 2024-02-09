#!/usr/bin/env python3

# Borealis: Bayesian optimization for finding a realizable solution for a discretized equation
# Version 1.00
# Date: 2024/02/29

# Author: Yusuke Takahashi, Hokkaido University
# Contact: ytakahashi@eng.hokudai.ac.jp

import numpy as np
import GPyOpt as GPyOpt
from orbital.orbital import orbital
from adapter_tacode.adapter_tacode import adapter_tacode


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

  # Define boundaries
  bounds = adapter_tacode.boundary_setting(config)

  # X , Y : 初期データ
  # initial_design_numdata : 設定する初期データの数。上記 X , Yを指定した場合は設定不要。 
  # normalize_Y : 目的関数(ガウス過程)を標準化する場合はTrue。(今回は予測を真値と比較しやすくするためFalse)
  bopt = GPyOpt.methods.BayesianOptimization(f=adapter_tacode.f_tacode,
                                             domain=bounds,
                                             #X=init_X,
                                             #Y=init_Y,
                                             model_type='GP',
                                             #model_type='GP_MCMC',
                                             normalize_Y=False,
                                             maximize=False,
                                             verbosity=True,
                                             #initial_design_numdata=50,
                                             acquisition_type='EI'
                                             #acquisition_type='MPI'
                                             )

  # ベイズ最適化_モデル初期化
  num_optiter = config['Bayes_optimization']['num_optiter'] 

  # ベイズ最適化
  #tolerance = 1e-8 
  bopt.run_optimization(max_iter=num_optiter)

  # ベイズ最適化_学習結果・過程
  # 最適化の軌跡
  #  print("X.shape" , ":" , bopt.X.shape)
  #  print("Y.shape" , ":" , bopt.Y.shape)
  #  print("-" * 50)
  #  print("X[:]" , ":")
  #  print(bopt.X[:])
  #  print("-" * 50)
  #  print("Y[:]" , ":")
  #  print(bopt.Y[:])
  #  print("-" * 50)

  velocity_lon_bopt = bopt.X[:,0]
  velocity_lat_bopt = bopt.X[:,1]
  velocity_alt_bopt = bopt.X[:,2]
  error_bopt       = bopt.Y[:]

  # 得られた最適解
  veloc_boptimized = bopt.x_opt
  error_boptimized = bopt.fx_opt
  index_boptimized = orbital.getNearestIndex(error_bopt, error_boptimized)
  epoch_boptimized = index_boptimized + 1
  print("Optimized parameters:")
  print("--Velocities" , ":" , veloc_boptimized)
  print("--Error:    " , ":" , error_boptimized)
  print("--Epoch:    " , ":" , epoch_boptimized)

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
  epoch             = np.linspace(1,len(error_bopt),len(error_bopt)).reshape(-1, 1)
  filename_tmp      = output_dir+'/'+config['Bayes_optimization']['filename_output']
  header_tmp        = config['Bayes_optimization']['header_output']
  print_message_tmp = '--Writing output file... '
  delimiter_tmp     = '\t'
  comments_tmp      = ''
  output_tmp        = np.c_[ velocity_lon_bopt,
                             velocity_lat_bopt,
                             velocity_alt_bopt,
                             error_bopt,
                             epoch
                            ]
  orbital.write_tecplotdata( filename_tmp, print_message_tmp, header_tmp, delimiter_tmp, comments_tmp, output_tmp )

