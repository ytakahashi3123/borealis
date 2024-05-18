#!/usr/bin/env python3

# Script for making image of optimal solution

import numpy as np
import yaml as yaml
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def read_config_yaml(file_control):
  print("Reading control file...:", file_control)
  try:
    with open(file_control) as file:
      config = yaml.safe_load(file)
  except Exception as e:
    import sys as sys
    print('Exception occurred while loading YAML...', file=sys.stderr)
    print(e, file=sys.stderr)
    sys.exit(1)
  return config


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
  file_control = 'make_image_optimal_result.yml'
  config = read_config_yaml(file_control)

  #file_control_borealis = 'borealis.yml'
  #config_bor =  read_config_yaml(file_control_borealis)

  # Initial settings
  work_dir = config['work_dir']
  filename_result = config['filename_result']

  var_x = config['variable_x']
  var_y = config['variable_y']

  flag_add = config['flag_add']
  if flag_add :
    var_y_add = config['variable_y_add']
    var_list = [var_x, var_y, var_y_add]
  else:
    var_list = [var_x, var_y]

  headername_tmp = config['headername']
  headerline_variables = config['headerline']
  num_skiprows_tmp = config['num_skiprows']
  comments_tmp  = config['comments']
  delimiter_tmp = config['delimiter']

  # Plot and Animation
  fig = plt.figure()
  ax = fig.add_subplot(1, 1, 1)
  ax.set_title(config['title_base'])

  # Plots
  ax.set_xlim( config['axis_x_limit'][0], config['axis_x_limit'][1] )
  ax.set_ylim( config['axis_y_limit'][0], config['axis_y_limit'][1] )
  #ax.set_aspect('equal') # グラフのアスペクト比を１：１に設定

  ax.set_xlabel( config['axis_x_label'] )
  ax.set_ylabel( config['axis_y_label'] )

  # Read reference data if necessary
  flag_ref = config['flag_read_reference']
  if flag_ref :
    var_x_ref = config['variable_x_reference']
    var_y_ref = config['variable_y_reference']
    var_list_ref = [var_x_ref, var_y_ref]
    var_index_ref = read_header_tecplot(config['filename_reference'], config['headerline_reference'], config['headername_reference'], var_list_ref)
    data_ref = np.loadtxt( config['filename_reference'],
                           comments=config['comments_reference'],
                           delimiter=config['delimiter_reference'],
                           skiprows=config['num_skiprows_reference'] )
    # Store data as dictionary
    reference_dict = {}
    for m in range( 0,len(var_list_ref) ):
      reference_dict[ var_list_ref[m] ] = data_ref[:,var_index_ref[m]]
    # Make plot
    ax.plot( reference_dict[var_x_ref], 
             reference_dict[var_y_ref], 
             color=config['color_map_reference'], 
             label=config['label_reference'])

  # Optimal data
  filename_tmp = config['work_dir'] + '/' + config['filename_result']
  print('--Reading output file...:',filename_tmp)
  try:
    data_input = np.genfromtxt(filename_tmp,comments=comments_tmp,delimiter=delimiter_tmp,skiprows=num_skiprows_tmp)
  except:
    data_input = np.genfromtxt(filename_tmp, comments=comments_tmp, delimiter=delimiter_tmp, skip_header=num_skiprows_tmp)
  var_index = read_header_tecplot(filename_tmp, headerline_variables, headername_tmp, var_list)
  # Store data as dictionary
  result_dict = {}
  for m in range( 0,len(var_list) ):
    result_dict[ var_list[m] ] = data_input[:,var_index[m]]
  # Make plot
  ax.plot( result_dict[var_x],
           result_dict[var_y],
           color=config['color_map'], 
           label=config['legend_label'])

  # Additional data
  if flag_add :
    ax_add= ax.twinx()
    ax_add.set_ylim( config['axis_y_limit_add'][0], config['axis_y_limit_add'][1] )
    ax_add.set_ylabel( config['axis_y_label_add' ])
    ax_add.plot( result_dict[var_x],
                 result_dict[var_y_add],
                 color=config['color_map_add'], 
                 label=config['legend_label_add'])

  # 凡例の表示
  if flag_add :
    # 追加の軸の凡例を元の軸の凡例に結合
    lines, labels = ax.get_legend_handles_labels()
    lines_add, labels_add = ax_add.get_legend_handles_labels()
    ax.legend(lines + lines_add, labels + labels_add, loc=config['legend_location'])
  else:
    ax.legend(loc=config['legend_location'])

  # グリッドの表示
  ax.grid(True)

  # Writing
  plt.savefig(config['filename_output_image'], dpi=config['dpi_image'])

  plt.close()


if __name__ == '__main__':

  main()