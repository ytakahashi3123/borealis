#!/usr/bin/env python3

import numpy as np
from orbital.orbital import orbital


class adapter_simple_function(orbital):

  def __init__(self,mpi_instance):

    print("Constructing class: adapter_simple_function")

    self.mpi_instance = mpi_instance

    return

  
  def initial_settings(self, config):

    # Control file 
    #self.config = config

    #if config['simple_function']['flag_eval']:
    #x = 2
    #function_user = eval(config['simple_function']['function_eval'])
    #print(function_user)

    # Function output
    if self.mpi_instance.rank == 0:
      if( config['simple_function']['flag_output'] ):
        result_dir   = config['simple_function']['result_dir']
        filename_tmp = result_dir + '/' + config['simple_function']['filename_output']
        super().make_directory_rm(result_dir)
        x_div = config['simple_function']['function_discrete']
        x_min = config['simple_function']['function_bound_min']
        x_max = config['simple_function']['function_bound_max']
        x_tmp = np.linspace(x_min, x_max, x_div)
        y_tmp = self.function(x_tmp)
        header_tmp    = 'Variables=x, y'
        delimiter_tmp = '\t'
        comments_tmp  = ''
        output_tmp    = np.c_[x_tmp, y_tmp]
        np.savetxt(filename_tmp, output_tmp, header=header_tmp, delimiter=delimiter_tmp, comments=comments_tmp )

    # Counter
    self.iter = 1
     
    return


  def reference_data_setting(self, config):

    return


  def function(self, x):
    return 2*np.sin(x) + 4*np.cos(2 * x) + 3*np.cos(2/5 * x)

  #def objective_function(self, x):
  # Ackley
  #  y1 = 22.71828
  #  y2 = -20 * np.exp(-0.2 * np.sqrt(1.0 / len(x) * np.sum(x ** 2, axis=0)))
  #  y4 = -np.exp(1.0 / len(x) * np.sum(np.cos(2.0 * np.pi * x), axis=0))
  #  return y1 + y2 + y4

  #def fitness_function(self, x):
  #  # Sphere_function
  #  return np.sum(x**2)


  @orbital.time_measurement_decorated
  def objective_function(self, parameter_opt, *id_serial):

    if id_serial:
      self.iter = id_serial[0]

    print('Iteration: ', self.iter)

    #x = parameter_opt[0,0]
    x = parameter_opt

    # Function
    result_opt = self.function(parameter_opt)

    print('x,y:',x.squeeze(),result_opt.squeeze())

    # カウンタの更新
    if not id_serial:
      self.iter += 1

    return result_opt.squeeze()
