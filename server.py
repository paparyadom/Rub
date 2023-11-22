import logging
import socket
import struct
import sys
from types import GeneratorType

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
    def __init_socket(host:str, port:int) -> socket.socket:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((host, port))
        sock.listen(10)
        return sock

    def run(self):
        self.inputs.append(self.server_socket)
        while True:
            self.logger.info('waiting for connections or data...')
            readable, writeable, exceptional = select.select(self.inputs, self.outputs, self.inputs)
            for sock in readable:
                if sock is self.server_socket:
                    sock, addr = self.server_socket.accept()
                    if not self.UserHandler.check_user(addr):
                        self.UserHandler.add_user(addr, sock)
                    self.logger.info(f'Connected by {addr}')
                    self.inputs.append(sock)
                else:
                    addr = sock.getpeername()
                    if not self._handle_query(self.UserHandler.from_user(addr)):
                        self.inputs.remove(sock)
                        self.logger.info(f'{addr} was removed from inputs')
                        if sock in self.outputs:
                            self.outputs.remove(sock)
                            self.logger.info(f'{addr} was removed from outputs')
                        sock.close()

    def _handle_query(self, user: User):
        try:
            rdata = user.sock.recv(8)
            (length,) = struct.unpack('>Q', rdata)
            rdata = b''
            while len(rdata) < length:
                to_read = length - len(rdata)
                print(to_read)
                rdata += user.sock.recv(
                    4096 if to_read > 4096 else to_read)
        except ConnectionError:
            self.logger.info(f"Client suddenly closed while receiving")
            return self.CommandHandler.close_connection(user.sock)
        print(f"Received {rdata} from: {user.addr} length: {length}")
        if not rdata:
            self.logger.info("Disconnected by", user.addr)
            return self.CommandHandler.close_connection(user.sock)

        answer = self.CommandHandler.handle_input(user, rdata)
        if isinstance(answer[0], GeneratorType):
            try:
                gen, file_size = answer
                length: bytes = struct.pack('>Q', file_size)
                user.sock.sendall(length)
                chunk = next(gen)
                while chunk:
                    user.sock.sendall(chunk)
                    print(chunk)
                    chunk = next(gen)
            except StopIteration:
                self.logger.info('end of file')
            except ConnectionError:
                self.logger.info(f"Client suddenly closed, cannot send")
                return self.CommandHandler.close_connection(user.sock)
        else:
            try:
                length: bytes = struct.pack('>Q', len(answer))
                user.sock.send(length)
                user.sock.send(answer)
            except ConnectionError:
                self.logger.info(f"Client suddenly closed, cannot send")
                return self.CommandHandler.close_connection(user.sock)
        self.logger.info(f"Send: {answer} to: {user.addr}")
        return True

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
        server = Server(host, port)
    except:
        host, port = '', 5458
        server = Server(host, port)
    server.run()
