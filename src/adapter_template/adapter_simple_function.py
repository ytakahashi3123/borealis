#!/usr/bin/env python3

import numpy as np
from orbital.orbital import orbital


class adapter_simple_function(orbital):

  def __init__(self):

    print("Constructing class: adapter_simple_function")

    return

  
  def initial_settings(self, config):

    # Control file 
    self.config = config

    # Counter
    self.iter = 1
     
    return


  def reference_data_setting(self, config):
    return


  @orbital.time_measurement_decorated
  def objective_function(self, x):

    print('Iteration: ', self.iter)

    # Function
    y = 2*np.sin(x) + 4*np.cos(2 * x) + 3*np.cos(2/5 * x)

    print('x,y:',x,y)

    # カウンタの更新
    self.iter += 1

    return y
