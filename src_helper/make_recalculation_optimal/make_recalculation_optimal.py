#!/usr/bin/env python3

# Script to copy directory of optimal file and modify control file for recalculation

import os
import sys
import glob
import shutil

# Add ath of parent directory to Python path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
  sys.path.insert(0, parent_dir)  
from general import general

def detect_directories(directory_input):
  # ディレクトリAの下にある全てのディレクトリを取得
  directories = glob.glob(os.path.join(directory_input, '*/'))
  return directories

def copy_directory(source_dir, dest_dir):
  # 既存のディレクトリが存在する場合は削除
  if os.path.exists(dest_dir):
    shutil.rmtree(dest_dir)
  # ディレクトリをコピー
  shutil.copytree(source_dir, dest_dir)
  return

def replace_flags_in_file(file_path, config):
  # ファイルを読み込む
  with open(file_path, 'r') as file:
    lines = file.readlines()
    
  # フラグの置き換え
  replaced_text = config['replaced_text']
 
  # 置換マッピングを作成
  replace_map = {item['text'][0]: item['text'][1] for item in replaced_text}

  # フラグの置き換え
  with open(file_path, 'w') as file:
    for line in lines:
      for old_text, new_text in replace_map.items():
        if old_text in line:
          line = line.replace(old_text, new_text)
      file.write(line)
 
  return

def main():

  # Read parameters
  file_control = 'make_recalculation_optimal.yml'
  config = general.read_config_yaml(file_control)

  work_directory = config['directory']
  filename = config['filename_replaced']

  # 対象ディレクトリを検出
  directories_copy = detect_directories(work_directory)
  print('Found directory:',directories_copy)
    
  # 各ディレクトリについて処理を行う
  for dir_tmp in directories_copy:
    dir_tmp_name = os.path.basename(os.path.normpath(dir_tmp))
    dir_compied = os.path.join(work_directory, f"{dir_tmp_name}_recal")
        
    # ディレクトリBをコピーしてディレクトリDを作成
    copy_directory(dir_tmp, dir_compied)
    print(f"Copied {dir_tmp} to {dir_compied}")
        
    # コピーされたディレクトリD内のファイルCを修正
    file_path = os.path.join(dir_compied, filename)
    if os.path.exists(file_path):
      replace_flags_in_file(file_path, config)
      print(f"Modified file: {file_path}")
    else:
      print(f"File {filename} not found in {dir_compied}")

  return


if __name__ == '__main__':

  main()
