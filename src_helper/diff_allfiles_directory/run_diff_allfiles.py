import os
import filecmp
import difflib

def get_all_files(directory):
    """
    Given a directory, return a list of all file paths within that directory.
    """
    file_list = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_list.append(os.path.relpath(os.path.join(root, file), directory))
    return file_list

def compare_files(file1, file2):
    """
    Given two file paths, print their differences line by line.
    """
    with open(file1, 'r') as f1, open(file2, 'r') as f2:
        f1_lines = f1.readlines()
        f2_lines = f2.readlines()
        diff = difflib.unified_diff(f1_lines, f2_lines, fromfile=file1, tofile=file2)
        for line in diff:
            print(line, end='')

def diff_directories(dir_a, dir_b):
    """
    Compare all files in dir_a and dir_b and print differences.
    """
    files_a = set(get_all_files(dir_a))
    files_b = set(get_all_files(dir_b))
    
    all_files = files_a.union(files_b)
    
    for file in all_files:
        file_a = os.path.join(dir_a, file)
        file_b = os.path.join(dir_b, file)
        
        if file in files_a and file in files_b:
            if not filecmp.cmp(file_a, file_b, shallow=False):
                print(f"Differences in file: {file}")
                compare_files(file_a, file_b)
        elif file in files_a:
            print(f"File {file} exists in {dir_a} but not in {dir_b}")
        else:
            print(f"File {file} exists in {dir_b} but not in {dir_a}")

if __name__ == "__main__":
    dir_a = "testcase/dira"
    dir_b = "testcase/dirb"
    
    diff_directories(dir_a, dir_b)
