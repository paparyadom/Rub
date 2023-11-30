from typing import Dict, Callable

from Commands.UserCommands import Packet, UserCommands as UC
from users import User


class InputsHandler:

    @staticmethod
    def cmd_get_help(packet: Packet, user: User = None) -> bytes:
        '''
        just write 'help'
        '''

        short_help = 'Avaliable users_commands:\n'
        for command, note in users_commands.items():
            short_help += f'- {command}{note["note"]}\n'

        if packet.cmd_tail:
            command = packet.cmd_tail[0]
            if (command in users_commands) and (users_commands[command].__doc__ is not None):
                res = users_commands[command]['cmd'].__doc__
            else:
                res = ' no help for you :('
            return res.encode()
        else:
            return short_help.encode() or '[!] No help for you'

    @staticmethod
    def handle_text_command(user: User, command: bytes, data_length: int) -> bytes:
        cmd, *cmd_tail = command.decode("utf-8").split()
        packet = Packet(cmd_tail=tuple(cmd_tail), data_length=data_length)
        if cmd in users_commands:
            return users_commands[cmd]['cmd'](user=user, packet=packet)
        return f'[!] no such command {cmd}'.encode()


users_commands: Dict[str, Dict[str, Callable | str]] = \
    {'where': {'cmd': UC.cmd_get_current_folder,
               'note': ' - show your current path'},
     'list': {'cmd': UC.cmd_get_list_of_files,
              'note': ' - show list of objects'},
     'open': {'cmd': UC.cmd_open_file,
              'note': ' - perform file opening'},
     'nefo': {'cmd': UC.cmd_create_folder,
              'note': ' - create new folder'},
     'defo': {'cmd': UC.cmd_delete_folder,
              'note': ' - delete folder'},
     'defi': {'cmd': UC.cmd_delete_file,
              'note': ' - delete file'},
     'send': {'cmd': UC.cmd_save_file,
              'note': ' - save file'},
     'info': {'cmd': UC.cmd_get_info,
              'note': ' - show information about object'},
     'jump': {'cmd': UC.cmd_change_folder,
              'note': ' - change path'},
     'help': {'cmd': InputsHandler.cmd_get_help,
              'note': ' - this list'},
     'whoami': {'cmd': UC.cmd_who,
                'note': ' - your info'}
     }
