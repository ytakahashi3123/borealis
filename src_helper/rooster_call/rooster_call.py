import time
import os
import subprocess

watch_file = "job_requests"
root_dir = os.getcwd()

while True:
  if os.path.exists(watch_file):
    directories = []
    with open(watch_file, 'r') as f:
      lines = f.readlines()

    for line in lines[1:]:
      line = line.strip()
      if line:
        directories.append(line)
        print(line)

    procs = []
    for dir_path in directories:
      os.chdir(dir_path)
      print(f'[Borealis-watchdog] Run subprocess in {dir_path}')
      # subprocess.call("./run_SU2-OPT_pps.sh")
      #proc = subprocess.Popen(["./run_SU2-OPT_pps.sh"])
      proc = subprocess.Popen(["./run_SU2-OPT_pps.sh"],preexec_fn=os.setpgrp)
      procs.append(proc)
      os.chdir(root_dir)

    print('All launched PIDs:')
    for proc in procs:
      print(f'  PID: {proc.pid}')

    os.remove(watch_file)
    print("[Borealis-watchdog] Job complete. Exiting.")
    break

  time.sleep(1)
