#!/usr/bin/env python3

import numpy as np
from orbital.orbital import orbital


class adapter_simple_function(orbital):

  def __init__(self):

    print("Constructing class: adapter_simple_function")

    return

  
  def initial_settings(self, config):

    # Control file 
    #self.config = config

    #if config['simple_function']['flag_eval']:
    #x = 2
    #function_user = eval(config['simple_function']['function_eval'])
    #print(function_user)


    # Function output
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


  @orbital.time_measurement_decorated
  def objective_function(self, parameter_opt):

    print('Iteration: ', self.iter)

    #x = parameter_opt[0,0]
    x = parameter_opt

    # Function
    result_opt = self.function(parameter_opt)

    print('x,y:',x.squeeze(),result_opt.squeeze())

    # カウンタの更新
    self.iter += 1

    return result_opt.squeeze()
