import os
import stat
import time
from typing import Tuple, Generator, NamedTuple
from pathlib import Path
import utility
from users import User


class Packet(NamedTuple):
    '''
    packet of data from user without command
    cmd_tail - string without command word
    data_length - amount of data we need to save (in case of receiving file)
    '''
    cmd_tail: Tuple[str]
    data_length: int


class UserCommands:

    @staticmethod
    def cmd_get_current_folder(user: User, packet: Packet = None) -> bytes:
        '''
        Send command 'where' for getting your current path
        '''
        return f'[>] you are now in {user.current_path}'.encode()

    @staticmethod
    def cmd_open_file(user: User, packet: Packet) -> Tuple[Generator, int] | bytes:
        '''
        open - open file.
               you can use absolute path (e.g. open D:\\folder\\file or open /home/folder/file)
               or relative path (e.g. open folder). In case of relative path will be opened
               from your current directory.

        '''

        if not packet.cmd_tail:
            return f'[!] empty file path'.encode()
        else:
            file = utility.define_abs_path(packet.cmd_tail[0], user.current_path)
            if os.path.isfile(file):
                file_size = os.stat(file)
                return utility.gen_chunk_read(file), file_size.st_size
            else:
                return f'[!] no such file'.encode()

    @staticmethod
    def cmd_get_list_of_files(user: User, packet: Packet = None) -> bytes:
        '''
        list - shows directories and files in directory.
               You can use absolute path (e.g. list D:\\folder or list /home/folder)
               or relative path (e.g. list folder). In case of relative path
               you will get objects in your current directory.

        '''

        if packet.cmd_tail:
            try:
                res = utility.walk_around_folder(packet.cmd_tail[0])
            except:
                return f'[!] unreachable path {packet.cmd_tail[0]}'.encode()
        else:
            res = utility.walk_around_folder(user.current_path)
        return res.encode()

    @staticmethod
    def cmd_create_folder(user: User, packet: Packet) -> bytes:
        '''
        nefo - create folder in current path in case of packet.cmd_tail == 0 (e.g. got 'nefo newfolder')
                or in path from packet (e.g. got 'nefo D:\\newfolder')
        '''

        if packet.cmd_tail:
            path = utility.define_abs_path(packet.cmd_tail[0], user.current_path)
            if not os.path.exists(path):
                try:
                    os.mkdir(path)
                except Exception as E:
                    return f'[err] something went wrong {E}'.encode()
                res = f'[>] successfully created folder "{path}"'
            else:
                res = f'[!] path "{path}" is already exists'
        else:
            res = f'[!] empty path'
        return res.encode()

    @staticmethod
    def cmd_delete_folder(user: User, packet: Packet) -> bytes:
        '''
        defo - delete folder by absolute path or in current folder.
               You can use absolute path (e.g. defo D:\\folder or defo /home/folder)
               or relative path (e.g. defo folder)
        '''

        if packet.cmd_tail:
            path = utility.define_abs_path(packet.cmd_tail[0], user.current_path)
            try:
                os.rmdir(path)
            except Exception as E:
                return f'[err] something went wrong {E}'.encode()
            res = f'[>] successfully deleted folder "{path}"'
        else:
            res = f'[!] empty path'
        return res.encode()

    @staticmethod
    def cmd_delete_file(user: User, packet: Packet) -> bytes:
        '''
        defi - delete by absolute path or in current folder.
               Use absolute path (e.g. defi D:\\file or defi /home/file)
               or relative path (e.g. defi file)

        '''

        print(packet.cmd_tail)
        if packet.cmd_tail:
            path = utility.define_abs_path(packet.cmd_tail[0], user.current_path)
            try:
                os.remove(path)
            except Exception as E:
                return f'[err] something went wrong {E}'.encode()
            res = f'[>] successfully deleted file "{path}"'
        else:
            res = f'[!] empty path to file'
        return res.encode()

    @staticmethod
    def cmd_save_file(user: User, packet: Packet) -> bytes:
        '''
        to do: save from path with spaces!!!

        '''
        _from, *_to = packet.cmd_tail

        if _to == 'here':
            path_to_save = user.current_path + utility.PATH_DIV + utility.extract_file_name(_from)
        elif len(_to) == 0:
            path_to_save = user.home_path + utility.PATH_DIV + utility.extract_file_name(_from)
        else:
            path_to_save = _to + utility.PATH_DIV + utility.extract_file_name(_from)

        with open(path_to_save, 'wb') as f:
            already_read = 0
            while already_read < packet.data_length:
                to_read = packet.data_length - already_read
                data = user.sock.recv(4096 if to_read > 4096 else to_read)
                f.write(data)
                already_read += len(data)

        return f'[>] file was successfully saved to "{path_to_save}" '.encode()

    @staticmethod
    def cmd_change_folder(user: User, packet: Packet) -> bytes:
        '''
        jump - change your current folder (e.g. jump D:\\folder or jump /home/folder)
               or jump folder.
               single 'jump' moves you to one folder up
               'jump home' moves you to your home directory
        '''
        if not packet.cmd_tail:
            path = utility.jump_up(user.current_path)
        else:
            if packet.cmd_tail[0].startswith('home'):
                path = user.home_path
            else:
                path = utility.define_abs_path(packet.cmd_tail[0], user.current_path)

        if os.path.exists(path) and os.path.isdir(path):
            user.current_path = path
            res = f'[>] path changed to {path}'
        else:
            res = f'[!] no such folder {path}'
        return res.encode()

    @staticmethod
    def cmd_get_info(user: User, packet: Packet, ) -> bytes:
        '''
        info - get information about folder (e.g info 'D:\\folder or info /home/folder)
               or about file (e.g. info 'D:\\folder\\file or info /home/file)
        '''
        if not packet.cmd_tail:
            res = f'[!] empty filepath'
        else:
            file_path = utility.define_abs_path(packet.cmd_tail[0], user.current_path)
            try:
                # status = os.stat(file_path)
                status = Path(file_path).stat()
                res = (f'{file_path} info:\n\t'
                       f'Size: {status.st_size} bytes\n\t'
                       f'Permissions:{stat.filemode(status.st_mode)}\n\t'
                       f'Owner:{status.st_uid}\n\t'
                       f'Created: {time.ctime(status.st_ctime)}\n\t'
                       f'Last modified: {time.ctime(status.st_mtime)}\n\t'
                       f'Last accessed: {time.ctime(status.st_atime)}'
                       )
            except Exception as e:
                res = f'[err] something went wrong {e}'

        return res.encode()

    @staticmethod
    def cmd_who(user: User, packet: Packet = None) -> bytes:
        return user.get_full_info().encode()

