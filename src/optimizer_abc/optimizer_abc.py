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
    self.str_id_history  = 'ID_history'

    self.text_color = '\033[96m'
    self.text_end = '\033[0m'

    return


  def initial_setting(self, config):

    # ディレクトリ作成は Rank 0 のみ
    if self.mpi_instance.rank == 0:
      result_dir = config['ABC']['result_dir']
      super().make_directory_rm(result_dir)

    # 全プロセスがディレクトリ作成完了を待つ
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

    # 重要: 各プロセスで異なる乱数シードを設定する
    # これを忘れると、全プロセスが同じ場所を探索して並列化の意味がなくなる
    #np.random.seed(42 + self.mpi_instance.rank)

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
    #food_source = np.array( [np.random.uniform(low=bound_low, high=bound_high) for bound_low, bound_high in parameter_boundary] )
    food_source = np.array([np.random.uniform(low=b[0], high=b[1]) for b in parameter_boundary])
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
        total_fitness = sum(fitness_values)
        if total_fitness == 0:
            return np.random.randint(len(fitness_values))
        probs = [f / total_fitness for f in fitness_values]
        return np.random.choice(len(fitness_values), p=probs)


  def run_optimizer_abc(self, config, objective_function, parameter_boundary):

    if self.mpi_instance.flag_mpi :
    # MPI情報の取得
      MPI = self.mpi_instance.MPI
      rank = self.mpi_instance.rank
      size = self.mpi_instance.size
      comm = self.mpi_instance.comm
    else:
      rank = 0
      size = 1
      comm = 0

    # 設定の読み込み
    num_optiter = config['ABC']['num_optiter']
    num_employ_bees = config['ABC']['num_employ_bees']
    num_onlook_bees = config['ABC']['num_onlook_bee']
    visit_limit = config['ABC']['vist_limit']
    num_dimension = self.num_dimension

    # 各プロセスの担当範囲を決定
    # 例: 80個を4プロセスなら、各20個
    indices_per_proc = np.array_split(np.arange(num_employ_bees), size)
    my_indices = indices_per_proc[rank]

    # データ保持用
    food_source = np.zeros((num_employ_bees, num_dimension))
    solution = np.zeros(num_employ_bees)
    visit_counter = np.zeros(num_employ_bees, dtype=int)

    # 履歴用
    id_history = np.zeros((num_optiter, num_employ_bees), dtype=int)
    id_history_init = np.zeros((num_employ_bees), dtype=int)
    # 現在のステップでの最新IDを保持する一時配列
    current_ids = np.zeros(num_employ_bees, dtype=int)

    # --- 1. Initialization (担当分のみ計算) ---
    for i in my_indices:
      food_source[i] = self.generate_food_source(parameter_boundary)
      # 重複しないIDを生成
      unique_id = self.generate_unique_id(0, 0, i+1, rank+1)
      solution[i] = objective_function(self.reshape_array(food_source[i], num_dimension), unique_id)
      current_ids[i] = unique_id 

    # 初期化時の同期
    if self.mpi_instance.flag_mpi :
      self._sync_all(MPI, rank, size, comm, food_source, solution, visit_counter, current_ids)

    id_history_init = current_ids

    # 初期状態を全プロセスで共有
    #comm.Allgather(MPI.IN_PLACE, [food_source, MPI.DOUBLE])
    # solutionは1次元配列なので Allallgather か Allreduce で集約
    #solution = comm.allreduce(solution, op=MPI.SUM)

    best_solution = np.min(solution)
    best_food_source = food_source[np.argmin(solution)].copy()

    # History
    best_index_history = np.zeros(num_optiter, dtype=int)
    food_source_history = np.zeros((num_optiter, num_employ_bees, num_dimension))
    solution_history = np.zeros((num_optiter, num_employ_bees))
    residaul_mean_history = []

    solution_init = solution.copy()
    solution_prev = solution.copy()

    # --- Iteration ---
    for n in range(num_optiter):
      # --- 1. Employed bee phase (担当分のみ探索) ---
      for i in my_indices:
        # 更新する次元を1つ選ぶ (k) と、比較対象を選ぶ (j != i)
        k = np.random.randint(num_dimension)
        j = np.random.choice([idx for idx in range(num_employ_bees) if idx != i])
        phi = np.random.uniform(-1, 1)
        
        v = food_source[i].copy()
        v[k] = food_source[i, k] + phi * (food_source[i, k] - food_source[j, k])
        # 境界チェック（クリッピング）
        v[k] = np.clip(v[k], parameter_boundary[k][0], parameter_boundary[k][1])
        
        unique_id = self.generate_unique_id(n+1, 1, i+1, rank+1)
        sol_v = objective_function(self.reshape_array(v, num_dimension), unique_id )
        if self.fitness_value_function(sol_v) > self.fitness_value_function(solution[i]):
          food_source[i] = v
          solution[i] = sol_v
          visit_counter[i] = 0
          current_ids[i] = unique_id
        else:
          visit_counter[i] += 1
          current_ids[i] = unique_id
      
      # フェーズ終了後に全プロセスを同期
      if self.mpi_instance.flag_mpi :
        self._sync_all(MPI, rank, size, comm, food_source, solution, visit_counter, current_ids)

      # --- 2. Onlooker bee phase ---
      fitness_values = [self.fitness_value_function(s) for s in solution]
      # 追従蜂も担当を分ける (sizeで割る)
      my_onlook_count = num_onlook_bees // size + (1 if rank < num_onlook_bees % size else 0)
      
      for m_idx in range(my_onlook_count):
        i = self.roulette_wheel_selection(fitness_values)
        # 雇用蜂と同じ近傍探索を行う
        k = np.random.randint(num_dimension)
        j = np.random.choice([idx for idx in range(num_employ_bees) if idx != i])
        phi = np.random.uniform(-1, 1)
        
        v = food_source[i].copy()
        v[k] = food_source[i, k] + phi * (food_source[i, k] - food_source[j, k])
        v[k] = np.clip(v[k], parameter_boundary[k][0], parameter_boundary[k][1])

        unique_id = self.generate_unique_id(n+1, 2, (m_idx+my_onlook_count*rank)+1, rank+1)
        sol_v = objective_function(self.reshape_array(v, num_dimension), unique_id)
        # ここで i は自分の担当外の可能性もあるが、計算効率のため「自分が選んだ i 」の更新に責任を持つ
        if self.fitness_value_function(sol_v) > self.fitness_value_function(solution[i]):
          food_source[i] = v
          solution[i] = sol_v
          visit_counter[i] = 0
          current_ids[i] = unique_id
        else:
          visit_counter[i] += 1
          current_ids[i] = unique_id

      if self.mpi_instance.flag_mpi :
        self._sync_all(MPI, rank, size, comm, food_source, solution, visit_counter, current_ids)

      # --- 3. Scout bee phase ---
      for local_idx in my_indices:
        if visit_counter[local_idx] > visit_limit:
          unique_id = self.generate_unique_id(n+1, 3, local_idx+1, rank+1)
          # 新しい蜜源の生成と評価
          food_source[local_idx] = self.generate_food_source(parameter_boundary)
          solution[local_idx] = objective_function(self.reshape_array(food_source[local_idx], num_dimension), unique_id)
          current_ids[local_idx] = unique_id
          # カウンターリセット
          visit_counter[local_idx] = 0
  
      # 重要：スカウトによって更新された情報を全プロセスに波及させる     
      if self.mpi_instance.flag_mpi :
        self._sync_all(MPI, rank, size, comm, food_source, solution, visit_counter, current_ids)

      # --- Update Global Best & History ---
      current_min_idx = np.argmin(solution)
      #print('rank, test-current_min',rank, current_min_idx,solution)
      if solution[current_min_idx] < best_solution:
        best_solution = solution[current_min_idx]
        best_food_source = food_source[current_min_idx].copy()

      food_source_history[n] = food_source.copy()
      solution_history[n] = solution.copy()
      best_index_history[n] = current_min_idx
      id_history[n] = current_ids.copy()

      residual = np.abs((solution - solution_prev) / (solution_init + 1e-20))
      residual_mean = np.mean(residual)
      residaul_mean_history.append(residual_mean)

      if rank == 0:
        print(f'Step: {n+1}, Best: {best_solution:.5e}, Residual: {self.text_color}{residual_mean:.10e}{self.text_end}')

      if residual_mean <= config['ABC']['tolerance']:
        num_optiter = n + 1
        break
      
      solution_prev = solution.copy()

    # Output
    if rank == 0:
      print('Best condition:', best_food_source )
      print('Best value:', best_solution )
      print('Step, Best-condition index, Best condition, Best solution')
      for n in range(0,num_optiter):
        i_opt = best_index_history[n]
        print(n+1, i_opt+1, id_history[n,i_opt], food_source_history[n,i_opt,:], solution_history[n,i_opt])

    # Dictionary作成 (Rank 0のみが保存に使う)
    solution_dict = {
            self.str_num_optiter: num_optiter,
            self.str_residual: residaul_mean_history,
            self.str_food_source: food_source_history[:num_optiter],
            self.str_error: solution_history[:num_optiter],
            self.str_best_index: best_index_history[:num_optiter],
            self.str_id_history: id_history[:num_optiter]
        }

    return best_food_source, best_solution, solution_dict

  def _sync_all(self, MPI, rank, size, comm, food_source, solution, visit_counter, current_ids):
    #rank = self.mpi_instance.rank
    #size = self.mpi_instance.size
    # 自分の担当インデックスを再取得
    indices_per_proc = np.array_split(np.arange(len(solution)), size)
    my_indices = indices_per_proc[rank]
    
    # 1. 担当以外をゼロにした一時的な配列を作成
    fs_tmp = np.zeros_like(food_source)
    sol_tmp = np.zeros_like(solution)
    vc_tmp = np.zeros_like(visit_counter)
    id_tmp = np.zeros_like(current_ids)
    
    fs_tmp[my_indices] = food_source[my_indices]
    sol_tmp[my_indices] = solution[my_indices]
    vc_tmp[my_indices] = visit_counter[my_indices]
    id_tmp[my_indices] = current_ids[my_indices]
    
    # 2. 全プロセスで合計(SUM)して同期。これで全員が最新の「全データ」を持つ。
    comm.Allreduce(fs_tmp, food_source, op=MPI.SUM)
    comm.Allreduce(sol_tmp, solution, op=MPI.SUM)
    comm.Allreduce(vc_tmp, visit_counter, op=MPI.SUM)
    comm.Allreduce(id_tmp, current_ids, op=MPI.SUM)

  def generate_unique_id(self, iter_idx, phase_idx, bee_idx, rank):
    # 一意のIDを生成する
    # 桁数の設計例（10進数でわかる形式）
    # [イテレーション: 10^7] [フェーズ: 10^6] [鉢番号: 10^3] [ランク: 1]
    # 例: 第12ステップ, Phase 2, Bee 15, Rank -> 12 2 015 004
    # - イテレーション: 10,000,000の位 (最大999回)
    # - フェーズ: 1,000,000の位 (0-9)
    # - 蜂番号: 1,000の位 (最大999ランクまで)
    # - MPIランク: 1の位 (最大999個まで)
    #unique_id = (iter_idx * 10000000) + (phase_idx * 1000000) + (bee_idx * 1000) + rank
    unique_id = (iter_idx * 10000) + (phase_idx * 1000) + (bee_idx)
    return int(unique_id)

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
    id_history            = solution_dict[self.str_id_history]

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
      text_tmp = 'zone t="Time'+str(n+1) +' sec"' + '\n'
      text_tmp =  text_tmp + 'i='+str(num_employ_bees)+' f=point' + '\n'
      for i in range(0, num_employ_bees):
        text_tmp = text_tmp
        for j in range(0,num_dimension):
          text_tmp = text_tmp  + str( food_source_history[n,i,j] ) + ', '
        text_tmp = text_tmp + str(id_history[n,i]) + ', ' + str(solution_history[n,i]) + ', ' + str(residaul_mean_history[n]) + '\n'
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
    id_history            = solution_dict[self.str_id_history]

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
      g_id  = id_history[n,i_opt]
      text_tmp = str(n+1) + ', ' + str(g_id) + ', ' 
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