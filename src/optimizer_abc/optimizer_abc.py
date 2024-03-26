#!/usr/bin/env python3

import numpy as np
from orbital.orbital import orbital


class optimizer_abc(orbital):

  def __init__(self,mpi_instance):

    print("Constructing class: ABC")

    self.mpi_instance = mpi_instance

    self.str_num_optiter = 'number_iteration'
    self.str_residual    = 'residual'
    self.str_food_source = 'food_source'
    self.str_error       = 'solution'
    self.str_best_index  = 'best_index'

    self.text_color = '\033[96m'
    self.text_end = '\033[0m'

    return


  def initial_setting(self, config):

    if self.mpi_instance.rank == 0:
      result_dir = config['ABC']['result_dir']
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


  def generate_food_source(self, parameter_boundary):
    food_source = np.array( [np.random.uniform(low=bound_low, high=bound_high) for bound_low, bound_high in parameter_boundary] )
    return food_source


  def fitness_value_function(self, solutioin):
    # Solution: Solution of objective function
    if solutioin >= 0:
      fitness = 1.0/(1.0+solutioin)
    else: 
      fitness = 1.0+abs(solutioin)
    return fitness


  def reshape_array(self, var, num_dim):
    #下記のreshape追加の理由、Bayesian　Optの引数が(1,dim)の次元になるので、それに合わせている。
    return var.reshape(1,num_dim)


  def roulette_wheel_selection(self, fitness_values):
    # Calculate the total sum of the fitness values of each individual
    total_fitness = sum(fitness_values)  
    # Select a random position on the roulette wheel
    selected_point = np.random.uniform(0, total_fitness)
    # Locate the individual corresponding to the selected position
    cumulative_fitness = 0
    for i, fitness in enumerate(fitness_values):
      cumulative_fitness += fitness
      if cumulative_fitness >= selected_point:
        return i


  def run_optimizer_abc(self, config, objective_function, parameter_boundary):

    # Number of iteration
    num_optiter = config['ABC']['num_optiter']
    # Number of employed bees 
    num_employ_bees = config['ABC']['num_employ_bees']
    # Number of onlooking bees 
    num_onlook_bees = config['ABC']['num_onlook_bee']
    # Limit of visit
    vist_limit = config['ABC']['vist_limit']
    # Number of dimensions
    num_dimension = self.num_dimension
    # Acture number of iteration after optimization
    num_optiter_optimized = num_optiter

    # Visit counter
    visit_counter = np.zeros(num_employ_bees).astype(int)

    # Best solution
    #best_food_source = float('inf')
    best_solution = float('inf')

    # For history record
    best_index_history  = np.zeros(num_optiter, dtype=int)
    food_source_history = np.zeros(num_optiter*num_employ_bees*num_dimension).reshape(num_optiter,num_employ_bees,num_dimension)
    solution_history    = np.zeros(num_optiter*num_employ_bees).reshape(num_optiter,num_employ_bees)

    # For residual
    solution_init = np.ones(num_employ_bees)
    solution_prev = np.ones(num_employ_bees)
    residual = np.zeros(num_employ_bees)
    residaul_mean_history = []

    # Initialization phase
    food_source = []
    solution = []
    for i in range(num_employ_bees):
      food_source_tmp = self.generate_food_source(parameter_boundary)
      food_source.append( food_source_tmp )
      solution.append( objective_function( self.reshape_array(food_source_tmp,num_dimension)) ) 

    solution_init[:] = solution[:].copy() 

    # Iteration
    for n in range(num_optiter):

      # Employed bee phase
      for i in range(num_employ_bees):
        phi = 2.0*np.random.rand(num_dimension) - 1.0
        index = np.random.randint(num_employ_bees-1)
        food_source_new = food_source[i] + phi*( food_source[i] - food_source[index] )
        solution_new = objective_function( self.reshape_array(food_source_new,num_dimension) )
        # Update source
        if self.fitness_value_function( solution_new ) > self.fitness_value_function( solution[i] ):
          food_source[i] = food_source_new
          solution[i]    = solution_new
          visit_counter[i] = 0
        else:
          visit_counter[i] += 1

      # Onlooker bee phase
      fitness_values = []
      for i in range(num_employ_bees):
        fitness_values.append( self.fitness_value_function( solution[i] ) )
      for i in range(num_onlook_bees):
        # Select randomly according to the evaluation value of the food source
        index = self.roulette_wheel_selection( fitness_values )
        # The acquisition count of the food source +1
        visit_counter[index] += 1

      # Scout bee phase
      for i in range(num_employ_bees):
        # Replace the food sources that have been visited more than a certain number of times
        if visit_counter[i] > vist_limit:
          food_source[i] = self.generate_food_source(parameter_boundary)
          solution[i] = objective_function( self.reshape_array(food_source[i], num_dimension) )
          visit_counter[i] = 0

      # Update best solution
      for i in range(num_employ_bees):
        if best_solution > solution[i] :
          best_food_source = food_source[i]
          best_solution = solution[i]

      # History
      food_source_history[n,:,:] = food_source[:]
      solution_history[n,:] = solution[:]
      min_index = np.argmin(solution)
      best_index_history[n] = min_index

      # Residual of error in objective function
      #!!!solutionはlist型、solution_prevとsolution_initはnp.ndarrayで一貫してない）
      residual = abs((solution - solution_prev)/solution_init)
      residual_mean = np.mean(residual)
      residaul_mean_history.append(residual_mean)
      print('Step:',n+1, ', Relative mean residual:', self.text_color+f'{residual_mean:.10e}'+self.text_end)

      if residual_mean <= config['ABC']['tolerance'] :
        num_optiter_optimized = n
        break

      solution_prev[:] = solution[:].copy()

    # Output
    print('Best condition:', best_food_source )
    print('Best value:', best_solution )
    print('Step, Best-condition index, Best condition, Best solution')
    for n in range(0,num_optiter_optimized):
      i_opt = best_index_history[n]
      print(n+1, i_opt+1, food_source_history[n,i_opt,:], solution_history[n,i_opt])

    # Store data
    solution_dict = {}
    solution_dict[self.str_num_optiter] = num_optiter_optimized
    solution_dict[self.str_residual]    = residaul_mean_history
    solution_dict[self.str_food_source] = food_source_history
    solution_dict[self.str_error]       = solution_history
    solution_dict[self.str_best_index]  = best_index_history

    return best_food_source, best_solution, solution_dict


  def write_optimization_process(self, config, solution_dict):

    # Number of iteration
    num_optiter = solution_dict[self.str_num_optiter]
    # Number of particles
    num_employ_bees = config['ABC']['num_employ_bees']
    # Number of dimension
    num_dimension = self.num_dimension
    # Parameter name list
    solution_name_list = self.parameter_name_list

    # Variables
    food_source_history   = solution_dict[self.str_food_source]
    solution_history      = solution_dict[self.str_error]
    best_index_history    = solution_dict[self.str_best_index]
    residaul_mean_history = solution_dict[self.str_residual]

    # Output results
    filename_tmp =  config['ABC']['result_dir'] + '/' + config['ABC']['filename_output']
    print('--Writing output file...:',filename_tmp)

    file_output = open( filename_tmp , 'w')
    # Header
    header_tmp = "Variables="
    for n in range(0,len(solution_name_list)):
      header_tmp = header_tmp + solution_name_list[n] + ','
    # Addition
    header_tmp = header_tmp + ' ID' + ',' + ' Solution' + ',' + 'Residual_mean' + '\n'
    file_output.write( header_tmp )

    for n in range(0, num_optiter):
      text_tmp = 'zone t="Time'+str(n) +' sec"' + '\n'
      text_tmp =  text_tmp + 'i='+str(num_employ_bees)+' f=point' + '\n'
      for i in range(0, num_employ_bees):
        text_tmp = text_tmp
        for j in range(0,num_dimension):
          text_tmp = text_tmp  + str( food_source_history[n,i,j] ) + ', '
        text_tmp = text_tmp + str(i+1) + ', ' + str(solution_history[n,i]) + ', ' + str(residaul_mean_history[n]) + '\n'
      file_output.write( text_tmp )
    file_output.close()

    return


  def write_best_solution_history(self, config, solution_dict):

    # Number of iteration
    num_optiter = solution_dict[self.str_num_optiter]
    # Number of particles
    num_employ_bees = config['ABC']['num_employ_bees']
    # Number of dimension
    num_dimension = self.num_dimension

    # Variables
    best_index_history    = solution_dict[self.str_best_index]
    food_source_history   = solution_dict[self.str_food_source]
    solution_history      = solution_dict[self.str_error]

    # Output results: Global information
    filename_tmp =  config['ABC']['result_dir'] + '/' + config['ABC']['filename_global']
    print('--Writing best solution file...:',filename_tmp)

    file_output = open( filename_tmp , 'w')
    # Header
    header_tmp = 'Variables = Step, GID, GSolution, '
    for n in range(0,num_dimension):
      header_tmp = header_tmp + 'GParameter_' + str(n+1) + ', '
    header_tmp = header_tmp.rstrip(',') + '\n'
    file_output.write( header_tmp )

    for n in range(0, num_optiter):
      i_opt = best_index_history[n]
      g_id  = n*num_employ_bees + i_opt
      text_tmp = str(n) + ', ' + str(g_id) + ', ' 
      text_tmp = text_tmp + str(solution_history[n, i_opt]) +  ', ' 
      for m in range(0,num_dimension):
        text_tmp = text_tmp + str( food_source_history[n, i_opt, m] ) + ', '
      text_tmp = text_tmp.rstrip(',') + '\n'
      file_output.write( text_tmp )
    file_output.close()

    return


  def drive_optimization(self, config, objective_function, parameter_boundary):

    best_condition, best_value, solution_dict = self.run_optimizer_abc(config, objective_function, parameter_boundary)

    if self.mpi_instance.rank == 0:
      self.write_optimization_process(config, solution_dict)

    if self.mpi_instance.rank == 0:
      self.write_best_solution_history(config, solution_dict)

    return