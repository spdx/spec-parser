import os


def safe_open(path, *args):
    ''' Open "path" after creating any parent directories as needed.
    '''
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return open(path, *args)
