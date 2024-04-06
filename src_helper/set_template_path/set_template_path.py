#!/usr/bin/env python3

import yaml as yaml
import re as re


def read_config_yaml(file_control):
  print("Reading control file...:", file_control)
  with open(file_control) as file:
    config = yaml.safe_load(file)
  return config

def modify_shell_script(script_path, variable_name, new_value):
    # Open the shell script for reading
    with open(script_path, 'r') as file:
      script_content = file.read()
    # Use regular expression to find and replace the EXCODE_HOME value
    modified_content = re.sub(r'(EXCODE_HOME=)(.*)', r'\1' + new_value + '', script_content)
    modified_content = re.sub(r'({}=)(.*)'.format(re.escape(variable_name)), r'\1' + new_value + '', script_content)
    # Write the modified content back to the shell script
    with open(script_path, 'w') as file:
      file.write(modified_content)

def main():
  # Read parameters
  file_control = 'set_template_path.yml'
  config = read_config_yaml(file_control)

  # Change shell script
  case_template = config['template']
  for n in range(0, len(case_template)):
    dict_case     = case_template[n]
    script_path   = dict_case['file']
    print('Changing file:', script_path)
    variable_name = dict_case['name']
    new_path      = dict_case['path']
    modify_shell_script(script_path, variable_name, new_path)

  return


if __name__ == '__main__':

  main()