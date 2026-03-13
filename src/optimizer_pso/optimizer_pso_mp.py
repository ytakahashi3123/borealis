#!/usr/bin/env python3

import numpy as np
from multiprocessing import Pool, cpu_count
from orbital.orbital import orbital

# multiprocessing worker global
# multiprocessing が worker に task を送るときに、
# module/class method/closureのような、 pickleできないオブジェクトが含まれているとエラーが生じる。
# したがって、ここではobjective_function をタスク引数から外す

_objective_function = None

def init_worker(obj_func):
  global _objective_function
  _objective_function = obj_func

def evaluate_particle(args):
  particle_id, position, iteration, num_particle, num_dimension, sign_of = args
  serial_id = iteration * num_particle + particle_id + 1
  value = _objective_function(
    position.reshape(1, num_dimension),
    serial_id,
    iteration,
    sign_of
  )
  return particle_id, value


# PSO_MP class
class optimizer_pso_mp(orbital):

  def __init__(self, mpi_instance):

    print("Constructing class: PSO (multiprocessing)")

    self.mpi_instance = mpi_instance # Not used

    self.str_num_optiter = 'number_iteration'
    self.str_residual = 'residual_history'
    self.str_position = 'position'
    self.str_velocity = 'velocity'
    self.str_error = 'error'
    self.str_global_index = 'global_particle_index'

    self.text_color = '\033[96m'
    self.text_end = '\033[0m'

    return


  def initial_setting(self, config):

    # initial setting

    result_dir = config['PSO']['result_dir']
    super().make_directory_rm(result_dir)

    boundary = config['parameter_optimized']['boundary']

    parameter_name_list = []
    num_dimension = 0
    for n in range(len(boundary)):
      parameter_component = boundary[n]['component']
      for m in range(len(parameter_component)):
        parameter_name_list.append(parameter_component[m]['type'])
        num_dimension += 1

    self.num_dimension = num_dimension
    self.parameter_name_list = parameter_name_list

    # Parameter boundary at initial step
    try:
      self.boundary_initial = config['parameter_optimized']['boundary_initial']
      self.flag_boundary_initial = True
    except (KeyError):
      self.flag_boundary_initial = False

    # Parameter velocity at initial step
    try:
      self.velocity_initial = config['parameter_optimized']['velocity_initial']
      self.flag_velocity_initial = True
    except (KeyError):
      self.flag_velocity_initial = False

    # Kind of computation of redisuals
    try:
      self.kind_residual_computation = config['PSO']['kind_residual_computation']
    except (KeyError, TypeError):
      self.kind_residual_computation = 'relative_change'
    print(f'[PSO-Borealis] Residual computation: {self.kind_residual_computation}')

    return


  def boundary_setting(self, config):

    # Setting parameter's boundaries

    boundary = config['parameter_optimized']['boundary']
    parameter_boundary = []
    for n in range(len(boundary)):
      parameter_component = boundary[n]['component']
      for m in range(len(parameter_component)):
        parameter_boundary.append( ( parameter_component[m]['bound_min'], parameter_component[m]['bound_max'] ) )

    return parameter_boundary


    # PSO main
  def run_pso(self, config, objective_function, parameter_boundary):

    # Dimension 
    num_dimension = self.num_dimension

    # Number of particles
    num_particle = config['PSO']['num_particle']
    # Number of iteration
    num_optiter = config['PSO']['num_optiter']

    # Actual number of iteration after optimization
    num_optiter_optimized = num_optiter

    # Particle parameters
    inertia = config['PSO']['inertia']
    cognitive_coef = config['PSO']['cognitive_coef']
    social_coef = config['PSO']['social_coef']

    # Maximization or minimization of the objective function
    maximize = config['PSO']['maximize']
    sign_of = -1.0 if maximize else 1.0

    nproc = config['PSO'].get("num_process", cpu_count())

    print("[PSO] Using processes:", nproc)

    #pool = Pool(nproc)
    pool = Pool(
      nproc,
      initializer=init_worker,
      initargs=(objective_function,)
    )

    particle_position = np.zeros((num_particle, num_dimension))
    particle_velocity = np.zeros((num_particle, num_dimension))

    for n in range(num_particle):

      # Initialize particle positions
      if self.flag_boundary_initial:
        low  = self.boundary_initial['bound_min']
        high = self.boundary_initial['bound_max']
        position_tmp = []
        for m in range(len(parameter_boundary)):
          position_tmp.append( np.random.uniform(low, high) )
        position_tmp = np.array(position_tmp)
      else:
        position_tmp = np.array( [ np.random.uniform(low, high) for low, high in parameter_boundary] )
      particle_position[n] = position_tmp

      # Initialize particle velocities
      if self.flag_velocity_initial:
        low  = self.velocity_initial['velocity_min']
        high = self.velocity_initial['velocity_max']
        velocity_tmp = np.array([ np.random.uniform(low, high) for _ in range(num_dimension) ])
      else:
        velocity_tmp = np.array([ np.random.uniform(-1.0, 1.0) for _ in range(num_dimension) ])
      particle_velocity[n] = velocity_tmp

    particle_best_position = particle_position.copy()
    particle_best_value = np.full(num_particle, np.inf)

    particle_best_value_init = np.ones(num_particle)
    particle_best_value_prev = np.ones(num_particle)

    residual = np.zeros(num_particle)

    # History arrays
    particle_position_history = np.zeros( (num_optiter, num_particle, num_dimension) )
    particle_velocity_history = np.zeros( (num_optiter, num_particle, num_dimension) )
    particle_solution = np.zeros((num_optiter, num_particle))

    global_best_index_history = np.zeros(num_optiter, dtype=int)

    residual_mean_history = []

    global_best_value = np.inf
    global_best_position = None

    # Optimization loop
    for i in range(num_optiter):
      tasks = [
          (n, particle_position[n], i, num_particle, num_dimension, sign_of)
          for n in range(num_particle)
      ]
      results = pool.map(evaluate_particle, tasks)

      # Process results
      for n, value in results:
        particle_solution[i, n] = value
        if value < particle_best_value[n]:
          particle_best_value[n] = value
          particle_best_position[n] = particle_position[n].copy()
        if value < global_best_value:
          global_best_value = value
          global_best_position = particle_position[n].copy()
          global_best_index_history[i] = n

      if i == 0:
        particle_best_value_init[:] = particle_best_value[:]

      # Udate velocity / position
      for n in range(num_particle):
        particle_position_history[i, n, :] = particle_position[n]
        particle_velocity_history[i, n, :] = particle_velocity[n]

        r1 = np.random.rand(num_dimension)
        r2 = np.random.rand(num_dimension)

        cognitive = cognitive_coef * r1 * (particle_best_position[n] - particle_position[n])
        social = social_coef * r2 * (global_best_position - particle_position[n])

        particle_velocity[n] = inertia * particle_velocity[n] + cognitive + social
        particle_position[n] += particle_velocity[n]

      # Residual of error in objective function
      if self.kind_residual_computation == 'relative_value':
        for n in range(num_particle):
          residual[n] = abs(particle_best_value[n] / particle_best_value_init[n])
      else:
        for n in range(num_particle):
          residual[n] = abs( (particle_best_value[n] - particle_best_value_prev[n]) / particle_best_value_init[n] )

      residual_mean = np.mean(residual)
      residual_mean_history.append(residual_mean)

      print('[PSO-Borealis] Step:',i+1,', Relative mean residual:',self.text_color + f'{residual_mean:.10e}' + self.text_end)
      residual[:] = 0
      if residual_mean <= config['PSO']['tolerance']:
        num_optiter_optimized = i
        break

      particle_best_value_prev[:] = particle_best_value[:]

    pool.close()
    pool.join()

    print(f"[PSO-Borealis] Best parameter: {global_best_position}")
    print(f"[PSO-Borealis] Best value: {global_best_value}")
    for i in range(0,num_optiter_optimized):
      n_opt = global_best_index_history[i]
      particle_position_tmp = particle_position_history[i, n_opt, :]
      solution_tmp = particle_solution[i, n_opt]
      #print(i+1, n_opt+1, particle_position_history[i,n_opt,:], particle_solution[i,n_opt])
      print(f"[PSO-Borealis] Step: {i+1}, Particle: {n_opt+1}, Parameter: {particle_position_tmp}, Solution: {solution_tmp}")

    # Making Solution dict
    solution_dict = {}
    solution_dict[self.str_num_optiter] = num_optiter_optimized
    solution_dict[self.str_residual] = residual_mean_history
    solution_dict[self.str_position] = particle_position_history
    solution_dict[self.str_velocity] = particle_velocity_history
    solution_dict[self.str_error] = particle_solution
    solution_dict[self.str_global_index] = global_best_index_history

    return global_best_position, global_best_value, solution_dict


  # Output optimization history
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
    for n in range(0, len(boundary)):
      parameter_component = boundary[n]['component']
      for m in range(0, len(parameter_component)):
        solution_name_list.append(parameter_component[m]['type'] + '_Velocity')

    # Variables
    particle_position_history = solution_dict[self.str_position]
    particle_velocity_history = solution_dict[self.str_velocity]
    particle_solution         = solution_dict[self.str_error]
    residaul_mean_history     = solution_dict[self.str_residual]

    # Output results: Particles
    filename_tmp = config['PSO']['result_dir'] + "/" + config['PSO']['filename_output']
    print("[PSO-Borealis] --Writing output file:", filename_tmp)

    file_output = open(filename_tmp, 'w')
    # Header
    header_tmp = "Variables="
    for n in range(0, len(solution_name_list)):
      header_tmp = header_tmp + solution_name_list[n] + ','
    # Addition
    header_tmp = header_tmp + ' ID' + ',' + ' Error' + ',' + 'Residual_mean' + '\n'
    file_output.write(header_tmp)

    for i in range(0, num_optiter):
      text_tmp = 'zone t="Time' + str(i) + ' sec"' + '\n'
      text_tmp = text_tmp + 'i=' + str(num_particle) + ' f=point' + '\n'
      for n in range(0, num_particle):
        text_tmp = text_tmp
        for m in range(0, num_dimension):
          text_tmp = text_tmp + str(particle_position_history[i, n, m]) + ', '
        for m in range(0, num_dimension):
          text_tmp = text_tmp + str(particle_velocity_history[i, n, m]) + ', '
        text_tmp = text_tmp + str(n+1) + ', ' + str(particle_solution[i, n]) + ' ,' + str(residaul_mean_history[i]) + '\n'
      file_output.write(text_tmp)
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
    particle_solution         = solution_dict[self.str_error]
    global_best_index_history = solution_dict[self.str_global_index]

    # Output results: Global particle information
    filename_tmp =  config['PSO']['result_dir'] + '/' + config['PSO']['filename_global']
    print('[PSO-Borealis] --Writing global solution file...:',filename_tmp)

    file_output = open( filename_tmp , 'w')
    # Header
    header_tmp = 'Variables = Step, GID, GSolution, '
    for n in range(0,num_dimension):
      header_tmp = header_tmp + 'GParameter_' + str(n+1) + ', '
    header_tmp = header_tmp.rstrip(',') + '\n'
    file_output.write( header_tmp )

    for i in range(0, num_optiter):
      n_opt = global_best_index_history[i]
      g_id  = i*num_particle + n_opt
      text_tmp = str(i) + ', ' + str(g_id) + ', ' 
      text_tmp = text_tmp + str(particle_solution[i, n_opt]) +  ', ' 
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

    best_position, best_value, solution_dict = self.run_pso(config,objective_function,parameter_boundary)

    self.write_optimization_process(config, solution_dict)

    self.write_best_solution_history(config, solution_dict)

    return