import logging
import os
import socket
import sys
from types import GeneratorType
from typing import Union

import select

from Saveloader.SaveLoader import JsonSaveLoader
from InputHandler import InputsHandler
from Protocols.BaseProtocol import TCD8
from users import User
from Session.SessionHandler import UsersSessionHandler

if not os.path.exists('storage'):
    os.mkdir('storage')


class Server:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.outputs = []
        self.inputs = []

        self.server_socket = self.__init_socket(self.host, self.port)
        self.logger = self.__init_logger()

        self.CommandHandler = InputsHandler()
        self.UserDataHandler = JsonSaveLoader(storage_path='storage')
        self.UsersSessionHandler = UsersSessionHandler(self.UserDataHandler)
        self.Proto = TCD8()

    def run(self):
        '''

        start file server
        '''
        self.inputs.append(self.server_socket)
        while True:
            self.logger.info(f'({self.host}:{self.port}) waiting for connections or data...')
            readable, writeable, exceptional = select.select(self.inputs, self.outputs, self.inputs)
            for sock in readable:
                if sock is self.server_socket:
                    sock, addr = self.server_socket.accept()
                    self.UsersSessionHandler.check_user(addr, sock)
                    self.logger.info(f'connected by {addr}')
                    self.inputs.append(sock)
                else:
                    addr = sock.getpeername()
                    if not self._handle_query(self.UsersSessionHandler.from_user(addr)):
                        self.inputs.remove(sock)
                        self.logger.info(f'{addr} was removed from inputs')
                        self.UsersSessionHandler.end_user_session(addr)
                        if sock in self.outputs:
                            self.outputs.remove(sock)
                            self.logger.info(f'{addr} was removed from outputs')
                        self.__close_connection(sock)

    def _handle_query(self, user: User) -> bool:
        '''
        handle queries from users
        '''
        qstatus, command, data_length = self.Proto.receive_data(user.sock)
        if command and command != b'exit':
            output_data = self.CommandHandler.handle_text_command(user, command, data_length)
            return self.__handle_answer(user, output_data)
        else:
            return False

    def __handle_answer(self, user: User, output_data: Union[GeneratorType, bytes]) -> bool:
        '''
        send text answer or file as bytes to user
        output_data is bytes for text answer
        or
        <class 'generator'> if need to send file

        '''
        if isinstance(output_data[0], GeneratorType):
            self.Proto.send_file(user.sock, output_data)
        else:
            self.Proto.send_text(user.sock, output_data)
        return True

    @staticmethod
    def __close_connection(user_sock: socket.socket):
        user_sock.close()

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


if __name__ == '__main__':
    import threading

    try:
        host, port = sys.argv[1:]
        server = Server(host, port)
    except:
        host, port = 'localhost', 5454
        server = Server(host, int(port))
    server.run()
