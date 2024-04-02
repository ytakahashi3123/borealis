#!/usr/bin/env python3

import numpy as np
import os as os
import shutil as shutil
import subprocess as subprocess
from orbital.orbital import orbital


class adapter_tacode(orbital):

  def __init__(self,mpi_instance):

    print("Constructing class: adapter_tacode")

    self.mpi_instance = mpi_instance

    return

  
  def initial_settings(self, config):

    self.work_dir   = config['tacode']['work_dir']
    self.case_dir   = config['tacode']['case_dir']
    self.step_digit = config['tacode']['step_digit']

    # Make directory
    if self.mpi_instance.rank == 0:
      super().make_directory_rm(self.work_dir)

    # Template case 
    path_specify = config['tacode']['directory_path_specify']
    default_path = '../../testcase_template' 
    manual_path  = config['tacode']['manual_path']
    self.template_path = self.get_directory_path(path_specify, default_path, manual_path)
  
    self.work_dir_template = self.work_dir+'/'+self.case_dir+'_template'
    if self.mpi_instance.rank == 0:
      shutil.copytree(self.template_path, self.work_dir_template)

    # Control file and computed result file
    self.filename_control_code    = config['tacode']['filename_control']
    self.filename_result_code = config['tacode']['filename_result']

    # Execution file
    self.cmd_code = config['tacode']['cmd_code']
    self.root_dir = os.getcwd()
    self.cmd_home = os.path.dirname(os.path.realpath(__file__)) + '/..'

    # Target parameter (corresponding to the parameter boundary)
    self.parameter_target = config['parameter_optimized']['boundary']

    # Result file: Make directory
    if self.mpi_instance.rank == 0:
      super().make_directory_rm(config['tacode']['result_dir'])

    # Control file 
    self.config = config

    # Counter
    self.iter = 1
     
    # Check code system
    if not ( (config['tacode']['code_system'] == 'python3' or config['tacode']['code_system'] == 'fortran') ):
      print('Error, code system of tacode is not supported. Only Tacode-Python3 or Ttacode-Fortran are avaiable.')
      print('Please check code system in configuration file of Borealis:',config['tacode']['code_system'])
      print('Program stopped.')
      exit()

    # Variables of trajectory file computed by Tacode
    if config['tacode']['code_system'] == 'python3' :
      self.str_time_sec  = 'Time[s]'
      self.str_longitude = 'Long[deg.]'
      self.str_latitude  = 'Lati[deg.]'
      self.str_altitude  = 'Alti[km]'
      self.str_velocity_longitude = 'Upl[m/s]'
      self.str_velocity_latitude  = 'Vpl[m/s]'
      self.str_velocity_altitude  = 'Wpl[m/s]'
      self.str_velocity_magnitude = 'VelplAbs[m/s]'
      self.str_density = 'Dens[kg/m3]'
      self.str_temperature = 'Temp[K]'
      self.str_knudsen     = 'Kn'
      self.str_time_day    = 'Time[day]'
    elif config['tacode']['code_system'] == 'fortran' :
      self.str_time_sec  = 'time[s]'
      self.str_longitude = 'longitude[deg]'
      self.str_latitude  = 'latitude[deg]'
      self.str_altitude  = 'altitude[km]'
      self.str_velocity_longitude = 'vel_long[m/s]'
      self.str_velocity_latitude  = 'velo_lati[m/s]'
      self.str_velocity_altitude  = 'velo_alt[m/s]'
      self.str_velocity_magnitude = 'vel_mag[m/s]'
      self.str_density = 'density[kg/m3]'
      self.str_temperature = 'temperature[K]'
      self.str_knudsen     = 'Kn'
      self.str_time_day    = 'Time[day]'

    #self.result_var = ['Time[s]','Long[deg.]','Lati[deg.]','Alti[km]','Upl[m/s]','Vpl[m/s]','Wpl[m/s]','VelplAbs[m/s]','Dens[kg/m3]','Temp[K]','Kn']
    #self.result_var_fortran = ['step', 'time[s]','longitude[deg]','latitude[deg]','altitude[km]','vel_long[m/s]','velo_lati[m/s]','velo_alt[m/s]','vel_mag[m/s]','density[kg/m3]','temperature[K]','Kn']

    self.result_var = [ self.str_time_sec, self.str_longitude, self.str_latitude, self.str_altitude, \
                        self.str_velocity_longitude, self.str_velocity_latitude, self.str_velocity_altitude, self.str_velocity_magnitude, \
                        self.str_density, self.str_temperature, self.str_knudsen ]
 
    # For trajectory data reading
    if config['tacode']['code_system'] == 'python3' :
      self.headerline_variables = 1
      self.num_skiprows = 3
    elif config['tacode']['code_system'] == 'fortran' :
      self.headerline_variables = 0
      self.num_skiprows = 2

    # 同期をとる
    if self.mpi_instance.flag_mpi:
      self.mpi_instance.comm.Barrier()

    return


  def reference_data_setting(self, config):

    # File directory and name setting
    path_specify = config['reference']['directory_path_specify']
    default_path = '../../testcase_template/case_day118.339/output' 
    manual_path  = config['reference']['manual_path']
    reference_path = self.get_directory_path(path_specify, default_path, manual_path)
    filename  = config['reference']['filename_input']

    # Reading reference data
    var_x = config['reference']['var_x'] 
    var_y = config['reference']['var_y']
    trajectory_time = []
    trajectory_mean = []
    trajectory_std  = []
    for i in range(0,len(var_y)):
      filename_tmp = super().split_file(reference_path+'/'+filename,'_'+var_y[i],'.') 
      print('Reading ',var_y[i],' data...',':', filename_tmp)
      data_input   = np.loadtxt(filename_tmp,comments=('#'),delimiter=None,skiprows=1)
      time     = data_input[:,0]
      mean     = data_input[:,1]
      std      = data_input[:,2]

      trajectory_time.append(time)
      trajectory_mean.append(mean)
      trajectory_std.append(std)   

    # For optimization
    self.unit_covert_timeunit = self.set_timeunit( config['reference']['timeunit'] )
    self.time_sec_opt  = trajectory_time[0]
    self.time_day_opt  = trajectory_time[0]/self.unit_covert_timeunit
    self.longitude_opt = trajectory_mean[0]
    self.latitude_opt  = trajectory_mean[1]
    self.altitude_opt  = trajectory_mean[2]

    _, self.i_target_opt      = super().closest_value_index(self.time_sec_opt, config['tacode']['target_time']*self.unit_covert_timeunit)
    self.target_time_opt      = self.time_day_opt[self.i_target_opt]
    self.target_longitude_opt = self.longitude_opt[self.i_target_opt]
    self.target_latitude_opt  = self.latitude_opt[self.i_target_opt]
    self.target_altitude_opt  = self.altitude_opt[self.i_target_opt]

    print('Time at start position:       ',self.target_time_opt, 'day')
    print('Initial Geodetic coordinate, :',self.target_longitude_opt,'deg.,',self.target_latitude_opt,'deg.,',self.target_altitude_opt,'km')

    return


  @orbital.time_measurement_decorated
  def rewrite_control_file_code(self, parameter_opt):
    
    # 何度もファイル開閉をするのは問題かもしれない

    print('--Modify control file')

    filename = self.work_dir_case+'/'+self.filename_control_code

    count = 0
    parameter_target = self.parameter_target
    for n in range(0, len(parameter_target ) ):
      parameter_name = parameter_target[n]['name'].rsplit('.', 1)
      parameter_component = parameter_target[n]['component']

      var_root_ctl = parameter_name[0]
      var_name_ctl = parameter_name[1]

      txt_indentified = var_name_ctl
      ele_indentified = len(parameter_component)
      txt_replaced = []
      for m in range(0, len(parameter_component) ):
        txt_replaced.append( str( parameter_opt[0,count] ) )
        count = count + 1
      print('--Variable:',var_name_ctl,'in',var_root_ctl, ', Parameters:',txt_replaced)

      # File operation
      for m in range(0,ele_indentified):
        # Reading control file
        with open(filename) as f:
          lines = f.readlines()

        # リストとして取得 
        lines_strip = [line.strip() for line in lines]

        # 置換する行を特定する
        line_both        = [(i, line) for i, line in enumerate(lines_strip) if txt_indentified in line]
        i_line, str_line = list(zip(*line_both))

        # 抽出した行をスペース・タブで分割する。そのele_indentified列目を置換し、line_replacedというstr型に戻す。
        words = lines_strip[i_line[0]+m+1].split()
        # Replace (words[0]に該当する'-'は置換しない、その次のwords[1]を置換する)
        words[1] = txt_replaced[m]
        # インデントを考慮して新しい行を構築
        line_replaced  = ' '.join(words)

        # 行を置換
        # lines_newはリストになることに注意。そのため、'',joinでstr型に戻す
        lines_updated = [item.replace( lines_strip[i_line[0]+m+1], line_replaced ) for item in lines]

        str_lines_new = ''.join(lines_updated)

        # Update the file
        with open(filename, mode="w") as f:
          f.write(str_lines_new)
    
    return

  @orbital.time_measurement_decorated
  def rewrite_control_code_fortran(self,parameter_opt):
    
    # txt_indentifiedの文字列を含む行を抽出し、その(ele_indentified+1)番目要素を置換する。

    print('--Modify control file')

    filename = self.work_dir_case+'/'+self.filename_control_code

    count = 0
    parameter_target = self.parameter_target
    for n in range(0, len(parameter_target ) ):
      parameter_name = parameter_target[n]['name']
      parameter_component = parameter_target[n]['component']

      var_name_ctl = parameter_name

      txt_indentified = var_name_ctl
      ele_indentified = len(parameter_component)
      txt_replaced = []
      for m in range(0, len(parameter_component) ):
        txt_replaced.append( str( parameter_opt[0,count] ) + ',' )
        count = count + 1
      txt_replaced[-1] = txt_replaced[-1].rstrip(',')
      print('--Variable:',var_name_ctl, ', Parameters:',txt_replaced)

      # File operation
      with open(filename) as f:
        lines = f.readlines()

      # リストとして取得 
      lines_strip = [line.strip() for line in lines]

      # 置換する行を特定する
      line_both        = [(i, line) for i, line in enumerate(lines_strip) if txt_indentified in line]
      i_line, str_line = list(zip(*line_both))
      # 抽出した行をスペース・タブで分割する。そのele_indentified+1番目を置換し、line_replacedというstr型に戻す。
      words = lines_strip[i_line[0]].split()
      for n in range(0, ele_indentified ):
        words[n] = txt_replaced[n]
      line_replaced  = ' '.join(words)

      # lines_newはリストになることに注意。そのため、'',joinでstr型に戻す
      lines_new     = [item.replace( lines_strip[i_line[0]], line_replaced ) for item in lines]
      str_lines_new = ''.join(lines_new)

      # 同じファイル名で保存
      with open(filename, mode="w") as f:
        f.write(str_lines_new)
    
    return


  @orbital.time_measurement_decorated
  def run_code(self):
    
    print('--Run code')

    # Move to computing directory, run Tacode, and return to the original directory
    os.chdir( self.work_dir_case )
    subprocess.call( self.cmd_code )
    os.chdir( self.root_dir )

    return


  @orbital.time_measurement_decorated
  def evaluate_error(self, result_dict):

    # Tacodeによるトラジェクトリ結果とReferenceの誤差を評価する

    print('--Evaluating error between computed result and reference data')

    longitude       = result_dict[ self.str_longitude ]
    latitude        = result_dict[ self.str_latitude ]
    altitude        = result_dict[ self.str_altitude ]
    time_sec_offset = result_dict[ self.str_time_sec ]
    time_day_offset = result_dict[ self.str_time_day ]

    time_start      = self.config['tacode']['time_start']
    time_end        = self.config['tacode']['time_end']
    target_time_set = self.config['tacode']['target_time']

    _, i_start = super().closest_value_index(time_day_offset, time_start)
    _, i_end   = super().closest_value_index(time_day_offset, time_end)

    # 誤差評価の計算
    error_tmp = 0.0
    count_tmp = 0
    for n in range(i_start, i_end):
      count_tmp = count_tmp+1
      for m in range(0,len(self.time_day_opt)):
        if (self.time_day_opt[m] >= time_day_offset[n] ):
          m_opt = m
          break
      grad_fact = ( time_day_offset[n] - self.time_day_opt[m_opt-1] )/( self.time_day_opt[m_opt] - self.time_day_opt[m_opt-1] )
