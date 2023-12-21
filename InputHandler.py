import re
import struct
from typing import Tuple, Any

from Commands.SuperUserCommands import SuperUserCommands as SUC
from Commands.UserCommands import Packet, ERR, UserCommands as UC
from users import User, SuperUser


class InputsHandler:
    one_arg_template = r'^((\"(.*)\")|([a-zA-z].*)|(/.*)|((.|\s+)*))'
    send_file_template = r'^((\"(.*)\")|(/(.*))|([a-zA-z].*))\s>\s(.*)'
    one_arg_fn = ('jump', 'list', 'where', 'open', 'nefo', 'defo', 'defi', 'info')
    send_file_fn = ('send')

    @staticmethod
    def get_help(packet: Packet) -> bytes:
        '''
        just write 'help'
        '''

        short_help = 'Avaliable commands:\n'
        cmd_list = SUC if isinstance(packet.user, SuperUser) else UC
        _list = [method for method in dir(cmd_list) if not method.startswith('__')]
        short_help += '\n'.join(_list)

        if packet.cmd_tail:
            command = packet.cmd_tail[0]
            res = (getattr(cmd_list, command).__doc__ or 'No info') if hasattr(cmd_list, command) else 'no help for you'
            return res.encode()
        else:
            return short_help.encode()

    @staticmethod
    async def handle_text_command(user: User | SuperUser, command: bytes, data_length: int) -> bytes:
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
            return await getattr(SUC, cmd)(packet=packet) if hasattr(SUC, cmd) \
                else ERR.UNKNOWN_COMMAND
        else:
            return await getattr(UC, cmd)(packet=packet) if hasattr(UC, cmd) \
                else ERR.UNKNOWN_COMMAND

    @staticmethod
    def parse_data(command: bytes) -> Tuple[str] | Tuple[str | Any, ...]:
        '''
        Extract from user command "command" (this command defines target function) and "command args (body)".
        If got single command return Tuple(command as str)

        If besides command got any arg - try to extract it using one_arg_template
        If extraction was successful - return Tuple(command as str, args as str)
        otherwise split incoming command by spaces and return result
        '''
        try:
            _command = command.decode()
        except:
            return ' ',
        _command = _command.strip()  # in case of putty
        command_word_length = _command.find(' ')  # find first space to extract command word
        if command_word_length == -1:
            return _command,
        else:
            cmd = _command[:command_word_length]  # getting body
            if cmd in InputsHandler.one_arg_fn:
                groups = re.search(InputsHandler.one_arg_template, _command[command_word_length + 1:])
                return cmd, groups.group(1)
            elif cmd in InputsHandler.send_file_fn:
                groups = re.search(InputsHandler.send_file_template, _command[command_word_length + 1:])
                if groups is None:
                    return cmd, _command[command_word_length + 1:], None
                else:
                    return cmd, groups.group(1), groups.group(7)
            return tuple(_command.split())

    @staticmethod
    async def handle_files(user: User | SuperUser, command: bytes, data_length: int, proto) -> bytes:
        '''
        This function is used to handle files operations.
        'open' function - open file -> send to user as bytes

        'send' function - used to receive file from user and save it.

        This functions apply standard functions from Protocols.TCD8 with 'with_ack' flag.
        Execution steps:
        -> receive from user packet with command 'send' and body with 'file name or path' + word 'home' or word 'here' or 'path to save'
        -> check existing of 'path to save' and user permissions. If both of these conditions are ok - go to next step,
        otherwise server can not execute this operation and send to user packet with ack=False and message why request was declined.
        -> check existing fragments of sending file (file with suffix '.part')
        -> send reply with ack=True and size of file (if we got just part of it) or 0 (if parts do not exist)
        -> receive and save file
        '''
        cmd, *cmd_tail = InputsHandler.parse_data(command)
        packet = Packet(user=user, cmd_tail=cmd_tail, data_length=data_length)
        if cmd == 'open':
            return await UC.open(packet) if isinstance(user, User) else await SUC.open(packet)
        elif cmd == 'send':
            send_func = UC.send if isinstance(user, User) else SUC.send
            saver_if_ok, cursor_if_ok = await send_func(packet=packet, check_fragmentation=True)
            if saver_if_ok:  # if got function
                await proto.send_data(user.sock.reader, user.sock.writer, struct.pack('>Q', cursor_if_ok), with_ack=True, ack=True)
                command, data_length = await proto.receive_data(user.sock.reader, user.sock.writer)
                packet = Packet(user=user, cmd_tail=('',), data_length=data_length)
                return await saver_if_ok(packet=packet)
            else:
                await proto.send_data(user.sock.reader, user.sock.writer, struct.pack('>Q', 0), with_ack=True, ack=False)
                return cursor_if_ok
        elif cmd == 'rawsend':
            file_name = cmd_tail[0]
            file_size = int(cmd_tail[1])
            send_func = UC.rawsend if isinstance(user, User) else SUC.rawsend
            packet = Packet(user=user, cmd_tail=(file_name,), data_length=file_size)
            return await send_func(packet)




