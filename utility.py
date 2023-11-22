import os
from typing import Generator


def is_path(path_or_folder: str) -> bool:
    '''
    check if path_to_folder is path. Use to avoid path like 'D:' in Windows OS when
    os.path.isdir() returns True

    '''
    symbols = ['\\', '/']
    return True if any(symbol in path_or_folder for symbol in symbols) else False


def walk_around_folder(abs_path: str) -> str:
    '''
    abs_path: absolute path to file
    return: list of objects as string
    '''
    path, folders, files = next(os.walk(abs_path))
    objList = ('.F...' + '\n.F...'.join(folders)) if len(folders) != 0 else '...'
    objList += ('\n.....' + '\n.....'.join(files)) if len(files) != 0 else '\n...'
    return f'[i] {abs_path} \n{objList}'


def gen_chunk_read(path_to_file: str, chunk_size: int = 2048) -> Generator:
    '''
    path_to_file: asbsolute path to file
    chunk_size: size of chunk
    '''

    with open(path_to_file, 'rb') as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            yield data


def define_abs_path(path_or_folder: str, user_path: str) -> str:
    '''
    define is path_to_folder absolute path or folder in current directory
    '''
    if is_path(path_or_folder):
        path = path_or_folder
    else:
        path = user_path + '\\' + path_or_folder
    return path
