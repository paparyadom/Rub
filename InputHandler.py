import re
from typing import List
from Commands.SuperUserCommands import SuperUserCommands as SUC
from Commands.UserCommands import Packet, UserCommands as UC
from users import User, SuperUser

one_arg_template = r'^([a-z]+)\s((\"(.*)\")|([a-zA-z].*)|(/.*)|((.|\s+)*))'
one_arg_fnc = ('jump', 'list', 'where', 'open', 'nefo', 'defo', 'defi', 'info')


class InputsHandler:

    @staticmethod
    def get_help(packet: Packet, user: User | SuperUser) -> bytes:
        '''
        just write 'help'
        '''

        short_help = 'Avaliable commands:\n'
        if user.uid == 'superuser':
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
        cmd, *cmd_tail = InputsHandler.parse_data(command)
        packet = Packet(cmd_tail=tuple(cmd_tail), data_length=data_length)
        if cmd == 'help':
            return InputsHandler.get_help(packet, user)
        print('-----> SHOULD BE REWORKED module: InputsHandler.py line:38')
        if user.uid == 'superuser':
            return getattr(SUC, cmd)(user=user, packet=packet) if hasattr(SUC, cmd) \
                else f'[!] no such command {cmd}'.encode()
        else:
            return getattr(UC, cmd)(user=user, packet=packet) if hasattr(UC, cmd) \
                else f'[!] no such command {cmd}'.encode()

    @staticmethod
    def parse_data(command: bytes) -> List[str]:
        _command = command.decode()
        cmd_word_length = _command.find(' ')
        if cmd_word_length == -1:
            return [_command]
        else:
            cmd = _command[:cmd_word_length]
            if cmd in one_arg_fnc:
                groups = re.search(one_arg_template, _command)
                return [groups.group(1), groups.group(2)]
            return _command.split()

