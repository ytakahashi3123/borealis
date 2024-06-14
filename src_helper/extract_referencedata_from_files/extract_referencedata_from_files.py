#!/usr/bin/env python3

# Script to extract reference data from output files

import numpy as np
import sys
import os
from scipy.interpolate import interp1d

# Add ath of parent directory to Python path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
  sys.path.insert(0, parent_dir)  
from general import general


def get_index_optimal(filename):

  # Extracting reading files
  data_extract = np.genfromtxt( filename, 
                                dtype=int, 
                                comments='#',
                                delimiter=',', 
                                skip_header=1 )
  index_local_to_global = data_extract[:,1]
  index_last = index_local_to_global[-1]

  return index_last


def main():

  # Read parameters
  file_control = 'extract_referencedata_from_files.yml'
  config = general.read_config_yaml(file_control)

  # Initial settings
  headername_tmp = config['headername']
  headerline_variables = config['headerline']
  num_skiprows_tmp = config['num_skiprows']
  comments_tmp  = config['comments']
  delimiter_tmp = config['delimiter']

  # Define data variables
  var_x = config['variable_x']
  var_y = config['variable_y']
  var_list = [var_x, var_y]

  # File reading
  dirname_input = config['directory_input']
  num_dataset = len(dirname_input)
  x_ref = np.zeros(num_dataset).reshape(num_dataset)
  y_ref = np.zeros(num_dataset).reshape(num_dataset)
  for n in range(0, num_dataset):
    if config['flag_filereading_extracted']:
      filename_extract = dirname_input[n] + '/' + config['filename_extract_list']
      index_last = get_index_optimal( filename_extract )
    else:
      index_last = config['step_end']
    index_last = index_last + 1

    filename_tmp = dirname_input[n] + '/' + config['work_dir'] + '/' + config['case_dir'] + str(index_last).zfill(config['step_digit']) + '/'  + config['filename_result']
    print('Reading reference file...:',filename_tmp)
    try:
      data_input = np.genfromtxt(filename_tmp,comments=comments_tmp,delimiter=delimiter_tmp,skiprows=num_skiprows_tmp)
    except:
      data_input = np.genfromtxt(filename_tmp, comments=comments_tmp, delimiter=delimiter_tmp, skip_header=num_skiprows_tmp)
    var_index = general.read_header_tecplot(filename_tmp, headerline_variables, headername_tmp, var_list)
    # Store data as dictionary
    result_dict = {}
    for m in range( 0,len(var_list) ):
      result_dict[ var_list[m] ] = data_input[:,var_index[m]]
  
    x_extracted_offset = config['x_extracted'] + config['x_offset'] 
    x = result_dict[var_x]
    y = result_dict[var_y]
    interp_func = interp1d(x, y, kind='linear')
    y_extracted = interp_func(x_extracted_offset)

    x_ref[n] = x_extracted_offset
    y_ref[n] = y_extracted/config['value_normalization']

  # Display
  print('X value: ',x_ref[0])
  print('Y values:',np.array2string(y_ref, separator=', ', max_line_width=np.inf))

  # File Output
  filename_tmp = config['filename_output']
  print('Writing data:',filename_tmp)
  file_output = open( filename_tmp , 'w')
  header_tmp = "Variables = " + config['result_x_name'] + ', '
  for n in range(0, num_dataset):
    header_tmp = header_tmp + config['result_y_name'][n] + ', '
  header_tmp = header_tmp.rstrip(', ') + '\n'
  file_output.write( header_tmp )
  text_tmp = str( x_ref[0] ) + ', '
  for n in range(0, num_dataset):
    text_tmp = text_tmp  + str( y_ref[n] ) + ', '
  text_tmp = text_tmp.rstrip(', ')  + '\n'
  file_output.write( text_tmp )
  file_output.close()

  return


if __name__ == '__main__':

  main()