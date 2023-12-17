import os
from pathlib import Path
from typing import Generator, List, Tuple


def walk_around_folder(abs_path: str, as_str: bool = True) -> str | Tuple:
    '''
    abs_path: absolute path to file
    return: list of objects as string
    '''
    path, folders, files = next(os.walk(abs_path))
    obj_list = ('folder> .. ' + '\nfolder> .. '.join(folders)) if len(folders) != 0 else '...'
    obj_list += ('\n>       .. ' + '\n>       .. '.join(files)) if len(files) != 0 else '\n...'
    return f'[>] {abs_path} \n{obj_list}' if as_str else (path, folders, files)


def gen_chunk_read(file_path: str, chunk_size: int = 4096) -> Generator:
    '''
    path_to_file: asbsolute path to file
    chunk_size: size of chunk
    '''
    with open(file_path, 'rb') as f:
        while True:
            data = f.read(chunk_size)
            yield data
            if not data:
                break


def define_path(path_or_folder: str, user_path: str) -> str:
    '''
    define is path_to_folder absolute path or folder in current user directory
    '''
    if Path(path_or_folder).is_absolute():
        path = path_or_folder
    else:
        path = Path().joinpath(user_path, path_or_folder)
    return path


def is_allowed(path: Path, restricted_path: List[str]) -> bool:
    '''
    check user restrictions
    '''
    target_path = path
    for path in restricted_path:
        if target_path.is_relative_to(Path(path)):
            return False
    return True
