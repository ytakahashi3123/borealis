#!/usr/bin/env python3

import numpy as np
import os as os
import shutil as shutil
import yaml as yaml
import sys as sys
import matplotlib.pyplot as plt
import matplotlib.animation as animation


def read_config_yaml(file_control):
  print("Reading control file...:", file_control)
  try:
    with open(file_control) as file:
      config = yaml.safe_load(file)
  except Exception as e:
    print('Exception occurred while loading YAML...', file=sys.stderr)
    print(e, file=sys.stderr)
    sys.exit(1)
  return config

def insert_suffix(filename, suffix, splitchar):
  parts = filename.split(splitchar)
  if len(parts) == 2:
    new_filename = f"{parts[0]}{suffix}.{parts[1]}"
    return new_filename
  else:
    # ファイル名が拡張子を含まない場合の処理
    return filename + suffix

def read_header_tecplot(filename, headerline, headername, var_list):
  # Set header
  with open(filename) as f:
    lines = f.readlines()
  # リストとして取得
  lines_strip = [line.strip() for line in lines]
  # ”Variables ="を削除した上で、カンマとスペースを削除
  variables_line = lines_strip[headerline].replace(headername, '')
  variables_line = variables_line.replace(',', ' ').replace('"', ' ')
  # 空白文字で分割して単語のリストを取得
  words = variables_line.split()

  # set variables
  result_var   = var_list
  result_index = []
  for i in range( 0,len(result_var) ):
    for n in range( 0,len(words) ):
      if result_var[i] == words[n] :
        result_index.append(n)
        break

  return result_index


def main():

  # Read parameters
  file_control = 'make_history.yml'
  config = read_config_yaml(file_control)

  # Initial settings
  filename_base = config['filename_base_input']
  str_series = config['str_series']
  step_start = config['step_start']
  step_end   = config['step_end']
  step_digit = config['step_digit']

  # Data variables
  var_x = config['variable_x']
  var_y = config['variable_y']
  var_list = [var_x, var_y]
  headername_tmp = config['headername']
  headerline_variables = config['headerline']
  num_skiprows = config['num_skiprows']

  # Animation
  fig, ax = plt.subplots()
  animate, = ax.plot([], [])
  ax.set_xlim( config['limit_x'][0], config['limit_x'][1] )
  ax.set_ylim( config['limit_y'][0], config['limit_y'][1] )
  #ax.set_aspect('equal') # グラフのアスペクト比を１：１に設定

  title_base = config['title_base']
  animate_title = ax.set_title("")
  #my_text = ax.text(10, 0, "")

  color_map = plt.get_cmap(config['color_map'])
  interval = config['interval']

  def read_resultfile(frame):
    n = frame+1
    number_padded = str(n).zfill(step_digit)
    filename_tmp = insert_suffix(filename_base, str_series+number_padded, '.')
    print('--Reading output file...:',filename_tmp)
    data_input = np.loadtxt(filename_tmp,comments=('#'),delimiter=None,skiprows=num_skiprows)

    var_index = read_header_tecplot(filename_tmp, headerline_variables, headername_tmp, var_list)
    # Store data as dictionary
    result_dict = {}
    for m in range( 0,len(var_list) ):
      result_dict[ var_list[m] ] = data_input[:,var_index[m]]

    x = result_dict[var_x]
    y = result_dict[var_y]
#    animate.set_color(color_map(n / step_end))  # フレームごとの色を設定
    animate.set_color('c')  # フレームごとの色を設定
    animate.set_data(x,y)
    animate_title.set_text( title_base+" at n="+str(n) )
    
    #my_text.set_x(x[1])
    #my_text.set_y(y[1])
    #my_text.set_text(f"theta={n%360}°")

  anim = animation.FuncAnimation(fig, read_resultfile, interval=interval, frames=step_end)

  # Read reference data if necessary
  if config['flag_read_reference'] :
    filename_tmp = config['filename_reference']
    var_x_ref = config['variable_x_reference']
    var_y_ref = config['variable_y_reference']
    var_list_tmp = [var_x_ref, var_y_ref]

    headername_tmp = config['headername_reference']
    headerline_tmp = config['headerline_reference']
    var_index = read_header_tecplot(filename_tmp, headerline_tmp, headername_tmp, var_list_tmp)

    num_skiprows_tmp = config['num_skiprows_reference']
    data_ref = np.loadtxt(filename_tmp,comments=('#'),delimiter=None,skiprows=num_skiprows_tmp)

    reference_dict = {}
    for m in range( 0,len(var_list_tmp) ):
      reference_dict[ var_list_tmp[m] ] = data_ref[:,var_index[m]]
    x_ref = reference_dict[var_x_ref]
    y_ref = reference_dict[var_y_ref]
    ax.grid()
    ax.plot(x_ref, y_ref, color=config['color_map_reference'], label=config['label_reference'])
    ax.legend(loc=0)

  # Output
  filename_movie = config['filename_movie']
  anim.save(filename_movie)
  #plt.show()
  plt.close()


if __name__ == '__main__':

  main()