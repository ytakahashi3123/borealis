#!/usr/bin/env python3

# Script for making animation of optimal solution history

import numpy as np
import sys
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Add ath of parent directory to Python path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
  sys.path.insert(0, parent_dir)  
from general import general


def main():

  # Read parameters
  file_control = 'make_history.yml'
  config = general.read_config_yaml(file_control)

  #file_control_borealis = 'borealis.yml'
  #config_bor =  read_config_yaml(file_control_borealis)

  # Initial settings
  work_dir = config['work_dir']
  case_dir = config['case_dir']
  filename_result = config['filename_result']

  step_start = config['step_start']
  step_end   = config['step_end']
  step_digit = config['step_digit']

  # Data variables
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
  #fig, ax = plt.subplots()
  fig = plt.figure()
  ax = fig.add_subplot(1, 1, 1)
  ax.grid()

  # Read reference data if necessary
  if config['flag_read_reference'] :
    var_x_ref = config['variable_x_reference']
    var_y_ref = config['variable_y_reference']
    var_list_ref = [var_x_ref, var_y_ref]

    var_index_ref = general.read_header_tecplot(config['filename_reference'], config['headerline_reference'], config['headername_reference'], var_list_ref)

    data_ref = np.loadtxt( config['filename_reference'],
                           comments=config['comments_reference'],
                           delimiter=config['delimiter_reference'],
                           skiprows=config['num_skiprows_reference'] )

    reference_dict = {}
    for m in range( 0,len(var_list_ref) ):
      reference_dict[ var_list_ref[m] ] = data_ref[:,var_index_ref[m]]
    ax.plot(reference_dict[var_x_ref], reference_dict[var_y_ref], color=config['color_map_reference'], label=config['label_reference'])

  # Animation
  animate, = ax.plot([], [], label=config['legend_label'])
  ax.set_xlim( config['axis_x_limit'][0], config['axis_x_limit'][1] )
  ax.set_ylim( config['axis_y_limit'][0], config['axis_y_limit'][1] )
  #ax.set_aspect('equal') # グラフのアスペクト比を１：１に設定

  animate_title = ax.set_title("")
  animate.set_color( config['color_map'] )
  ax.set_xlabel( config['axis_x_label'] )
  ax.set_ylabel( config['axis_y_label'] )

  #color_map = plt.get_cmap(config['color_map'])
  interval = config['interval']

  if flag_add :
    ax_add= ax.twinx()
    animate_add, = ax_add.plot([], [], label=config['legend_label_add'])
    animate_add.set_color( config['color_map_add'] )
    ax_add.set_ylim( config['axis_y_limit_add'][0], config['axis_y_limit_add'][1] )
    ax_add.set_ylabel( config['axis_y_label_add' ])

  if flag_add :
    # 追加の軸の凡例を元の軸の凡例に結合
    handles, labels = ax.get_legend_handles_labels()
    handles_add, labels_add = ax_add.get_legend_handles_labels()
    ax.legend(handles + handles_add, labels + labels_add, loc=config['legend_location'])
  else:
    ax.legend(loc=config['legend_location'])


  # Number of frames
  num_frames = step_end

  # Extracting reading files
  flag_filereading_extracted = config['flag_filereading_extracted']
  if flag_filereading_extracted:
    data_extract = np.genfromtxt( config['filename_extract_list'], 
                                  dtype=int, 
                                  comments='#',
                                  delimiter=',', 
                                  skip_header=1 )
    index_local_to_global = data_extract[:,1]
    num_frames = len(index_local_to_global)

  # Data reading
  def read_resultfile(frame):
    if flag_filereading_extracted:
      n = index_local_to_global[frame] + 1
    else:
      n = frame+1

    work_dir_case = work_dir + '/' + case_dir + str(n).zfill(step_digit)
    filename_tmp = work_dir_case + '/' + filename_result
    print('--Reading output file...:',filename_tmp)
    try:
      data_input = np.genfromtxt(filename_tmp,comments=comments_tmp,delimiter=delimiter_tmp,skiprows=num_skiprows_tmp)
    except:
      data_input = np.genfromtxt(filename_tmp, comments=comments_tmp, delimiter=delimiter_tmp, skip_header=num_skiprows_tmp)

    var_index = general.read_header_tecplot(filename_tmp, headerline_variables, headername_tmp, var_list)
    # Store data as dictionary
    result_dict = {}
    for m in range( 0,len(var_list) ):
      result_dict[ var_list[m] ] = data_input[:,var_index[m]]

    x = result_dict[var_x]
    y = result_dict[var_y]
    #animate.set_color(color_map(n / step_end))  # フレームごとの色を設定
    animate.set_data(x,y)

    if flag_add :
      y_add = result_dict[var_y_add]
      animate_add.set_data(x, y_add)

    # Title
    animate_title.set_text( config['title_base'] + str(frame+1) )

    return

  anim = animation.FuncAnimation(fig, read_resultfile, interval=interval, frames=num_frames)

  # Output
  if config['file_output']:
    anim.save( config['filename_output_movie'] )
  else :
    plt.show()

  plt.close()


if __name__ == '__main__':

  main()