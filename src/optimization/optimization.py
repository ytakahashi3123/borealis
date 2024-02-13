#!/usr/bin/env python3

import numpy as np
import GPyOpt as GPyOpt
from orbital.orbital import orbital


class optimization(orbital):

  def __init__(self):

    print("Constructing class: optimization")

    self.str_error = 'Error'

    return


  def boundary_setting(self, config):

    # Setting parameter's boundaries

    boundary = config['Bayes_optimization']['boundary']
    bounds = []
    for n in range(0, len(boundary) ):
      boundary_name = boundary[n]['name']
      parameter_component = boundary[n]['component']
      for m in range(0,  len(parameter_component)):
        bound_type = parameter_component[m]['type']
        bound_min  = parameter_component[m]['bound_min']
        bound_max  = parameter_component[m]['bound_max']
        bounds.append( {'name': bound_type, 'type': 'continuous', 'domain': (bound_min, bound_max) } )
        print( 'Boundary in',bound_type,'component of',boundary_name,'(min--max):', bound_min,'--',bound_max)

    return bounds


  def bayesian_optimization(self, config, objective_function, parameter_boundary):

    # X , Y : 初期データ
    # initial_design_numdata : 設定する初期データの数。上記 X , Yを指定した場合は設定不要。 
    # normalize_Y : 目的関数(ガウス過程)を標準化する場合はTrue。(今回は予測を真値と比較しやすくするためFalse)
    bopt = GPyOpt.methods.BayesianOptimization(f=objective_function,
                                              domain=parameter_boundary,
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

    # ベイズ最適化
    #tolerance = 1e-8 
    bopt.run_optimization(max_iter=config['Bayes_optimization']['num_optiter'] )

    boundary = config['Bayes_optimization']['boundary']
    solution_dict = {}
    count = 0
    for n in range(0, len(boundary) ):
      parameter_component = boundary[n]['component']
      for m in range(0, len(parameter_component)):
        bound_type = parameter_component[m]['type']
        solution_dict[bound_type] = bopt.X[:,count]
        count = count + 1
    solution_dict[self.str_error] = bopt.Y[:,0]

    # Optimized solutions
    value_boptimized = bopt.x_opt
    error_boptimized = bopt.fx_opt
    _, index_boptimized = super().closest_value_index(solution_dict[self.str_error], error_boptimized)
    epoch_boptimized = index_boptimized + 1
    
    print("Optimized solutions:")
    print("--Solutions :" , value_boptimized)
    print("--Error     :" , error_boptimized)
    print("--Epoch     :" , epoch_boptimized)

    return solution_dict


  def write_optimization_data(self, config, solution_dict):

    boundary = config['Bayes_optimization']['boundary']
    solution_name_list = []
    for n in range(0, len(boundary) ):
      parameter_component = boundary[n]['component']
      for m in range(0, len(parameter_component)):
        solution_name_list.append( parameter_component[m]['type'] )
    solution_name_list.append(self.str_error)

    # Output results
    result_dir = config['Bayes_optimization']['result_dir']
    super().make_directory_rm(result_dir)
    filename_tmp      = result_dir+'/'+config['Bayes_optimization']['filename_output']
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


  def run_optimization(self, config, objective_function, parameter_boundary):

    # Bayesian optimization
    solution_dict = self.bayesian_optimization(config, objective_function, parameter_boundary)

    # Write data
    self.write_optimization_data(config, solution_dict)

    return