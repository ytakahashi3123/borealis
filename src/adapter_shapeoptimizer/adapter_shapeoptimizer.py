#!/usr/bin/env python3

# Borealis adapter: Python script to run Borealis with preCICE for Shape Optimization.
# Version: Borealis-v1.4.0
# Release date: 2025/08/31

# Author: Yusuke Takahashi, Hokkaido University
# Contact: ytakahashi@eng.hokudai.ac.jp

import numpy as np
import os
import re
import sys
import shutil as shutil
import subprocess
import time
import signal
from orbital.orbital import orbital

class adapter_shapeoptimizer(orbital):
  
  def __init__(self,mpi_instance):

    print("Constructing class: adapter_shapeoptimizer")

    self.mpi_instance = mpi_instance

    return    


  def initial_settings(self, config):

    # Get current time of the system
    self.current_time = time.time()

    self.work_dir   = config['shapeoptimizer']['work_dir']
    self.case_dir   = config['shapeoptimizer']['case_dir']
    self.step_digit = config['shapeoptimizer']['step_digit']

    # Make directory
    if self.mpi_instance.rank == 0:
      super().make_directory_rm(self.work_dir)

    # Template case 
    path_specify = config['shapeoptimizer']['directory_path_specify']
    default_path = '../../shapeoptimizer'
    manual_path  = config['shapeoptimizer']['manual_path']
    self.template_path = self.get_directory_path(path_specify, default_path, manual_path)

    self.work_dir_template = self.work_dir+'/'+self.case_dir+'_template'
    if self.mpi_instance.rank == 0:
      shutil.copytree(self.template_path, self.work_dir_template)

    # Control file and computed result file
    #self.filename_control_code = config['shapeoptimizer']['filename_control']
    #self.filename_result_code  = config['shapeoptimizer']['filename_result']

    # Execution file
    self.cmd_code = config['shapeoptimizer']['cmd_code']
    self.root_dir = os.getcwd()
    self.cmd_home = os.path.dirname(os.path.realpath(__file__)) + '/..'

    # Target parameter (corresponding to the parameter boundary)
    self.parameter_target = config['parameter_optimized']['boundary']

    # Result file: Make directory
    if self.mpi_instance.rank == 0:
      super().make_directory_rm(config['shapeoptimizer']['result_dir'])

    # Control file 
    self.config = config

    # Counter
    self.step = 1

    # Delete old file
    self.filename_jobrequests = "job_requests"
    #if self.mpi_instance.rank == 0:
    #  if os.path.exists(self.filename_jobrequests):
    #    try:
    #      os.remove(self.filename_jobrequests)
    #      print(f"{self.filename_jobrequests} has been deleted.")
    #    except OSError as e:
    #      print(f"Failed to delete {self.filename_jobrequests}: {e}", file=sys.stderr)
    #      sys.exit(1)  # 終了コード1でスクリプト終了
    #  else:
    #    print(f"{self.filename_jobrequests} does not exist.")

    # 同期をとる
    if self.mpi_instance.flag_mpi:
      self.mpi_instance.comm.Barrier()

    # For result data reading
    #self.headerline_variables = 1
    #self.num_skiprows = 2

    # Get number of dimension and check its consistency
    num_dims = []
    for param in self.parameter_target:
      component_list = param.get('component', [])
      coordinate_list = param.get('coordinate', [])
      num_dim = len(component_list)
      num_dims.append(num_dim)
      #print(f"{param['name']}: number of dimensions = {num_dim}")
    # 全て同じ次元かどうかをチェック
    all_same_dim = all(n == num_dims[0] for n in num_dims)
    if all_same_dim:
      print(f"[ShapeOpt-Borealis] All the dimensions of the parameter are the same: {num_dim} dimensions")
    else:
      print(f"[ShapeOpt-Borealis] Dimenions of the parameter is different")
      print(f"[ShapeOpt-Borealis] Number of dimensions of each element: {num_dims}")
      raise SystemExit()
    self.num_dim = num_dim
    
    # Get number of boundary（= number of "name"
    num_marker = len(self.parameter_target)
    print(f"[ShapeOpt-Borealis] Number of markers: {num_marker}")
    self.num_marker = num_marker

    # Set variables for optimization
    self.displacements = np.zeros((self.num_marker,self.num_dim))
    self.forces_marker = np.zeros(self.num_dim)

    # Caseディレクトリの作成
    self.work_dir_case = self.work_dir + '/' + self.case_dir + '_rank' + str(self.mpi_instance.rank+1).zfill(self.step_digit)
    print('[ShapeOpt-Borealis] --Make case directory: ', self.work_dir_case)
    shutil.copytree(self.work_dir_template, self.work_dir_case)
        
    # Set control parameters
    self.work_dir_series    = config['shapeoptimizer']['work_dir_series']
    forces_file             = config['shapeoptimizer']['filename_forces']
    displacements_file      = config['shapeoptimizer']['filename_displacements']
    self.filename_forces_base        = self.work_dir_case+'/'+self.work_dir_series+'/'+os.path.splitext(forces_file)[0]
    self.filename_forces_ext         = os.path.splitext(forces_file)[1]
    self.filename_displacements_base = self.work_dir_case+'/'+self.work_dir_series+'/'+os.path.splitext(displacements_file)[0]
    self.filename_displacements_ext  = os.path.splitext(displacements_file)[1]
    self.step_digit_series = config['shapeoptimizer']['step_digit_series']

    # Delete old files if the files remain
    self.delete_step_files(forces_file, digit=self.step_digit_series, directory=self.work_dir_case+'/'+self.work_dir_series)
    self.delete_step_files(displacements_file, digit=self.step_digit_series, directory=self.work_dir_case+'/'+self.work_dir_series)

    # Indexes and powers
    #self.index_var_of = config['shapeoptimizer']['index_variable_objectivefunction']
    self.power_var_of = config['shapeoptimizer']['power_variable_objectivefunction']

    return


  def reference_data_setting(self, config):
    # Optimizerの処理で必要。特に何も行わない
    return


  def load_mapped_data(self, filename, nDim=2):
    data = []
    with open(filename, "r") as f:
        # Skip Tecplot headers
        while True:
            line = f.readline()
            if not line:
                raise ValueError("ZONE not found in .dat file.")
            if line.strip().startswith("ZONE"):
                break
        for line in f:
            if not line.strip():
                continue  # skip empty lines
            values = line.strip().split()
            if nDim == 2 :
                d = {
                    "sample_point": [float(values[0]), float(values[1])],
                    "nearest_node_id": int(values[3]),
                    "nearest_node_coord": [float(values[4]), float(values[5])],
                    "triangle_id": int(values[7])
                }
            else:
                d = {
                    "sample_point": [float(values[0]), float(values[1]), float(values[2])],
                    "nearest_node_id": int(values[3]),
                    "nearest_node_coord": [float(values[4]), float(values[5]), float(values[6])],
                    "triangle_id": int(values[7])
                }
            data.append(d)
    return data
  
  def write_displacements(self, filename, displacements):
    if not isinstance(displacements, np.ndarray):
        raise TypeError("[ShapeOpt-Borealis-ERROR] displacements must be a numpy ndarray.")
    if displacements.ndim != 2:
        raise ValueError("[ShapeOpt-Borealis-ERROR] displacements must be a 2D numpy array.")
    try:
        with open(filename, 'w') as f:
            for row in displacements:
                f.write(' '.join(f"{val:.6e}" for val in row) + '\n')
        #print(f"[Borealis-INFO] Displacements written to '{filename}'")
    except Exception as e:
        print(f"[ShapeOpt-Borealis-ERROR] Failed to write displacements to file: {e}")

  def read_forces_marker(self, filename):
    data = []
    with open(filename, 'r') as f:
      for line in f:
        # 空行やコメントを無視したい場合（必要なら）
        line = line.strip()
        if not line or line.startswith('#'):
          continue
        for val in line.split():
          data.append( float(val) )
        #values = [float(val) for val in line.split()]
        #data.append(values)
    return np.array(data)

  def delete_step_files(self, base_file, digit=5, directory="."):
    # 拡張子前の base 名を取得
    base_tmp = os.path.splitext(base_file)[0]  # 'forces'
    # 削除対象の正規表現パターンを作成
    pattern_forces = re.compile(rf"^{re.escape(base_tmp)}_step\d{{{digit}}}\.dat$")
    # 削除ファイルリストの作成：削除
    deleted_files = []
    for filename in os.listdir(directory):
        if pattern_forces.match(filename):
            file_path = os.path.join(directory, filename)
            try:
                os.remove(file_path)
                deleted_files.append(filename)
            except Exception as e:
                print(f"[ShapeOpt-Borealis-WARNING] Could not delete {filename}: {e}")
    print(f"[ShapeOpt-Borealis] Deleted {len(deleted_files)} step files at the previous time:")
    for f in deleted_files:
        print(f"  - {f}")

  def write_request_instruction(self, filename):
    print('[ShapeOpt-Borealis] Writing job requests file')
    size = self.mpi_instance.size # 並列数
    filename_request_instruction = filename
    with open(filename_request_instruction, "w") as f:
      f.write("Directories for subprocesses:\n")
      for n in range(0,size):
        work_dir_case_rank = self.work_dir + '/' + self.case_dir + '_rank' + str(n+1).zfill(self.step_digit)
        f.write(f"{work_dir_case_rank}\n")

  def cleanup(self, proc):
    if proc and proc.poll() is None:
      print(f"[ShapeOpt-Borealis] Terminating subprocess (PID={proc.pid})...")
      proc.terminate()
      try:
        proc.wait(timeout=5)
      except subprocess.TimeoutExpired:
        print("[ShapeOpt-Borealis-WARN] Subprocess did not terminate, killing it.")
        proc.kill()

  def stop_process_freshness(self, flag_freshness,filename, proc):
    if not flag_freshness:
      print(f"[ShapeOpt-Borealis]-ERROR] {filename} might be an old file generated at previous time. Please delete them before starting the process.")
      #print(f"[Borealis] Killing process with PID: {proc.pid}")
      cleanup(proc)
      #proc.send_signal(signal.SIGTERM)  # ソフトな終了
      # proc.kill()  # 強制終了（必要なら）
      raise SystemExit()
      #raise RuntimeError(f"[Borealis-ERROR] {filename} might be an old file generated at previous time. Please delete them before starting the process.")

  def run_subprocess(self):

    print('[ShapeOpt-Borealis] Run subprocess')
    os.chdir( self.work_dir_case )
    #subprocess.call( "./run_SU2-OPT_pps.sh" )
    proc = subprocess.Popen(["./run_SU2-OPT_pps.sh"])
    os.chdir( self.root_dir )

    return proc

  def run_initialprocess(self):

    # Start codes
    proc_code = self.run_subprocess()
    self.cleanup(proc_code)

    return proc_code


  def objective_function(self, parameter_opt, *args):

    if args:
      # args[0]: 粒子ID
      # args[1]: 最適化ステップ
      self.step = args[1]
      # args[2]: 目的関数を最大化するか最小化するか
      sign_of = args[2]

    print('[ShapeOpt-Borealis] Iteration: ', self.step+1)

    step_str = f"{self.step:0{self.step_digit_series}d}"

    # Set displacements data
    filename_displacements_series = f"{self.filename_displacements_base}_step{step_str}{self.filename_displacements_ext}"
    # Write displacements file
    self.displacements = parameter_opt.reshape(self.num_marker, self.num_dim)
    self.write_displacements(filename_displacements_series, self.displacements)
    print(f"[ShapeOpt-Borealis] Step {self.step+1}: Wrote {filename_displacements_series}\n", f"Displacements: {self.displacements[1,:]}..{self.displacements[-1,:]}")

    if self.step == 0:
      if self.mpi_instance.flag_mpi:
        self.mpi_instance.comm.Barrier()
      # 形状最適化(shapeoptimizer_preCICE)サブプロセスの起動指示ファイルを生成
      # ->中間スクリプトがこれを検知して形状最適化を実行する（親プロセスをMPIで起動したとき、親プロセスが子プロセスをMPIで起動できない仕様上このような措置を図る）
      if self.mpi_instance.rank == 0:
        self.write_request_instruction(self.filename_jobrequests)

    # Get forces data
    filename_forces_series = f"{self.filename_forces_base}_step{step_str}{self.filename_forces_ext}"
    while not os.path.exists(filename_forces_series):
      time.sleep(3.0)
    self.forces_marker = self.read_forces_marker(filename_forces_series)
    print(f"[ShapeOpt-Borealis] Step {self.step+1}: Read {filename_forces_series}\n", f"Forces: {self.forces_marker}")

    # Penalty
    penalty = 0.0
    if self.config['parameter_optimized']['flag_penalty']:
      boundary = self.config['parameter_optimized']['boundary']
      huge_tmp = self.config['parameter_optimized']['penalty_value']
      penalty = super().get_penalty_term(parameter_opt, boundary, huge_tmp)

    # Evaluate error
    force_tmp = self.forces_marker[0]**self.power_var_of[0] * self.forces_marker[1]**self.power_var_of[1]
    error = sign_of * abs( force_tmp ) + penalty

    # カウンタの更新
    if not args:
      self.step += 1

    return error
