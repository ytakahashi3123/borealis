#!/usr/bin/env python3

import numpy as np
import GPyOpt as GPyOpt
import matplotlib.pyplot as plt
from orbital.orbital import orbital


class Bayesian_optimization(orbital):

  def __init__(self,mpi_instance):

    print("Constructing class: Bayesian_optimization")

    self.mpi_instance = mpi_instance

    self.str_error = 'Error'

    return


  def initial_setting(self, config):

    if self.mpi_instance.rank == 0:
      result_dir = config['Bayesian_optimization']['result_dir']
      super().make_directory_rm(result_dir)
    if self.mpi_instance.flag_mpi :
      self.mpi_instance.comm.Barrier()

    return


  def boundary_setting(self, config):

    # Setting parameter's boundaries

    boundary = config['parameter_optimized']['boundary']
    parameter_boundary = []
    for n in range(0, len(boundary) ):
      boundary_name = boundary[n]['name']
      parameter_component = boundary[n]['component']
      for m in range(0,  len(parameter_component)):
        bound_type = parameter_component[m]['type']
        bound_min  = parameter_component[m]['bound_min']
        bound_max  = parameter_component[m]['bound_max']
        parameter_boundary.append( {'name': bound_type, 'type': 'continuous', 'domain': (bound_min, bound_max) } )
        print( 'Boundary in',bound_type,'component of',boundary_name,'(min--max):', bound_min,'--',bound_max)

    return parameter_boundary


  def bayesian_optimization(self, config, objective_function, parameter_boundary):

    # Ref: https://github.com/SheffieldML/GPyOpt/blob/master/GPyOpt/methods/bayesian_optimization.py
    problem = GPyOpt.methods.BayesianOptimization(f = objective_function,
                                                  domain = parameter_boundary,
                                                  #X=init_X,
                                                  #Y=init_Y,
                                                  model_type                 = config['Bayesian_optimization']['model_type'],
                                                  normalize_Y                = config['Bayesian_optimization']['normalize_Y'],
                                                  maximize                   = config['Bayesian_optimization']['maximize'],
                                                  initial_design_numdata     = config['Bayesian_optimization']['initial_design_numdata'],
                                                  acquisition_type           = config['Bayesian_optimization']['acquisition_type'],
                                                  acquisition_weight         = config['Bayesian_optimization']['acquisition_weight'],
                                                  acquisition_optimizer_type = config['Bayesian_optimization']['acquisition_optimizer_type'],
                                                  verbosity                  = config['Bayesian_optimization']['verbosity']
                                                  )

    # ベイズ最適化
    #tolerance = 1e-8 
    problem.run_optimization(max_iter=config['Bayesian_optimization']['num_optiter'],verbosity=True)

    # Store optimized data
    boundary = config['parameter_optimized']['boundary']
    solution_dict = {}
    count = 0
    for n in range(0, len(boundary) ):
      parameter_component = boundary[n]['component']
      for m in range(0, len(parameter_component)):
        bound_type = parameter_component[m]['type']
        solution_dict[bound_type] = problem.X[:,count]
        count = count + 1
    solution_dict[self.str_error] = problem.Y[:,0]

    # Optimized solutions
    value_boptimized = problem.x_opt
    error_boptimized = problem.fx_opt
    _, index_boptimized = super().closest_value_index(solution_dict[self.str_error], error_boptimized)
    epoch_boptimized = index_boptimized + 1
    
    print("Optimized solutions:")
    print("--Solutions :" , value_boptimized)
    print("--Error     :" , error_boptimized)
    print("--Epoch     :" , epoch_boptimized)

    return problem, solution_dict


  def write_optimization_data(self, config, solution_dict):

    boundary = config['parameter_optimized']['boundary']
    solution_name_list = []
    for n in range(0, len(boundary) ):
      parameter_component = boundary[n]['component']
      for m in range(0, len(parameter_component)):
        solution_name_list.append( parameter_component[m]['type'] )
    solution_name_list.append(self.str_error)

    # Output results
    filename_tmp =  config['Bayesian_optimization']['result_dir'] + '/' + config['Bayesian_optimization']['filename_output']
    print('--Writing output file...:',filename_tmp)

    # Open file
    file_output = open( filename_tmp , 'w')
    
    # Header
    header_tmp = "Variables="
    for n in range(0,len(solution_name_list)):
      header_tmp = header_tmp + solution_name_list[n] + ','
    # Addition
    header_tmp = header_tmp + 'Epoch' + '\n'
    file_output.write( header_tmp )

    num_step = len( solution_dict[solution_name_list[0]] )
    epoch    = np.linspace(1,num_step,num_step)

    text_tmp = ''
    for n in range(0, num_step):
      for m in range(0, len(solution_name_list)):
        text_tmp = text_tmp  + str( solution_dict[solution_name_list[m]][n] ) + ', '
      text_tmp = text_tmp + str(epoch[n]) + '\n'

    file_output.write( text_tmp )
    file_output.close()

    return


  def plot_optimization_process(self, config, problem):

    # not supported

  # 予測・グラフ化
  #bopt.model.model #ベイズ最適化で使っているガウス過程のモデル(GPyのオブジェクト）
  #bopt.model.model.predict #ガウス過程の回帰の関数
  #bopt.X,myBopt.Y #サンプリングしたxとy

  # ガウス過程回帰モデル
  #  gprmodel = problem.model.model

  #予測（第一成分：mean、第二成分：std)
  #  num_div_optfunction = config['Bayesian_optimization']['num_div_optfunction'] 
  #  x_lat = np.linspace(bound_lat_min, bound_lat_max, num_div_optfunction).reshape(-1, 1)
  #  x_alt = np.linspace(bound_alt_min, bound_alt_max, num_div_optfunction).reshape(-1, 1)
  #  x_func = np.meshgrid(x_lat,x_alt)
  #  pred_mean, pred_std = gprmodel.predict(x_func)
  #  pred_var = pred_std**2

  #  mean = pred_mean[:, 0]
  #  var  = pred_var[:, 0]
  #  std  = pred_std[:, 0]

  # Plot
    if config['Bayesian_optimization']['flag_image_acquisition']:
      filename_tmp = config['Bayesian_optimization']['result_dir'] + '/' + config['Bayesian_optimization']['filename_image_acquisition']
      problem.plot_acquisition(filename=filename_tmp)

    if config['Bayesian_optimization']['flag_image_convergence']:
      filename_tmp = config['Bayesian_optimization']['result_dir'] + '/' + config['Bayesian_optimization']['filename_image_convergence']
      problem.plot_convergence(filename=filename_tmp)

    return


  def drive_optimization(self, config, objective_function, parameter_boundary):

    # Bayesian optimization
    problem, solution_dict = self.bayesian_optimization(config, objective_function, parameter_boundary)

    # Write data
    if self.mpi_instance.rank == 0:
      self.write_optimization_data(config, solution_dict)

    # Plot data
    if self.mpi_instance.rank == 0:
      self.plot_optimization_process(config, problem)

    return