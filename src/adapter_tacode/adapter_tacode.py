#!/usr/bin/env python3

import numpy as np
import os as os
import shutil as shutil
from orbital.orbital import orbital


class adapter_tacode(orbital):

  def __init__(self):

    print("Constructing class: adapter_tacode")

    return

  
  def initial_settings(self, config):

    self.work_dir      = config['tacode']['work_dir']
    self.case_dir      = config['tacode']['case_dir']
    #self.template_path = config['tacode']['template_path']

    path_specify = config['tacode']['directory_path_specify']
    default_path = '/../../testcase_template' 
    manual_path  = config['tacode']['manual_path']
    self.template_path = self.get_directory_path(path_specify, default_path, manual_path)

    # Make directory
    super().make_directory_rm(self.work_dir)
  
    self.work_dir_template = self.work_dir+'/'+self.case_dir+'_template'
    shutil.copytree(self.template_path, self.work_dir_template)

    self.filename_control_tacode    = config['tacode']['filename_control']
    self.filename_trajectory_tacode = config['tacode']['filename_trajectory']

    self.cmd_tacode = config['tacode']['cmd_tacode']
    self.root_dir   = os.getcwd()
    self.cmd_home = os.path.dirname(os.path.realpath(__file__)) + '/..'

    # Target parameter
    self.parameter_target = config['Bayes_optimization']['boundary']

    # Counter
    self.iter = 1
  
    #self.process_list = []

    return


  def reference_data_setting(self, config):

    # File directory and name setting
    path_specify = config['reference']['directory_path_specify']
    default_path = '/../../testcase_template/case_day118.339/output' 
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

    time_opt      = trajectory_time[0]
    longitude_opt = trajectory_mean[0]
    latitude_opt  = trajectory_mean[1]
    altitude_opt  = trajectory_mean[2]

    geodetic_coord_opt  = [longitude_opt,latitude_opt,altitude_opt]

    # For optimization
    self.unit_covert_timeunit = self.set_timeunit( config['reference']['timeunit'] )
    self.time_sec_opt  = time_opt
    self.time_day_opt  = time_opt/self.unit_covert_timeunit
    self.longitude_opt = geodetic_coord_opt[0]
    self.latitude_opt  = geodetic_coord_opt[1]
    self.altitude_opt  = geodetic_coord_opt[2]

    #self.i_target_opt         = super().getNearestIndex(self.time_sec_opt, config['tacode']['target_time']*self.unit_covert_timeunit)
    _, self.i_target_opt      = super().closest_value_index(self.time_sec_opt, config['tacode']['target_time']*self.unit_covert_timeunit)
    self.target_time_opt      = self.time_day_opt[self.i_target_opt]
    self.target_longitude_opt = self.longitude_opt[self.i_target_opt]
    self.target_latitude_opt  = self.latitude_opt[self.i_target_opt]
    self.target_altitude_opt  = self.altitude_opt[self.i_target_opt]

    print('Time at start position:       ',self.target_time_opt, 'day')
    print('Initial Geodetic coordinate, :',self.target_longitude_opt,'deg.,',self.target_latitude_opt,'deg.,',self.target_altitude_opt,'km')

    # Used in Tacode trajectory (:trajectory.dat) for comparison with GPR result
    self.time_start      = config['tacode']['time_start']
    self.time_end        = config['tacode']['time_end']
    self.target_time_set = config['tacode']['target_time']

    # Result file
    self.result_dir       = config['tacode']['result_dir']
    self.flag_tecplot     = config['tacode']['flag_tecplot']
    self.header_tecplot   = config['tacode']['header_tecplot']
    self.filename_tecplot = config['tacode']['filename_tecplot']

    # Make directory
    super().make_directory(self.result_dir)

    return


  def boundary_setting(self, config):

    boundary = config['Bayes_optimization']['boundary']
    bounds = []
    for n in range(0, len(boundary) ):
      boundary_name = boundary[n]['name']
