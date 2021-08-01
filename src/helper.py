import os
from os import path

metadata_defaults = {'Instantiability': ['Concrete'], 'Status': ['Stable']}
property_defaults = {'minCount': ['0'], 'maxCount': ['*']}


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

def union_dict(d1, d2):
    '''
    Concat two dict d1, d2. (inplace). Values in dict d1 will be given priority over dict d2.
    '''
    for k,v in d2.items():
        if not k in d1:
            d1[k] = v