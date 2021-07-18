import os
from os import path


def safe_open(fname, *args):
    ''' Open "fname" after creating neccessary nested directories as needed.
    '''

    dname = os.path.dirname(fname) if os.path.dirname(fname) != '' else './'
    os.makedirs(dname, exist_ok=True)
    return open(fname, *args)


def safe_listdir(dname):
    if path.exists(dname) and path.isdir(dname):
        return os.listdir(dname)
    return []
