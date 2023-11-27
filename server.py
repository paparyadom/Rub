import logging
import pickle
import socket
import struct
import sys
from types import GeneratorType
from typing import Union, Tuple

import select

from input_handle import InputsHandler
from users import User
from users import UsersHandler


class Server:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.outputs = []
        self.inputs = []
        self.server_socket = self.__init_socket(self.host, self.port)
        self.CommandHandler = InputsHandler()
        self.UserHandler = UsersHandler()
        self.logger = self.__init_logger()

    @staticmethod
    def __init_socket(host: str, port: int) -> socket.socket:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((host, port))
        sock.listen(10)
        return sock

    @staticmethod
    def __init_logger() -> logging.Logger:

        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(logging.Formatter(fmt='[%(levelname)s] %(message)s'))
        logger.addHandler(handler)
        return logger

    def run(self):
        '''

        start file server
        '''
        self.inputs.append(self.server_socket)
        while True:
            self.logger.info('waiting for connections or data...')
            readable, writeable, exceptional = select.select(self.inputs, self.outputs, self.inputs)
            for sock in readable:
                if sock is self.server_socket:
                    sock, addr = self.server_socket.accept()
                    if not self.UserHandler.check_user(addr):
                        self.UserHandler.add_user(addr, sock)
                    self.logger.info(f'connected by {addr}')
                    self.inputs.append(sock)
                else:
                    addr = sock.getpeername()
                    if not self._handle_query(self.UserHandler.from_user(addr)):
                        self.inputs.remove(sock)
                        self.logger.info(f'{addr} was removed from inputs')
                        if sock in self.outputs:
                            self.outputs.remove(sock)
                            self.logger.info(f'{addr} was removed from outputs')
                        self.__close_connection(sock)

    def _handle_query(self, user: User) -> bool:
        '''
        handle queries from users
        '''
        command, data_length = self.__receive_data(user)
        if command:
            output_data = self.CommandHandler.handle_text_command(user, command, data_length)
            return self.__send_answer(user, output_data)
        else:
            return False

    def __receive_data(self, user: User) -> Tuple[bytes, int]:
        '''
        try to receive data according to protocol:
        total length [8 bytes] + command length [8 bytes] + other data length [8 bytes] + data if data length != 0

        '''
        try:
            r_total_len = user.sock.recv(8)
            r_c_length = user.sock.recv(8)
            r_data_len = user.sock.recv(8)
            (length,) = struct.unpack('>Q', r_total_len)
            (cmd_length,) = struct.unpack('>Q', r_c_length)
            (data_length,) = struct.unpack('>Q', r_data_len)
            command = user.sock.recv(cmd_length)
            if command.startswith(b'exit'):
                command = b''
        except Exception as E:
                self.logger.info(f'something went wrong {E}')
                return b'', 0

        except ConnectionError:
            self.logger.info(f'client suddenly closed connection')
            return b''
        self.logger.info(f'received {command} from: {user.addr} length: {length}')
        if not command:
            self.logger.info(f'disconnected by, {user.addr}')
        return command, data_length

    def __send_answer(self, user: User, output_data: Union[GeneratorType, bytes]) -> bool:
        '''
        send text answer or file as bytes to user
        output_data is bytes for text answer
        or
        <class 'generator'> if need to send file

        '''
        if isinstance(output_data[0], GeneratorType):
            self.__send_file(user, output_data)
        else:
            self.__send_text(user, output_data)
        return True

    def __send_file(self, user: User, data):
        '''

        send file as bytes to user by generator
        '''
        try:
            gen, file_size = data
            length: bytes = struct.pack('>Q', file_size)
            user.sock.sendall(length)
            chunk = next(gen)
            while chunk:
                user.sock.sendall(chunk)
                print(chunk)
                chunk = next(gen)
        except StopIteration:
            self.logger.info('EOF')
        except ConnectionError:
            self.logger.info(f'client suddenly closed, can not send')
        self.logger.info(f'send: {data} to: {user.addr}')

    def __send_text(self, user: User, data: bytes):
        '''
        send text as bytes to user
        '''
        try:
            length: bytes = struct.pack('>Q', len(data))
            user.sock.send(length)
            user.sock.send(data)
        except ConnectionError:
            self.logger.info(f'client suddenly closed, can not send')
        self.logger.info(f'send: {data} to: {user.addr}')

    def __close_connection(self, user_sock: socket.socket):
        user_sock.close()


# def input_stup(server: Server):
#     while True:
#         print('i am alive')
#         bb = input('write something')
#         if bb == 'exit':
#             server.stop_server()
#
#         print(bb)

if __name__ == '__main__':
    import threading
    try:
        host, port = sys.argv[1:]
        server = Server(host, port)
    except:
        host, port = '', 5460
        server = Server(host, int(port))
    serv = threading.Thread(target=server.run)
    # other = threading.Thread(target=input_stup, args=(server,))
    # other.start()
    serv.start()


