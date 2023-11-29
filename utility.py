import os
from typing import Generator


PATH_DIV = os.sep



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
    obj_list = ('folder> .. ' + '\nfolder> .. '.join(folders)) if len(folders) != 0 else '...'
    obj_list += ('\n>       .. ' + '\n>       .. '.join(files)) if len(files) != 0 else '\n...'
    return f'[>] {abs_path} \n{obj_list}'


def gen_chunk_read(file_path: str, chunk_size: int = 2048) -> Generator:
    '''
    path_to_file: asbsolute path to file
    chunk_size: size of chunk
    '''
    with open(file_path, 'rb') as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            yield data


def define_abs_path(path_or_folder: str, user_path: str) -> str:
    '''
    define is path_to_folder absolute path or folder in current user directory
    '''
    if is_path(path_or_folder):
        path = path_or_folder
    else:
        path = user_path + PATH_DIV + path_or_folder
    return path


def extract_file_name(file_path: str) -> str:
    '''
    extract file name from path to file

    '''
    return file_path.split(PATH_DIV)[-1]


def jump_up(path: str) -> str:
    splitted_path = path.split(PATH_DIV)
    new_path = PATH_DIV.join(splitted_path[:-1])

    return new_path if new_path[-1] != ':' else new_path + PATH_DIV
