import os

def check_path_type(path):
    if os.path.isdir(path):
        return 0 # folder
    elif os.path.isfile(path):
        return 1 # file
    else:
        return -1 # else

def get_parent_path(folder_path):
    parent_path = os.path.dirname(folder_path)
    return parent_path