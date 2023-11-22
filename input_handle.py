import os
import socket
import time
from typing import Dict, Callable, List, Tuple, Generator, Any

import users
import utility
from users import User


def _cmd_get_current_folder(user: User, data=None, ) -> bytes:
    '''
    Send command 'where' for getting your current path
    '''
    return f'[i] you are now in {user.current_path}'.encode()


def _cmd_open_file(user: User, data: List[str]) -> Tuple[Generator, int]:
    '''
    open - open file.
           you can use absolute path (e.g. open D:\\folder\\file or open /home/folder/file)
           or relative path (e.g. open folder). In case of relative path will be opened
           from your current directory.

    '''

    if len(data) == 0:
        return f'[!] empty file path'.encode()
    else:
        file = utility.define_abs_path(data[0], user.current_path)
        if os.path.isfile(file):
            file_size = os.stat(file)
            return utility.gen_chunk_read(file), file_size.st_size
        else:
            return f'[!] no such file'.encode()


def _cmd_get_list_of_files(user: User, data: List[str] = None) -> bytes:
    '''
    list - shows directories and files in directory.
           You can use absolute path (e.g. list D:\\folder or list /home/folder)
           or relative path (e.g list folder). In case of relative path
           you will get objects in your current directory.

    '''

    if data:
        try:
            res = utility.walk_around_folder(data[0])
        except:
            return f'[!] unreachable path {data[0]}'.encode()
    else:
        res = utility.walk_around_folder(user.current_path)
    return res.encode()


def _cmd_create_folder(data: List[str], user: User) -> bytes:
    '''
    crfo
    :param data:
    :return:
    '''

    if data:
        path = utility.define_abs_path(data[0], user.current_path)
        if not os.path.exists(path):
            try:
                os.mkdir(path)
            except Exception as E:
                return f'[e] something went wrong {E}'.encode()
            res = f'[i] successfully created folder "{path}"'
        else:
            res = f'[!] path "{path}" is already exists'
    else:
        res = f'[!] empty path'
    return res.encode()


def _cmd_delete_folder(user: User, data: List[str]) -> bytes:
    '''
    defo
    :param data:
    :return:
    '''

    if data:
        path = utility.define_abs_path(data[0], user.current_path)
        try:
            os.rmdir(path)
        except Exception as E:
            return f'[e] something went wrong {E}'.encode()
        res = f'[i] successfully deleted folder "{path}"'
    else:
        res = f'[!] empty path'
    return res.encode()


def _cmd_delete_file(user: User, data: List[str]) -> bytes:
    '''
    defo
    :param data:
    :return:
    '''

    if data:
        path = utility.define_abs_path(data[0], user.current_path)
        try:
            os.remove(path)
        except Exception as E:
            return f'[e] something went wrong {E}'.encode()
        res = f'[i] successfully deleted file "{path}"'
    else:
        res = f'[!] empty path to file'
    return res.encode()


def _cmd_save_file(data: List[str]) -> bytes:
    pass


def _cmd_get_help(data: List[str], user: User) -> bytes:
    '''
    just write 'help'
    '''

    short_help = 'Avaliable commands:\n'
    for command, note in commands.items():
        short_help += f'{command}{note["note"]}\n'

    if data:
        command = data[0]
        if (command in commands) and (commands[command].__doc__ is not None):
            res = commands[command]['cmd'].__doc__
        else:
            res = 'no help for you'
        return res.encode()
    else:
        return short_help.encode() or '[!] No help for you'


def _cmd_change_folder(user: User, data: List[str]) -> bytes:
    '''
    jump - change your current folder (e.g jump 'D:\folder or jump /home/folder)
           or jump folder
    '''
    if len(data) == 0:
        res = f'[!] got empty path to folder'
    else:
        path = utility.define_abs_path(data[0], user.current_path)
        if os.path.exists(path) and os.path.isdir(path):
            user.current_path = path
            res = f'[i] path changed to {path}'
        else:
            res = f'[!] no such folder {path}'
    return res.encode()


def _cmd_get_info(data: List[str], user: User = None) -> bytes:
    '''
    info - get information about folder (e.g info 'D:\folder or info /home/folder)
           or about file (e.g. info 'D:\folder\file or info /home/file)
    '''
    if len(data) == 0:
        res = f'[!] empty filepath'
    else:
        file_path = utility.define_abs_path(data[0], user.current_path)
        try:
            stat = os.stat(file_path)
            res = (f'{file_path} info:\n\t'
                   f'Size: {stat.st_size} bytes\n\t'
                   f'Permissions:{oct(stat.st_mode)}\n\t'
                   f'Owner:{stat.st_uid}\n\t'
                   f'Created: {time.ctime(stat.st_ctime)}\n\t'
                   f'Last modified: {time.ctime(stat.st_mtime)}\n\t'
                   f'Last accessed: {time.ctime(stat.st_atime)}'
                   )
        except Exception as e:
            res = f'[Err] something went wrong {e}'
    return res.encode()


commands: Dict[str, Dict[str, Callable]] = \
    {'where': {'cmd': _cmd_get_current_folder,
               'note': ' - show your current path'},
     'list': {'cmd': _cmd_get_list_of_files,
              'note': ' - show list of objects'},
     'open': {'cmd': _cmd_open_file,
              'note': ' - perform file opening'},
     'nefo': {'cmd': _cmd_create_folder,
              'note': ' - create new folder'},
     'defo': {'cmd': _cmd_delete_folder,
              'note': ' - delete folder'},
     'defi': {'cmd': _cmd_delete_file,
              'note': ' - delete file'},
     'safi': {'cmd': _cmd_save_file,
              'note': ' - save file'},
     'info': {'cmd': _cmd_get_info,
              'note': ' - show information about object'},
     'jump': {'cmd': _cmd_change_folder,
              'note': ' - change path'},
     'help': {'cmd': _cmd_get_help,
              'note': ' - this list'}
     }


class InputsHandler:

    @staticmethod
    def close_connection(sock: socket.socket):
        sock.close()

    @staticmethod
    def handle_input(user: users.User, data: bytes) -> bytes:
        input_data = data.decode("utf-8").split()
        command, *data = input_data
        if command in commands:
            return commands[command]['cmd'](user=user, data=data)
        return f'[!] no such command {command}'.encode()

