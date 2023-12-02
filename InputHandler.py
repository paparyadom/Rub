from Commands.UserCommands import Packet, UserCommands as UC
from Commands.SuperUserCommands import SuperUserCommands as SUC
from users import User, SuperUser


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
        cmd, *cmd_tail = command.decode("utf-8").split()
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
