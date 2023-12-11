import stat
import time
from pathlib import Path
from typing import Callable, Generator, NamedTuple, Tuple

import utility
from users import User, SuperUser


class Packet(NamedTuple):
    '''
    packet of data from user without command
    cmd_tail - string without command word
    data_length - amount of data we need to save (in case of receiving file)
    '''
    user: User | SuperUser
    cmd_tail: Tuple[str]
    data_length: int


class UserCommands:

    @staticmethod
    def where(packet: Packet) -> bytes:
        '''
        Send command 'where' for getting your current path
        '''
        return f'[>] you are now in {packet.user.current_path}'.encode()

    @staticmethod
    def open(packet: Packet) -> Tuple[Generator, int] | bytes:
        '''
        open - open file.
               you can use absolute path (e.g. open D:\\folder\\file or open /home/folder/file)
               or relative path (e.g. open folder). In case of relative path will be opened
               from your current directory.

        '''

        if not packet.cmd_tail:
            return f'[!] empty file path'.encode()
        else:
            path = Path(utility.define_path(packet.cmd_tail[0], packet.user.current_path))
            if Path(path).is_file():
                if not utility.is_allowed(path, packet.user.restrictions['r']):
                    return f'[!] you have no permission to {path}'.encode()
                file_size = Path(path).stat()
                return utility.gen_chunk_read(path.__str__()), file_size.st_size
            else:
                return f'[!] no such file'.encode()

    @staticmethod
    def list(packet: Packet) -> bytes:
        '''
        list - shows directories and files in directory.
               You can use absolute path (e.g. list D:\\folder or list /home/folder)
               or relative path (e.g. list folder). In case of relative path
               you will get objects in your current directory.

        '''
        if packet.cmd_tail:
            path = Path(utility.define_path(packet.cmd_tail[0], packet.user.current_path))
            if not utility.is_allowed(path, packet.user.restrictions['x']):
                return f'[!] you have no permission to {path}'.encode()
            try:
                res = utility.walk_around_folder(path.__str__())
            except:
                return f'[!] unreachable path {path}'.encode()
        else:
            path = Path(packet.user.current_path)
            if not utility.is_allowed(path, packet.user.restrictions['x']):
                return f'[!] you have no permission to {path}'.encode()
            res = utility.walk_around_folder(path.__str__())
        return res.encode()

    @staticmethod
    def nefo(packet: Packet) -> bytes:
        '''
        nefo - create folder in current path in case of packet.cmd_tail == 0 (e.g. nefo newfolder)
                or in path from packet (e.g. 'nefo D:\\newfolder')
        '''

        if packet.cmd_tail:
            path = Path(utility.define_path(packet.cmd_tail[0], packet.user.current_path))
            if not utility.is_allowed(path, packet.user.restrictions['x']):
                return f'[!] you have no permission to {path}'.encode()
            if not Path(path).exists():
                try:
                    Path(path).mkdir()
                except Exception as E:
                    return f'[err] something went wrong {E}'.encode()
                res = f'[>] successfully created folder "{path}"'
            else:
                res = f'[!] path "{path}" is already exists'
        else:
            res = f'[!] empty path'
        return res.encode()

    @staticmethod
    def defo(packet: Packet) -> bytes:
        '''
        defo - delete folder by absolute path or in current folder.
               You can use absolute path (e.g. defo D:\\folder or defo /home/folder)
               or relative path (e.g. defo folder)
        '''

        if packet.cmd_tail:
            path = Path(utility.define_path(packet.cmd_tail[0], packet.user.current_path))
            if not utility.is_allowed(path, packet.user.restrictions['x']):
                return f'[!] you have no permission to {path}'.encode()
            try:
                Path(path).rmdir()
            except Exception as E:
                return f'[err] something went wrong {E}'.encode()
            res = f'[>] successfully deleted folder "{path}"'
        else:
            res = f'[!] empty path'
        return res.encode()

    @staticmethod
    def defi(packet: Packet) -> bytes:
        '''
        defi - delete by absolute path or in current folder.
               Use absolute path (e.g. defi D:\\file or defi /home/file)
               or relative path (e.g. defi file)
        '''

        if packet.cmd_tail:
            path = Path(utility.define_path(packet.cmd_tail[0], packet.user.current_path))
            if not utility.is_allowed(path, packet.user.restrictions['x']):
                return f'[!] you have no permission to {path}'.encode()
            try:
                Path(path).unlink()
            except Exception as E:
                return f'[err] something went wrong {E}'.encode()
            res = f'[>] successfully deleted file "{path}"'
        else:
            res = f'[!] empty path to file'
        return res.encode()

    @staticmethod
    def send(packet: Packet, check_fragmentation: bool) -> Tuple[int, Callable] | bytes:
        '''
        to do: save from path with spaces!!!
        '''

        cursor_position = 0
        mode = 'wb'

        _from, *_to = packet.cmd_tail
        if len(_to) == 0:
            path_to_save = Path().joinpath(packet.user.home_path, Path(_from).name)
            print('i am here')
        elif _to[0] == 'here':
            path_to_save = Path().joinpath(packet.user.current_path, Path(_from).name)
        else:
            path_to_save = Path().joinpath(_to[0], Path(_from).name)

        if not path_to_save.parent.exists():
            return f'[>] no such path "{path_to_save.parent}"'.encode()

        if not utility.is_allowed(path_to_save, packet.user.restrictions['w']):
            return f'[!] you have no permission to {path_to_save}'.encode()

        if check_fragmentation:
            fragmented_path = Path(path_to_save.__str__() + '.part')
            if fragmented_path.exists():
                cursor_position = fragmented_path.stat().st_size
                path_to_save = fragmented_path
                mode = 'ab'


        def saver(packet: Packet):
            nonlocal path_to_save
            nonlocal mode

            with open(path_to_save, mode) as f:
                already_read = 0
                while already_read < packet.data_length:
                    to_read = packet.data_length - already_read
                    try:
                        data = packet.user.sock.recv(4096 if to_read > 4096 else to_read)
                        f.write(data)
                        already_read += len(data)
                    except:
                        f.close()
                        path_to_save.rename(path_to_save.__str__() + '.part')
                        break
            if mode == 'ab':
                path_to_save.rename(path_to_save.__str__()[:-5])

            return f'[>] file was successfully saved to "{path_to_save.__str__()}" '.encode()
        return cursor_position, saver





    @staticmethod
    def jump(packet: Packet) -> bytes:
        '''
        jump - change your current folder (e.g. jump D:\\folder or jump /home/folder)
               or jump folder.
               single 'jump' moves you to one folder up
               'jump -home' moves you to your home directory
        '''
        if not packet.cmd_tail:
            path = Path(packet.user.current_path).parent
        else:
            if packet.cmd_tail[0].startswith('-home'):
                path = Path(packet.user.home_path)
            else:
                path = Path(utility.define_path(packet.cmd_tail[0], packet.user.current_path))

        if Path(path).exists() and Path(path).is_dir():
            if not utility.is_allowed(path, packet.user.restrictions['x']):
                return f'[!] you have no permission to {path}'.encode()

            packet.user.current_path = path.__str__()
            res = f'[>] path changed to {path.__str__()}'
        else:
            res = f'[!] no such folder {path.__str__()}'
        return res.encode()

    @staticmethod
    def info(packet: Packet, ) -> bytes:
        '''
        info - get information about folder (e.g info 'D:\\folder or info /home/folder)
               or about file (e.g. info 'D:\\folder\\file or info /home/file)
        '''
        if not packet.cmd_tail:
            res = f'[!] empty filepath'
        else:
            path = Path(utility.define_path(packet.cmd_tail[0], packet.user.current_path))
            if not utility.is_allowed(path, packet.user.restrictions['x']):
                return f'[!] you have no permission to {path}'.encode()
            try:
                status = Path(path).stat()
                res = (f'[>] {path} info:\n\t'
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
    def whoami(packet: Packet) -> bytes:
        return packet.user.get_full_info().encode()
