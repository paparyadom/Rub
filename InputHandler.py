import re
import struct
from typing import Tuple, Any

from Commands.SuperUserCommands import SuperUserCommands as SUC
from Commands.UserCommands import Packet, UserCommands as UC
from users import User, SuperUser

one_arg_template = r'^([a-z]+)\s((\"(.*)\")|([a-zA-z].*)|(/.*)|((.|\s+)*))'
send_file_template = r'^([a-z]+)\s((\"(.*)\")|([a-zA-z].*)|(/.*)|((.|\s+)*))'  # TO DO
one_arg_fnc = ('jump', 'list', 'where', 'open', 'nefo', 'defo', 'defi', 'info')


class InputsHandler:
    def __init__(self, super_users):
        self.__super_users = super_users

    @staticmethod
    def get_help(packet: Packet) -> bytes:
        '''
        just write 'help'
        '''

        short_help = 'Avaliable commands:\n'
        if packet.user.uid == 'superuser':
            cmd_list = SUC
        else:
            cmd_list = UC
        _list = [method for method in dir(cmd_list) if not method.startswith('__')]
        short_help += '\n'.join(_list)

        if packet.cmd_tail:
            command = packet.cmd_tail[0]
            if hasattr(cmd_list, command):
                res = getattr(cmd_list, command).__doc__ or 'No info'
            else:
                res = 'no help for you'
            return res.encode()
        else:
            return short_help.encode()

    @staticmethod
    def handle_text_command(user: User | SuperUser, command: bytes, data_length: int) -> bytes:
        '''

        Args:
            user: instance of class User or SuperUser
            command: text command from user
            data_length: incoming data length

        Returns: string as bytes

        Incoming command -- <function parse_data> --> processing function -> bytes
        '''
        cmd, *cmd_tail = InputsHandler.parse_data(command)
        packet = Packet(user=user, cmd_tail=cmd_tail, data_length=data_length)
        if cmd == 'help':
            return InputsHandler.get_help(packet)
        if isinstance(user, SuperUser):
            return getattr(SUC, cmd)(packet=packet) if hasattr(SUC, cmd) \
                else f'[!] no such command {cmd}'.encode()
        else:
            return getattr(UC, cmd)(packet=packet) if hasattr(UC, cmd) \
                else f'[!] no such command {cmd}'.encode()

    @staticmethod
    def parse_data(command: bytes) -> Tuple[str] | Tuple[str | Any, str | Any]:
        '''
        Extract from user command "command" (this command defines target function) and "command args".
        If got single command return Tuple(command as str)

        If besides command got any arg - try to extract it using one_arg_template
        If extraction was successful - return Tuple(command as str, args as str)
        otherwise split incoming command by spaces and return result
        '''
        _command = command.decode()
        _command = _command.strip()  # in case of putty

        cmd_word_length = _command.find(' ')  # find first space to extract command word
        if cmd_word_length == -1:
            return _command,
        else:
            cmd = _command[:cmd_word_length]  # getting body
            if cmd in one_arg_fnc:
                groups = re.search(one_arg_template, _command)
                return groups.group(1), groups.group(2)
            return tuple(_command.split())

    @staticmethod
    def handle_files(user: User | SuperUser, command: bytes, data_length: int, proto) -> bytes:
        cmd, *cmd_tail = InputsHandler.parse_data(command)
        packet = Packet(user=user, cmd_tail=cmd_tail, data_length=data_length)
        if cmd == 'open':
            return UC.open(packet) if isinstance(user, User) else SUC.open(packet)
        else:
            send_func = UC.send if isinstance(user, User) else SUC.send
            cursor, sender = send_func(packet=packet, check_fragmentation=True)
            proto.send_data(user.sock, struct.pack('>Q', cursor))
            qstatus, command, data_length = proto.receive_data(user.sock)
            packet = Packet(user=user, cmd_tail=('',), data_length=data_length)
            return sender(packet=packet)