#      longitude_opt_cor = ( self.longitude_opt[m_opt] - self.longitude_opt[m_opt-1] )*grad_fact + self.longitude_opt[m_opt-1]
#      latitude_opt_cor  = ( self.latitude_opt[m_opt]  - self.latitude_opt[m_opt-1]  )*grad_fact + self.latitude_opt[m_opt-1]
      altitude_opt_cor  = ( self.altitude_opt[m_opt]  - self.altitude_opt[m_opt-1]  )*grad_fact + self.altitude_opt[m_opt-1]
      error_tmp = error_tmp + ( altitude[n] - altitude_opt_cor )**2 

#        error_tmp = error_tmp/float(count_tmp)
    error_tmp = np.sqrt( error_tmp/float(count_tmp) )

    # Green color
    print('--Error:','\033[92m'+str(error_tmp)+'\033[0m', 'in Epoch',str(self.iter) )

    return error_tmp


  @orbital.time_measurement_decorated
  def read_result_data(self):
    
    # Trajectoryデータの読み込み
    filename = self.work_dir_case+'/'+self.filename_result_code

    print("--Reading computed results by Tacode...:",filename)

    # Set header
    with open(filename) as f:
      lines = f.readlines()
    # リストとして取得
    lines_strip = [line.strip() for line in lines]
    # ”Variables ="を削除した上で、カンマとスペースを削除
    variables_line = lines_strip[self.headerline_variables].replace('Variables =', '')
    variables_line = variables_line.replace(',', ' ').replace('"', ' ')
    # 空白文字で分割して単語のリストを取得
    words = variables_line.split()

    # set variables
    result_var   = self.result_var
    result_index = []
    for i in range( 0,len(result_var) ):
      for n in range( 0,len(words) ):
        if result_var[i] == words[n] :
          result_index.append(n)
          #print( result_var[i], words[n], i, n)
          break

    # Read data
    data_input = np.loadtxt(filename,comments=('#'),delimiter=None,skiprows=self.num_skiprows)

    # Store data as dictionary
    result_dict = {}
    for n in range( 0,len(result_var) ):
      result_dict[ result_var[n] ] = data_input[:,result_index[n]]

    # 開始時刻をGPRデータと合わせる
    time_start      = self.config['tacode']['time_start']
    time_end        = self.config['tacode']['time_end']
    target_time_set = self.config['tacode']['target_time']

    time_sec        = result_dict[ self.str_time_sec ]
    time_day        = time_sec/orbital.unit_covert_day2sec
    time_day_offset = time_day+target_time_set
    time_sec_offset = time_sec+target_time_set*orbital.unit_covert_day2sec

    # Update time variables offset
    result_dict[ self.str_time_sec ] = time_sec_offset
    result_dict[ self.str_time_day ] = time_day_offset

    return result_dict


  @orbital.time_measurement_decorated
  def write_result_data(self, result_dict):

    if( self.config['tacode']['flag_output'] ):
      longitude     = result_dict[ self.str_longitude ]
      latitude      = result_dict[ self.str_latitude ]
      altitude      = result_dict[ self.str_altitude ]
      velocity_long = result_dict[ self.str_velocity_longitude ]
      velocity_lat  = result_dict[ self.str_velocity_latitude ]
      velocity_alt  = result_dict[ self.str_velocity_altitude ]
      velocity_mag  = result_dict[ self.str_velocity_magnitude ]
      density       = result_dict[ self.str_density ]
      temperature   = result_dict[ self.str_temperature ]
      kn            = result_dict[ self.str_knudsen ]

      time_sec_offset = result_dict[ self.str_time_sec ]
      time_day_offset = result_dict[ self.str_time_day ]

      result_dir        = self.config['tacode']['result_dir']
      filename_output  = self.config['tacode']['filename_output']
      number_padded     = str(self.iter).zfill(self.step_digit)
      filename_tmp      = super().insert_suffix(result_dir+'/'+filename_output,'_case'+number_padded,'.')
      print('--Writing output file...:',filename_tmp)

      result_var_tmp = self.result_var
      header_tmp = "Variables="
      for n in range(0,len(result_var_tmp)):
        header_tmp = header_tmp + result_var_tmp[n] + ','
      header_tmp = header_tmp.rstrip(',')
      # Addition
      header_tmp = header_tmp + ',' + self.str_time_day
      
      delimiter_tmp     = '\t'
      comments_tmp      = ''
      output_tmp        = np.c_[time_sec_offset, longitude, latitude, altitude, velocity_long, velocity_lat, velocity_alt, velocity_mag, density, temperature, kn, time_day_offset]
      np.savetxt(filename_tmp, output_tmp, header=header_tmp, delimiter=delimiter_tmp, comments=comments_tmp )

    return


  @orbital.time_measurement_decorated
#  def objective_function(self, id_serial, parameter_opt):
  def objective_function(self, parameter_opt, *id_serial):

    # コントロールファイルを適切に修正して、tacodeを実行する。

    if id_serial:
      self.iter = id_serial[0]

    print('Iteration: ', self.iter)

    # Caseディレクトリの作成
    self.work_dir_case = self.work_dir + '/' + self.case_dir + str(self.iter).zfill(self.step_digit)
    print('--Make case directory: ', self.work_dir_case)
    shutil.copytree(self.work_dir_template, self.work_dir_case)

    # コントロールファイルの書き換え 
    if self.config['tacode']['code_system'] == 'python3' :
      self.rewrite_control_file_code(parameter_opt)
    elif self.config['tacode']['code_system'] == 'fortran' :
      self.rewrite_control_code_fortran(parameter_opt)

    # Run Tacode
    self.run_code()

    # Read result for evaluating error
    result_dict = self.read_result_data()

    # Write result data
    self.write_result_data(result_dict)

    # Evaluate error
    error = self.evaluate_error(result_dict)

    # カウンタの更新
    if not id_serial:
      self.iter += 1

    return error
