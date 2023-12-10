import logging
import os
import socket
import sys
from types import GeneratorType
from typing import Union

import select

from InputHandler import InputsHandler
from Protocols.BaseProtocol import *
from Saveloader.SaveLoader import JsonSaveLoader
from Session.SessionHandler import UsersSessionHandler
from users import User

if not os.path.exists('storage'):
    os.mkdir('storage')


class Server:
    def __init__(self, host: str, port: int, proto: BaseProtocol):
        self.host = host
        self.port = port
        self.outputs = []
        self.inputs = []

        self.ssock = self.__init_socket(self.host, self.port)
        self.logger = self.__init_logger()

        self.__InputsHandler = InputsHandler({'superuser'})
        self.UserDataHandler = JsonSaveLoader(storage_path='storage')
        self.UsersSessionHandler = UsersSessionHandler(self.UserDataHandler)
        self.Proto = proto

    def run(self):
        '''

        start file server
        '''
        self.inputs.append(self.ssock)
        while True:
            self.logger.info(f'({self.host}:{self.port}) waiting for connections or data...')
            readable, writeable, exceptional = select.select(self.inputs, self.outputs, self.inputs)
            for sock in readable:
                if sock is self.ssock:
                    sock, addr = self.ssock.accept()  # accept connection from user
                    # uid = self.Proto.handshake(sock)
                    self.UsersSessionHandler.check_user(addr, sock, self.Proto.handshake(sock))  # check user
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
            if command.startswith((b'send', b'open')):
                output_data = self.__InputsHandler.handle_files(user, command, data_length, self.Proto)
            else:
                output_data = self.__InputsHandler.handle_text_command(user, command, data_length)
            return self.__handle_answer(user, output_data)
        else:
            return False

    def __handle_answer(self, user: User, output_data: Union[GeneratorType, bytes]) -> bool:
        '''
        send text answer or file as bytes to user
        output_data is bytes for text answer
        or
        <class 'generator'> in case of file sending

        '''
        if isinstance(output_data[0], GeneratorType):
            self.Proto.send_file(user.sock, output_data)
        else:
            self.Proto.send_data(user.sock, output_data)
        return True

    def stop(self):
        sessions = set(addr for addr in self.UsersSessionHandler.active_sessions.keys())
        for addr in sessions:
            self.UsersSessionHandler.end_user_session(addr)
        self.ssock.close()
        logging.warning('STOP')

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

    try:
        host, port = sys.argv[1:]
        server = Server(host, int(port), proto=SimpleProto())
    except:
        host, port = '', 5455
        server = Server(host, port, proto=SimpleProto())
    try:
        server.run()
    except KeyboardInterrupt:
        server.stop()

