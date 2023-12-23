import asyncio
import stat
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Generator, NamedTuple, Tuple

import utility
from users import User, SuperUser


@dataclass
class ERR:
    NOT_FOUND: bytes = lambda e='': f'[x] no such file or path "{e}"'.encode()
    PERMISSION_DENIED: bytes = f'[x] you have no permission'.encode()
    EMPTY_PATH: bytes = f'[x] empty path'.encode()
    OTHER: bytes = lambda e='': f'[x] something went wrong: {e}'.encode()
    UNKNOWN_COMMAND: bytes = f'[x] no such command'.encode()
    ALREADY_EXISTS: bytes = f'[x] path is already exists'.encode()


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
    async def where(packet: Packet) -> bytes:
        '''
        where - show your current path
        '''
        return f'[>] you are now in {utility.trim_path(path=packet.user.current_path,user_home_folder=packet.user.home_path)}'.encode()

    @staticmethod
    async def open(packet: Packet) -> Tuple[Generator, int] | bytes:
        '''
        open - open file.
               you can use absolute path (e.g. open D:\\folder\\file or open /home/folder/file)
               or relative path (e.g. open folder). In case of relative path will be opened
               from your current directory.

        '''

        if not packet.cmd_tail:
            return ERR.EMPTY_PATH
        else:
            path = Path(utility.define_path(packet.cmd_tail[0], packet.user.current_path))
            if Path(path).is_file():
                if not utility.is_allowed(path, packet.user.permissions['r']):
                    return ERR.PERMISSION_DENIED
                file_size = Path(path).stat()
                return utility.gen_chunk_read(path.__str__()), file_size.st_size
            else:
                return ERR.NOT_FOUND(packet.cmd_tail[0])

    @staticmethod
    async def list(packet: Packet) -> bytes:
        '''
        list - shows directories and files in directory.
               You can use absolute path (e.g. list D:\\folder or list /home/folder)
               or relative path (e.g. list folder). In case of relative path
               you will get objects in your current directory.

        '''
        if packet.cmd_tail:
            path = Path(utility.define_path(packet.cmd_tail[0], packet.user.current_path))
            trimmed_path = utility.trim_path(path=path.__str__(), user_home_folder=packet.user.home_path)
            if not utility.is_allowed(path, packet.user.permissions['x']):
                return ERR.PERMISSION_DENIED
            try:
                res = utility.walk_around_folder(path.__str__(), trimmed_path=trimmed_path)
            except:
                return ERR.NOT_FOUND(packet.cmd_tail[0])
        else:
            path = Path(packet.user.current_path)
            trimmed_path = utility.trim_path(path=path.__str__(), user_home_folder=packet.user.home_path)
            if not utility.is_allowed(path, packet.user.permissions['x']):
                return ERR.PERMISSION_DENIED
            res = utility.walk_around_folder(path.__str__(), trimmed_path=trimmed_path)
        return res.encode()

    @staticmethod
    async def nefo(packet: Packet) -> bytes:
        '''
        nefo - create folder in current path in case of packet.cmd_tail == 0 (e.g. nefo newfolder)
                or in path from packet (e.g. 'nefo D:\\newfolder')
        '''

        if packet.cmd_tail:
            path = Path(utility.define_path(packet.cmd_tail[0], packet.user.current_path))
            if not utility.is_allowed(path, packet.user.permissions['x']):
                return ERR.PERMISSION_DENIED
            if not Path(path).exists():
                try:
                    Path(path).mkdir()
                except Exception as E:
                    return ERR.OTHER(E)
                res = f'[>] successfully created folder "{utility.trim_path(path=path.__str__(),user_home_folder=packet.user.home_path)}"'.encode()
            else:
                res = ERR.ALREADY_EXISTS
        else:
            res = ERR.EMPTY_PATH
        return res

    @staticmethod
    async def defo(packet: Packet) -> bytes:
        '''
        defo - delete folder by absolute path or in current folder.
               You can use absolute path (e.g. defo D:\\folder or defo /home/folder)
               or relative path (e.g. defo folder)
        '''

        if packet.cmd_tail:
            path = Path(utility.define_path(packet.cmd_tail[0], packet.user.current_path))
            if not utility.is_allowed(path, packet.user.permissions['x']):
                return ERR.PERMISSION_DENIED
            try:
                Path(path).rmdir()
            except Exception as E:
                return ERR.OTHER(E)
            res = f'[>] successfully deleted folder "{utility.trim_path(path=path.__str__(),user_home_folder=packet.user.home_path)}"'
        else:
            res = ERR.EMPTY_PATH
        return res.encode()

    @staticmethod
    async def defi(packet: Packet) -> bytes:
        '''
        defi - delete by absolute path or in current folder.
               Use absolute path (e.g. defi D:\\file or defi /home/file)
               or relative path (e.g. defi file)
        '''

        if packet.cmd_tail:
            path = Path(utility.define_path(packet.cmd_tail[0], packet.user.current_path))
            if not utility.is_allowed(path, packet.user.permissions['x']):
                return ERR.PERMISSION_DENIED
            try:
                Path(path).unlink()
            except Exception as E:
                return ERR.OTHER(E)
            res = f'[>] successfully deleted file "{utility.trim_path(path=path.__str__(),user_home_folder=packet.user.home_path)}"'
        else:
            res = ERR.EMPTY_PATH
        return res.encode()

    @staticmethod
    async def send(packet: Packet, check_fragmentation: bool) -> Tuple[Callable, int] | Tuple[bool, bytes]:
        '''
        send - send file to file server.
                "send > here" - send file to your current path
                "send > home"
        '''

        cursor_position = 0
        mode = 'wb'

        _from, _to = packet.cmd_tail
        if _to is None or _to == 'home':
            path_to_save = Path().joinpath(packet.user.home_path, Path(_from).name)
        elif _to == 'here':
            path_to_save = Path().joinpath(packet.user.current_path, Path(_from).name)
        else:
            path_to_save = Path().joinpath(_to, Path(_from).name)

        if not path_to_save.parent.exists():
            return False, ERR.NOT_FOUND(path_to_save.__str__())
        elif not utility.is_allowed(path_to_save, packet.user.permissions['w']):
            return False, ERR.PERMISSION_DENIED
        else:  # try to find parts of file
            if check_fragmentation:
                fragmented_path = Path(path_to_save.__str__() + '.part')
                if fragmented_path.exists():
                    cursor_position = fragmented_path.stat().st_size
                    path_to_save = fragmented_path
                    mode = 'ab'

        async def saver(packet: Packet, chunk: int = 8192) -> bytes:
            '''
            'saver' function implements saving whole file or part of it.
            If there is no part of file - open file with mode 'wb' and write file data.
            If there is a connection failure during downloading - just save read data to filename.extension.part
            If we got part of file - just open existing file in 'ab' mode add data there

            When the whole file is downloaded - trim '.part' from file name
            '''
            saved_to = path_to_save.__str__()
            parted = False
            try:
                with open(path_to_save, mode) as f:
                    already_read = 0
                    while already_read < packet.data_length:
                        to_read = packet.data_length - already_read
                        try:
                            data = await asyncio.wait_for(
                                packet.user.sock.reader.read(chunk if to_read > chunk else to_read), timeout=5)
                            f.write(data)
                            already_read += len(data)
                            if data == b'' and to_read > 0:
                                raise Exception
                        except:
                            f.close()
                            if path_to_save.suffix != '.part':
                                path_to_save.rename(path_to_save.__str__() + '.part')
                                saved_to = path_to_save.__str__() + '.part'
                            parted = True
                            break
                if mode == 'ab' and parted is False:
                    path_to_save.rename(path_to_save.__str__()[:-5])
                    saved_to = path_to_save.__str__()[:-5]
            except Exception as E:
                return ERR.OTHER(E)
            return f'[>] file was successfully saved to "{utility.trim_path(path=saved_to.__str__(),user_home_folder=packet.user.home_path)}" '.encode()

        return saver, cursor_position

    @staticmethod
    async def jump(packet: Packet) -> bytes:
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
            if not utility.is_allowed(path, packet.user.permissions['x']):
                return ERR.PERMISSION_DENIED

            packet.user.current_path = path.__str__()
            res = f'[>] path changed to {utility.trim_path(path=path.__str__(),user_home_folder=packet.user.home_path)}'.encode()
        else:
            res = ERR.NOT_FOUND(packet.cmd_tail[0])
        return res

    @staticmethod
    async def info(packet: Packet, ) -> bytes:
        '''
        info - get information about folder (e.g info 'D:\\folder or info /home/folder)
               or about file (e.g. info 'D:\\folder\\file or info /home/file)
        '''
        if not packet.cmd_tail:
            res = ERR.EMPTY_PATH
        else:
            path = Path(utility.define_path(packet.cmd_tail[0], packet.user.current_path))
            if not utility.is_allowed(path, packet.user.permissions['x']):
                return ERR.PERMISSION_DENIED
            try:
                status = Path(path).stat()
                res = (f'[>] {utility.trim_path(path=path.__str__(),user_home_folder=packet.user.home_path)} info:\n\t'
                       f'Size: {status.st_size} bytes\n\t'
                       f'Permissions:{stat.filemode(status.st_mode)}\n\t'
                       # f'Owner:{status.st_uid}\n\t'
                       f'Created: {time.ctime(status.st_ctime)}\n\t'
                       f'Last modified: {time.ctime(status.st_mtime)}\n\t'
                       f'Last accessed: {time.ctime(status.st_atime)}'
                       )
            except Exception as E:
                res = ERR.OTHER(E)
        return res.encode()

    @staticmethod
    async def whoami(packet: Packet) -> bytes:
        '''
        whoami - information about user
        '''
        return packet.user.get_full_info().encode()

    @staticmethod
    async def rawsend(packet: Packet, check_fragmentation=True, chunk=4096) -> bytes:
        '''
        rawsend - ...
        '''
        mode = 'wb'
        parted = False
        file_name = packet.cmd_tail[0]
        path_to_save = Path(packet.user.current_path, file_name)
        saved_to = path_to_save.__str__()
        if check_fragmentation:
            fragmented_path = Path(path_to_save.__str__() + '.part')
            if fragmented_path.exists():
                path_to_save = fragmented_path
                mode = 'ab'
            try:
                with open(path_to_save, mode) as f:
                    already_read = 0
                    while already_read < packet.data_length:
                        to_read = packet.data_length - already_read
                        try:
                            data = await asyncio.wait_for(
                                packet.user.sock.reader.read(chunk if to_read > chunk else to_read), timeout=5)
                            f.write(data)
                            already_read += len(data)
                            if not data and to_read > 0:
                                raise Exception
                        except Exception as E:
                            f.close()
                            if path_to_save.suffix != '.part':
                                path_to_save.rename(path_to_save.__str__() + '.part')
                                saved_to = path_to_save.__str__() + '.part'
                            parted = True
                            break
                if mode == 'ab' and parted is False:
                    path_to_save.rename(path_to_save.__str__()[:-5])
                    saved_to = path_to_save.__str__()[:-5]
            except Exception as E:
                return ERR.OTHER(E)
        return f'{file_name} was successfully saved to {utility.trim_path(path=saved_to.__str__(),user_home_folder=packet.user.home_path)}'.encode()