#      boundary_name = boundary[n]['name'].rsplit('.', 1)
#      print(boundary_name[0])
      parameter_component = boundary[n]['component']
      for m in range(0,  len(parameter_component)):
        bound_type = parameter_component[m]['type']
        bound_min  = parameter_component[m]['bound_min']
        bound_max  = parameter_component[m]['bound_max']
        bounds.append( {'name': bound_type, 'type': 'continuous', 'domain': (bound_min, bound_max) } )
        print( 'Boundary in',bound_type,'component of',boundary_name,'(min--max):', bound_min,'--',bound_max)

    return bounds


  def rewrite_control_file(self,filename,txt_indentified,ele_indentified,txt_replaced):
    # 
    # txt_indentifiedの文字列を含む行を抽出し、その(ele_indentified)列目要素を置換する。
    # 何度もファイル開閉をするのは問題かもしれない
    print(filename,txt_indentified,ele_indentified,txt_replaced)

    for m in range(0,ele_indentified):
      # Reading control file
      with open(filename) as f:
        lines = f.readlines()

      # リストとして取得 
      lines_strip = [line.strip() for line in lines]

      # 置換する行を特定する
      # i_line    = [i for i, line in enumerate(lines_strip) if txt_indentified in line]
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


  def run_tacode(self):
    import subprocess
    # Tacodeの実行
    
    # 計算ディレクトリに移動、実行、元ディレクトリに戻る
    os.chdir( self.work_dir_case )
#    subprocess.call('pwd')

    # Get relative path
    #current_path  = os.getcwd()
    #relative_path = os.path.relpath(self.cmd_home, current_path)

    # Run Tacode
    #try:
    #  # 相対パスにあるプログラムを実行
    #  subprocess.run([self.cmd_tacode, relative_path], check=True)
    #except subprocess.CalledProcessError as e:
    #  print("Error:", e)
    #  exit()

    subprocess.call( self.cmd_tacode )

    os.chdir( self.root_dir )

    return


  def evaluate_error(self):
    # Tacodeによるトラジェクトリ結果とGPR結果の誤差を評価する

    # Trajectoryデータの読み込み
    filename_tmp = self.work_dir_case+'/'+self.filename_trajectory_tacode
    print('--Reading trajectory file (tacode)... :',filename_tmp)
    time_sec, longitude, latitude, altitude, velocity,  density, temperature, kn = super().read_inputdata_tacode(filename_tmp)
    velocity_long = velocity[0]
    velocity_lat  = velocity[1]
    velocity_alt  = velocity[2]
    velocity_mag  = velocity[3]

    # 開始時刻をGPRデータと合わせる
    time_day        = time_sec/orbital.unit_covert_day2sec
    time_day_offset = time_day+self.target_time_set
    time_sec_offset = time_sec+self.target_time_set*orbital.unit_covert_day2sec

    i_start = super().getNearestIndex(time_day_offset, self.time_start)
    i_end   = super().getNearestIndex(time_day_offset, self.time_end)

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

    if( self.flag_tecplot ):
      number_padded     = '{0:04d}'.format(self.iter)
      filename_tmp      = super().split_file(self.result_dir+'/'+self.filename_tecplot,'_case'+number_padded,'.')
      header_tmp        = self.header_tecplot
      print_message_tmp = '--Writing tecplot file... '
      delimiter_tmp     = '\t'
      comments_tmp      = ''
      output_tmp        = np.c_[time_day_offset, longitude, latitude, altitude, velocity_long, velocity_lat, velocity_alt, velocity_mag, density, temperature, kn, time_sec_offset]
      super().write_tecplotdata( filename_tmp, print_message_tmp, header_tmp, delimiter_tmp, comments_tmp, output_tmp )

    return error_tmp


  def f_tacode(self,x):
    # Tacodeのコントロールファイルを適切に修正して、tacodeを実行する。

    print('Iteration: ', self.iter)

    # Caseディレクトリの作成
    number_padded      = '{0:04d}'.format(self.iter)
    self.work_dir_case = self.work_dir+'/'+self.case_dir+number_padded
    print('--Case directory: ', self.work_dir_case)
    shutil.copytree(self.work_dir_template, self.work_dir_case)

    # コントロールファイルの書き換え 
    print('--Modification: control file')
    filename_ctl = self.work_dir_case+'/'+self.filename_control_tacode

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
        txt_replaced.append( str( x[0,count] ) )
        count = count + 1
      print('Variable:',var_name_ctl,'in',var_root_ctl, ',Parameters:',txt_replaced)
      self.rewrite_control_file(filename_ctl, txt_indentified, ele_indentified, txt_replaced)

    # Tacodeの実行
    print('--Start Tacode')
    self.run_tacode()
    print('--End Tacode')

    # Trajectoryファイルの読み込みと誤差評価
    print('--Evaluating error between Tacode and GPR results')
    error = self.evaluate_error()
    print('--Done, Error between Tacode and GPR: ',error)

    # カウンタの更新
    self.iter += 1

    return error
