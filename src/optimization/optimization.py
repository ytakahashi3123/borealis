#!/usr/bin/env python3

import GPyOpt as GPyOpt
from orbital.orbital import orbital
#from adapter_tacode.adapter_tacode import adapter_tacode


class optimization(orbital):

  def __init__(self):

    print("Constructing class: optimization")

    return


  def bayesian_optimization(self, config, objective_function, bounds):

    # X , Y : 初期データ
    # initial_design_numdata : 設定する初期データの数。上記 X , Yを指定した場合は設定不要。 
    # normalize_Y : 目的関数(ガウス過程)を標準化する場合はTrue。(今回は予測を真値と比較しやすくするためFalse)
    bopt = GPyOpt.methods.BayesianOptimization(f=objective_function,
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
    error_bopt        = bopt.Y[:]

    var_opt = [velocity_lon_bopt, velocity_lat_bopt, velocity_alt_bopt, error_bopt ]

    # 得られた最適解
    veloc_boptimized = bopt.x_opt
    error_boptimized = bopt.fx_opt
    index_boptimized = orbital.getNearestIndex(error_bopt, error_boptimized)
    epoch_boptimized = index_boptimized + 1
    
    print("Optimized parameters:")
    print("--Velocities" , ":" , veloc_boptimized)
    print("--Error:    " , ":" , error_boptimized)
    print("--Epoch:    " , ":" , epoch_boptimized)

    return var_opt


  def run_optimization(self, objective_function, bounds):

    var_opt = self.bayesian_optimization(config, objective_function, bounds)

    return