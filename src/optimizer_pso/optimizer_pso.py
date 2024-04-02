#!/usr/bin/env python3

import numpy as np
from orbital.orbital import orbital


class optimizer_pso(orbital):

  def __init__(self, mpi_instance):

    print("Constructing class: PSO")

    self.mpi_instance = mpi_instance

    self.str_num_optiter = 'number_iteration'
    self.str_residual = 'residual_hisotry'
    self.str_position = 'position'
    self.str_velocity = 'velocity'
    self.str_error = 'error'
    self.str_global_index = 'global_particle_index'

    self.text_color = '\033[96m'
    self.text_end = '\033[0m'

    return


  def initial_setting(self, config):

    if self.mpi_instance.rank == 0:
      result_dir = config['PSO']['result_dir']
      super().make_directory_rm(result_dir)
    if self.mpi_instance.flag_mpi :
      self.mpi_instance.comm.Barrier()

    boundary = config['parameter_optimized']['boundary']
    num_dimension = 0
    parameter_name_list = []
    for n in range(0, len(boundary) ):
      parameter_component = boundary[n]['component']
      for m in range(0, len(parameter_component)):
        parameter_name_list.append( parameter_component[m]['type'] )
        num_dimension = num_dimension + 1

    self.num_dimension = num_dimension
    self.parameter_name_list = parameter_name_list

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
    num_dimension = self.num_dimension

    # Number of particles
    num_particle = config['PSO']['num_particle']

    # Number of iteration
    num_optiter = config['PSO']['num_optiter']

    # Acture number of iteration after optimization
    num_optiter_optimized = num_optiter

    # Particle parameters
    inertia        = config['PSO']['inertia']
    cognitive_coef = config['PSO']['cognitive_coef']
    social_coef    = config['PSO']['social_coef']

    # MPI settings
    flag_mpi = self.mpi_instance.flag_mpi
    if flag_mpi :
      MPI = self.mpi_instance.MPI
      comm = self.mpi_instance.comm
      size = self.mpi_instance.size
      rank = self.mpi_instance.rank
      particle_size = num_particle // size
      num_particle_start = rank * particle_size
      num_particle_end   = (rank + 1) * particle_size if rank < size - 1 else num_particle
      print('Rank, Iter_start, Iter_zend', rank, num_particle_start, num_particle_end)
    else :
      rank = 0
      num_particle_start = 0
      num_particle_end = num_particle

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

    # History
    #global_best_position_hisotry = np.zeros(num_optiter*num_dimension).reshape(num_optiter,num_dimension)
    #global_best_value_hisotry = np.zeros(num_optiter)
    global_best_index_hisotry = np.zeros(num_optiter, dtype=int)

    particle_position_history = np.zeros(num_optiter*num_particle*num_dimension).reshape(num_optiter,num_particle,num_dimension)
    particle_velocity_history = np.zeros(num_optiter*num_particle*num_dimension).reshape(num_optiter,num_particle,num_dimension)
    particle_solutioin        = np.zeros(num_optiter*num_particle).reshape(num_optiter,num_particle)

    # For residual
    particle_best_value_init = np.ones(num_particle)
    particle_best_value_prev = np.ones(num_particle)
    residual = np.zeros(num_particle)
    residaul_mean_history = []

    #count = 0
    for i in range(0, num_optiter):
      # グローバルベスト位置
      global_best_position = None 
      # グローバルベストの目的関数値
      global_best_value = float('inf')
      
      #for n in range(0, num_particle):
      for n in range(num_particle_start, num_particle_end):
        # パーソナルベストの更新: 下記のreshape追加の理由、Bayesian　Optの引数が(1,dim)の次元になるので、それに合わせている。
        id_serial = i*num_particle + n + 1
        value = objective_function( particle_position[n].reshape(1, num_dimension), id_serial )
        particle_solutioin[i,n] = value
        if value < particle_best_value[n]:
          particle_best_position[n] = particle_position[n].copy()
          particle_best_value[n] = value
    
        # グローバルベストの更新
        if value < global_best_value:
          global_best_position = particle_position[n].copy()
          global_best_value = value
          # --History
          #global_best_position_hisotry[i,:] = global_best_position
          #global_best_value_hisotry[i] = global_best_value
          global_best_index_hisotry[i] = n

        #count = count + 1
        #print(count)

      if i == 0: 
        particle_best_value_init[:] = particle_best_value[:].copy() 

      # MPI process
      if flag_mpi :
        global_best_value_g = comm.allreduce(global_best_value, op=MPI.MIN)
        if global_best_value == global_best_value_g :
          rank_l = rank
          global_best_position_l = global_best_position
          global_best_index_l    = global_best_index_hisotry[i]
        else:
          rank_l = -1
          global_best_position_l = global_best_position
          global_best_index_l    = global_best_index_hisotry[i]
        rank_g = comm.allreduce(rank_l, op=MPI.MAX)
        # --Global values
        global_best_position_g = comm.bcast(global_best_position_l, root=rank_g)
        global_best_position   = comm.bcast(global_best_position_l, root=rank_g)
        global_best_value      = global_best_value_g
        global_best_index_g    = comm.bcast(global_best_index_l, root=rank_g)
        global_best_index_hisotry[i] = global_best_index_g

      # パーティクルの速度の更新
      #for n in range(0, num_particle):
      for n in range(num_particle_start, num_particle_end):
        # History
        particle_velocity_history[i,n,:] =  particle_velocity[n][:]
        particle_position_history[i,n,:] =  particle_position[n][:]

        # Update position and velocity of particle for next step
        rand1 = np.random.rand(num_dimension)
        rand2 = np.random.rand(num_dimension)
        cognitive_velocity = cognitive_coef * rand1 * (particle_best_position[n] - particle_position[n])
        social_velocity    = social_coef * rand2 * (global_best_position - particle_position[n])
        particle_velocity[n] = inertia * particle_velocity[n] + cognitive_velocity + social_velocity
        particle_position[n] = particle_position[n] + particle_velocity[n]

      # Residual of error in objective function
      for n in range(num_particle_start, num_particle_end):
        residual[n] = abs((particle_best_value[n] - particle_best_value_prev[n])/particle_best_value_init[n])
      if flag_mpi :
        residual = comm.allreduce(residual, op=MPI.SUM)
      residual_mean = np.mean(residual)
      residaul_mean_history.append(residual_mean)
      if self.mpi_instance.rank == 0:
        print('Step:',i+1, ', Relative mean residual:', self.text_color+f'{residual_mean:.10e}'+self.text_end)
      residual[:] = 0

      if residual_mean <= config['PSO']['tolerance'] :
        num_optiter_optimized = i
        break

      particle_best_value_prev[:] = particle_best_value[:].copy()

    # MPI process for history data
    particle_position_history = comm.allreduce(particle_position_history, op=MPI.SUM)
    particle_velocity_history = comm.allreduce(particle_velocity_history, op=MPI.SUM)
    particle_solutioin        = comm.allreduce(particle_solutioin, op=MPI.SUM)

    if self.mpi_instance.rank == 0:
      print("Best position:", global_best_position)
      print("Best value:", global_best_value)
      for i in range(0,num_optiter_optimized):
        n_opt=global_best_index_hisotry[i]
        print(i+1, n_opt+1, particle_position_history[i,n_opt,:], particle_solutioin[i,n_opt])

    # Store data
    solution_dict = {}
    solution_dict[self.str_num_optiter]  = num_optiter_optimized
    solution_dict[self.str_residual]     = residaul_mean_history
    solution_dict[self.str_position]     = particle_position_history
    solution_dict[self.str_velocity]     = particle_velocity_history
    solution_dict[self.str_error]        = particle_solutioin
    solution_dict[self.str_global_index] = global_best_index_hisotry

    return global_best_position, global_best_value, solution_dict


  def write_optimization_process(self, config, solution_dict):

    # Number of iteration
    num_optiter = solution_dict[self.str_num_optiter]

    # Number of particles
    num_particle = config['PSO']['num_particle']

    # Number of dimension
    num_dimension = self.num_dimension

    # Parameter name list
    solution_name_list = self.parameter_name_list
    boundary = config['parameter_optimized']['boundary']
    for n in range(0, len(boundary) ):
      parameter_component = boundary[n]['component']
      for m in range(0, len(parameter_component)):
        solution_name_list.append( parameter_component[m]['type']+'_Velocity' )

    # Variables
    particle_position_history = solution_dict[self.str_position]
    particle_velocity_history = solution_dict[self.str_velocity]
    particle_solutioin        = solution_dict[self.str_error]
    residaul_mean_history     = solution_dict[self.str_residual]

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
      text_tmp = 'zone t="Time'+str(i) +' sec"' + '\n'
      text_tmp =  text_tmp + 'i='+str(num_particle)+' f=point' + '\n'
      for n in range(0, num_particle):
        text_tmp = text_tmp
        for m in range(0,num_dimension):
          text_tmp = text_tmp  + str( particle_position_history[i,n,m] ) + ', '
        for m in range(0,num_dimension):
          text_tmp = text_tmp  + str( particle_velocity_history[i,n,m] ) + ', '
        text_tmp = text_tmp + str(n+1) + ', ' + str(particle_solutioin[i,n]) + ' ,' + str(residaul_mean_history[i]) +  '\n'
      file_output.write( text_tmp )
    file_output.close()

    return


  def write_best_solution_history(self, config, solution_dict):

    # Number of iteration
    num_optiter = solution_dict[self.str_num_optiter]
    # Number of particles
    num_particle = config['PSO']['num_particle']
    # Number of dimension
    num_dimension = self.num_dimension

    # Variables
    particle_position_history = solution_dict[self.str_position]
    particle_solutioin        = solution_dict[self.str_error]
    global_best_index_hisotry = solution_dict[self.str_global_index]

    # Output results: Global particle information
    filename_tmp =  config['PSO']['result_dir'] + '/' + config['PSO']['filename_global']
    print('--Writing global solution file...:',filename_tmp)

    file_output = open( filename_tmp , 'w')
    # Header
    header_tmp = 'Variables = Step, GID, GSolution, '
    for n in range(0,num_dimension):
      header_tmp = header_tmp + 'GParameter_' + str(n+1) + ', '
    header_tmp = header_tmp.rstrip(',') + '\n'
    file_output.write( header_tmp )

    for i in range(0, num_optiter):
      n_opt = global_best_index_hisotry[i]
      g_id  = i*num_particle + n_opt
      text_tmp = str(i) + ', ' + str(g_id) + ', ' 
      text_tmp = text_tmp + str(particle_solutioin[i, n_opt]) +  ', ' 
      for m in range(0,num_dimension):
        text_tmp = text_tmp + str( particle_position_history[i, n_opt, m] ) + ', '
      text_tmp = text_tmp.rstrip(',') + '\n'
      file_output.write( text_tmp )
    file_output.close()

    return


  def write_objective_function(self, config, objective_function):
    # Function form
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

    if self.mpi_instance.rank == 0:
      self.write_optimization_process(config, solution_dict)

    if self.mpi_instance.rank == 0:
      self.write_best_solution_history(config, solution_dict)

    #self.write_objective_function(config, objective_function)

    return

