#!/usr/bin/env python3

import numpy as np
from orbital.orbital import orbital


class optimizer_ga(orbital):

  def __init__(self):

    print("Constructing class: GA")

    self.str_num_generation = 'number_generationn'
    self.str_residual       = 'residual'
    self.str_population     = 'population'
    self.str_error          = 'solution'
    self.str_best_index     = 'best_index'

    self.text_color = '\033[96m'
    self.text_end = '\033[0m'

    return


  def initial_setting(self, config):

    result_dir = config['GA']['result_dir']
    super().make_directory_rm(result_dir)

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


  def generate_population(self, parameter_boundary):
    population = np.array( [np.random.uniform(low=bound_low, high=bound_high) for bound_low, bound_high in parameter_boundary] )
    return population


  def is_odd(self, i):
    return i % 2 != 0


  #def fitness_function(self, position):
  #  return objective_function(position)


  def reshape_array(self, var, num_dim):
    #下記のreshape追加の理由、Bayesian　Optの引数が(1,dim)の次元になるので、それに合わせている。
    return var.reshape(1,num_dim)


  def run_optimizer_ga(self, config, fitness_function, parameter_boundary):

    # Number of iteration
    num_generation = config['GA']['num_generation']
    # Number of population
    num_population = config['GA']['num_population']
    # Rate of mutation
    mutation_rate = config['GA']['mutation_rate']
    # Limit of mutation
    mutation_limit = config['GA']['mutation_limit']
    # Number of dimensions
    num_dimension = self.num_dimension
    # Acture number of iteration after optimization
    num_generation_optimized = num_generation

    # Odd-even check
    if self.is_odd(num_population):
      print('The population size was odd, so for implementation convenience, it was corrected to an even number')
      num_population = num_population + 1

    # Generating initial population
    population = []
    for i in range(num_population):
      population_tmp = self.generate_population(parameter_boundary)
      #population_tmp = np.random.uniform(low=bound_lower, high=bound_upper, size=num_dimension)
      population.append(population_tmp)
    #population = np.array(population)

    # History
    best_index_history = np.zeros(num_generation, dtype=int)
    population_history = np.zeros(num_generation*num_population*num_dimension).reshape(num_generation,num_population,num_dimension)
    solution_history   = np.zeros(num_generation*num_population).reshape(num_generation,num_population)

    # For residual
    solution_init = np.ones(num_population)
    solution_prev = np.ones(num_population)
    residual = np.zeros(num_population)
    residaul_mean_history = []

    # Iteration of genetic algorithm
    for n in range(num_generation):
      # Fitness computations (objective function)
      fitness_values = np.zeros(num_population)
      for i in range(num_population):
        population_tmp = self.reshape_array( population[i],num_dimension ) 
        fitness_values[i] = fitness_function( population_tmp )
        
      if n == 0: 
        solution_init[:] = fitness_values[:].copy() 

      # Selection of the best individual
      best_index = np.argmin(fitness_values)
      best_individual = population[best_index]
      best_fitness = fitness_values[best_index] #np.min(fitness_values)

      # History
      population_history[n,:,:] = population
      solution_history[n,:]     = fitness_values
      best_index_history[n]     = best_index

      # Generating a new population (Selection, Crossover, Mutation)
      new_population = []
      for i in range(num_population//2):
        # Tournament selection (Randomly select two individuals and choose the one with the better fitness)
        tournament_indices = np.random.choice(range(num_population), size=2, replace=False)
        tournament_fitness = fitness_values[tournament_indices]
        selected_index = tournament_indices[np.argmin(tournament_fitness)]
        selected_individual = population[selected_index]
        
         #Crossover (Take a simple average)
        crossover_individual = np.mean([selected_individual, best_individual], axis=0)
        
        # Mutation (Randomly perturb individuals slightly)
        if np.random.rand() < mutation_rate:
          mutation_amount = np.random.uniform(low=-mutation_limit, high=mutation_limit)
          mutated_individual = selected_individual + mutation_amount
        else:
          mutated_individual = selected_individual
        
        # Adding new individuals to the population
        new_population.extend([crossover_individual, mutated_individual])

      # Update the next generation of individuals
      population = np.array(new_population)

      # Residual of error in objective function
      #!!!solutionはlist型、solution_prevとsolution_initはnp.ndarrayで一貫してない）
      residual = abs((fitness_values - solution_prev)/solution_init)
      residual_mean = np.mean(residual)
      residaul_mean_history.append(residual_mean)
      print('Step:',n+1, ', Relative mean residual:', self.text_color+f'{residual_mean:.10e}'+self.text_end)

      if residual_mean <= config['GA']['tolerance'] :
        num_generation_optimized = n
        break

      solution_prev[:] = fitness_values[:].copy()

    # Output
    print("Best parameter:", best_individual)
    print("Fitness of best solution:", best_fitness)
    for n in range(0,num_generation_optimized):
      i_opt = best_index_history[n]
      print(n+1, i_opt+1, population_history[n,i_opt,:], solution_history[n,i_opt])

    # Store data
    solution_dict = {}
    solution_dict[self.str_num_generation] = num_generation_optimized
    solution_dict[self.str_residual]       = residaul_mean_history
    solution_dict[self.str_population]     = population_history
    solution_dict[self.str_error]          = solution_history
    solution_dict[self.str_best_index]     = best_index_history

    return best_individual, best_fitness, solution_dict


  def write_optimization_process(self, config, solution_dict):

    # Number of iteration
    num_generation = solution_dict[self.str_num_generation]
    # Number of particles
    num_population = config['GA']['num_population']
    # Number of dimension
    num_dimension = self.num_dimension
    # Parameter name list
    solution_name_list = self.parameter_name_list

    # Variables
    population_history    = solution_dict[self.str_population]
    solution_history      = solution_dict[self.str_error]
    best_index_history    = solution_dict[self.str_best_index]
    residaul_mean_history = solution_dict[self.str_residual]

    # Output results
    filename_tmp =  config['GA']['result_dir'] + '/' + config['GA']['filename_output']
    print('--Writing output file...:',filename_tmp)

    file_output = open( filename_tmp , 'w')
    # Header
    header_tmp = "Variables="
    for n in range(0,len(solution_name_list)):
      header_tmp = header_tmp + solution_name_list[n] + ','
    header_tmp = header_tmp + ' ID' + ',' + ' Solution' + ',' + 'Residual_mean' + '\n'
    file_output.write( header_tmp )

    for n in range(0, num_generation):
      text_tmp = 'zone t="Time'+str(n+1) +' sec"' + '\n'
      text_tmp =  text_tmp + 'i='+str(num_population)+' f=point' + '\n'
      for i in range(0, num_population):
        text_tmp = text_tmp
        for j in range(0,num_dimension):
          text_tmp = text_tmp  + str( population_history[n,i,j] ) + ', '
        solution_tmp = solution_history[n,i]
        text_tmp = text_tmp + str(i+1) + ', ' + str(n+1) + ', ' + str(solution_tmp) + '\n'
      file_output.write( text_tmp )
    file_output.close()

    return


  def write_best_solution_history(self, config, solution_dict):

    # Number of iteration
    num_generation = solution_dict[self.str_num_generation]
    # Number of particles
    num_population = config['GA']['num_population']
    # Number of dimension
    num_dimension = self.num_dimension

    # Variables
    best_index_history = solution_dict[self.str_best_index]
    population_history = solution_dict[self.str_population]
    solution_history   = solution_dict[self.str_error]

    # Output results: Global information
    filename_tmp =  config['GA']['result_dir'] + '/' + config['GA']['filename_global']
    print('--Writing best solution file...:',filename_tmp)

    file_output = open( filename_tmp , 'w')
    # Header
    header_tmp = 'Variables = Step, GID, GSolution, '
    for n in range(0,num_dimension):
      header_tmp = header_tmp + 'GParameter_' + str(n+1) + ', '
    header_tmp = header_tmp.rstrip(',') + '\n'
    file_output.write( header_tmp )

    for n in range(0, num_generation):
      i_opt = best_index_history[n]
      g_id  = n*num_population + i_opt
      text_tmp = str(n) + ', ' + str(g_id) + ', ' 
      text_tmp = text_tmp + str(solution_history[n, i_opt]) +  ', ' 
      for m in range(0,num_dimension):
        text_tmp = text_tmp + str( population_history[n, i_opt, m] ) + ', '
      text_tmp = text_tmp.rstrip(',') + '\n'
      file_output.write( text_tmp )
    file_output.close()

    return


  def drive_optimization(self, config, objective_function, parameter_boundary):

    best_condition, best_value, solution_dict = self.run_optimizer_ga(config, objective_function, parameter_boundary)

    self.write_optimization_process(config, solution_dict)

    self.write_best_solution_history(config, solution_dict)

    return