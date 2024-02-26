#!/usr/bin/env python3

import numpy as np
from orbital.orbital import orbital


class pso(orbital):

  def __init__(self):

    print("Constructing class: PSO")

    self.str_num_optiter = 'number_iteration'
    self.str_residual = 'residual_hisotry'
    self.str_position = 'position'
    self.str_velocity = 'velocity'
    self.str_error = 'Error'

    return


  def initial_setting(self, config):

    result_dir = config['PSO']['result_dir']
    super().make_directory_rm(result_dir)

    return


  def boundary_setting(self, config):

    # Setting parameter's boundaries

    boundary = config['parameter_optimized']['boundary']
    parameter_boundary = []
    for n in range(0, len(boundary) ):
      parameter_component = boundary[n]['component']
      for m in range(0, len(parameter_component)):
        parameter_boundary.append( (parameter_component[m]['bound_min'],parameter_component[m]['bound_max']) )

    return parameter_boundary


  def run_pso(self, config, objective_function, parameter_boundary):

    # Dimension 
    boundary = config['parameter_optimized']['boundary']
    num_dimension = 0
    for n in range(0, len(boundary) ):
      parameter_component = boundary[n]['component']
      for m in range(0, len(parameter_component)):
        num_dimension = num_dimension + 1

    # Number of particles
    num_particle = config['PSO']['num_particle']

    # Number of iteration
    num_optiter = config['PSO']['num_optiter']

    # Particle parameters
    inertia        = config['PSO']['inertia']
    cognitive_coef = config['PSO']['cognitive_coef']
    social_coef    = config['PSO']['social_coef']

    # Initialize particles
    particle_position = []
    particle_velocity = []
    particle_best_position = []
    particle_best_value = []
    for n in range(0, num_particle):
      position_tmp = np.array( [np.random.uniform(low, high) for low, high in parameter_boundary] )
      velocity_tmp = np.array( [np.random.uniform(-1, 1) for _ in range(num_dimension)] )
      particle_position.append( position_tmp )
      particle_velocity.append( velocity_tmp )
      particle_best_position.append( particle_position.copy() )
      particle_best_value.append( float('inf') )

    global_best_position = None  # グローバルベスト位置
    global_best_value = float('inf')  # グローバルベストの目的関数値

    # Vizualization
    particle_position_viz = np.zeros(num_optiter*num_particle*num_dimension).reshape(num_optiter,num_particle,num_dimension)
    particle_velocity_viz = np.zeros(num_optiter*num_particle*num_dimension).reshape(num_optiter,num_particle,num_dimension)
    particle_solutioin    = np.zeros(num_optiter*num_particle).reshape(num_optiter,num_particle)

    num_optiter_optimized = num_optiter

    particle_best_value_init = np.ones(num_particle)
    particle_best_value_prev = np.ones(num_particle)
    residual = np.zeros(num_particle)
    residaul_mean_history = []

    for i in range(0, num_optiter):
      for n in range(0, num_particle):
        # パーソナルベストの更新: 下記のreshape追加の理由、Bayesian　Optの引数が(1,dim)の次元になるので、それに合わせている。
        value = objective_function( particle_position[n].reshape(1, num_dimension) )
        if value < particle_best_value[n]:
          particle_best_position[n] = particle_position[n].copy()
          particle_best_value[n] = value
    
        # グローバルベストの更新
        if value < global_best_value:
          global_best_position = particle_position[n].copy()
          global_best_value = value

        particle_solutioin[i,n] = value

      if i == 0: 
        particle_best_value_init[:] = particle_best_value[:].copy() 

      # パーティクルの速度の更新
      for n in range(0, num_particle):
        rand1 = np.random.rand(num_dimension)
        rand2 = np.random.rand(num_dimension)
        cognitive_velocity = cognitive_coef * rand1 * (particle_best_position[n] - particle_position[n])
        social_velocity    = social_coef * rand2 * (global_best_position - particle_position[n])

        # Update position and velocity of particle
        particle_velocity[n] = inertia * particle_velocity[n] + cognitive_velocity + social_velocity
        particle_position[n] = particle_position[n] + particle_velocity[n]

        particle_position_viz[i,n,:] =  particle_position[n][:]
        particle_velocity_viz[i,n,:] =  particle_velocity[n][:]

      # Residual of error in objective function
      residual = abs((particle_best_value- particle_best_value_prev)/particle_best_value_init)
      residual_mean = np.mean(residual)
      residaul_mean_history.append(residual_mean)
      print("Step, relative mean residual, ", i, f'{residual_mean:.10e}')

      if residual_mean <= config['PSO']['tolerance'] :
        num_optiter_optimized = i
        break

      particle_best_value_prev[:] = particle_best_value[:].copy()

    print("Best position:", global_best_position)
    print("Best value:", global_best_value)

    # Store data
    solution_dict = {}
    solution_dict[self.str_num_optiter] = num_optiter_optimized
    solution_dict[self.str_residual]    = residaul_mean_history
    solution_dict[self.str_position]    = particle_position_viz
    solution_dict[self.str_velocity]    = particle_velocity_viz
    solution_dict[self.str_error]       = particle_solutioin

    return global_best_position, global_best_value, solution_dict


  def write_optimization_process(self, config, solution_dict):

    # Number of iteration
    num_optiter = solution_dict[self.str_num_optiter]

    # Number of particles
    num_particle = config['PSO']['num_particle']

    # Dimension 
    boundary = config['parameter_optimized']['boundary']
    solution_name_list = []
    num_dimension = 0
    for n in range(0, len(boundary) ):
      parameter_component = boundary[n]['component']
      for m in range(0, len(parameter_component)):
        solution_name_list.append( parameter_component[m]['type'] )
        num_dimension = num_dimension + 1 

    for n in range(0, len(boundary) ):
      parameter_component = boundary[n]['component']
      for m in range(0, len(parameter_component)):
        solution_name_list.append( parameter_component[m]['type']+'_Velocity' )

    # Variables
    particle_position_viz = solution_dict[self.str_position]
    particle_velocity_viz = solution_dict[self.str_velocity]
    particle_solutioin = solution_dict[self.str_error]

    # Output results: Particles
    filename_tmp =  config['PSO']['result_dir'] + '/' + config['PSO']['filename_output']
    print('--Writing output file...:',filename_tmp)

    file_output = open( filename_tmp , 'w')
    # Header
    header_tmp = "Variables="
    for n in range(0,len(solution_name_list)):
      header_tmp = header_tmp + solution_name_list[n] + ','
    # Addition
    header_tmp = header_tmp + ' ID' + ',' + ' Error' + ',' + 'Residual_mean' + '\n'
    file_output.write( header_tmp )

    for i in range(0, num_optiter):
      text_tmp = 'zone t="Time'+str(i+1) +' sec"' + '\n'
      text_tmp =  text_tmp + 'i='+str(num_particle)+' f=point' + '\n'
      for n in range(0, num_particle):
        text_tmp = text_tmp
        for m in range(0,num_dimension):
          text_tmp = text_tmp  + str( particle_position_viz[i,n,m] ) + ', '
        for m in range(0,num_dimension):
          text_tmp = text_tmp  + str( particle_velocity_viz[i,n,m] ) + ', '
        text_tmp = text_tmp + str(n+1) + ', ' + str(particle_solutioin[i,n]) + '\n'
      file_output.write( text_tmp )
    file_output.close()


  def write_objective_function(self, config, objective_function):
    # Function shape
    flag_function_output = False
    if flag_function_output :
      filename_tmp='tecplot_function.dat'
      file_output = open( filename_tmp , 'w')
      header_tmp = "Variables = X, Error"  + '\n'
      file_output.write( header_tmp )
      x_len = 100
      x_ref = np.linspace(-10,10,x_len)
      text_tmp = 'zone t="Function_ref"' + '\n'
      text_tmp =  text_tmp + 'i='+str(x_len)+' f=point' + '\n'
      for i in range(0, x_len):
        solution_tmp = objective_function( x_ref[i] )
        text_tmp = text_tmp + str(x_ref[i]) + ',' + str(solution_tmp) + '\n'
      file_output.write( text_tmp )
      file_output.close()

    return

  def drive_optimization(self, config, objective_function, parameter_boundary):

    best_position, best_value, solution_dict = self.run_pso(config, objective_function, parameter_boundary)

    self.write_optimization_process(config, solution_dict)

    #self.write_objective_function(config, objective_function)

    return

