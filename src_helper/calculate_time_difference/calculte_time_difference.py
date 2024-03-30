# 

# Program to calculate time difference
# Author: Yusuke Takahashi, Hokkaido University
# Contact: ytakahashi@eng.hokudai.ac.jp

import os
from datetime import datetime

# ディレクトリのパスを指定
directory_path = "./"

# "timestamp_start_" or "timestamp_end_"で始まるファイルを検索
file_list=["timestamp_start_", "timestamp_end_"]

data_str_list = []
for i in range(0,len(file_list)):
  for filename in os.listdir(directory_path):
    prefix = file_list[i]
    if filename.startswith(prefix):
        file_path = os.path.join(directory_path, filename)

  # 日時文字列を抽出
  prefix_deleted = directory_path+prefix
  if file_path.startswith(prefix_deleted):
    extracted_string = file_path[len(prefix_deleted):]
    data_str_list.append(extracted_string)
  else:
    print('There is no file:',file_list[i])
    print('Program stopped.')
    exit()

# 2つの日時文字列を指定
date_str1 = data_str_list[0]
date_str2 = data_str_list[1]

# 日時文字列を日付オブジェクトに変換
date_format = "%Y%m%d-%H%M%S"
date1 = datetime.strptime(date_str1, date_format)
date2 = datetime.strptime(date_str2, date_format)

# 時間差を計算し、秒に変換
time_difference = (date2 - date1).total_seconds()

print(f"時間差（秒）: {time_difference} 秒")
