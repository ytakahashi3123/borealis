#!/usr/bin/env python3

import yaml
import sys
import os

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


def make_directory(dir_path):
  if not os.path.exists(dir_path):
    os.mkdir(dir_path)
  return


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