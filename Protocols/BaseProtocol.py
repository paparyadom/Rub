import socket
from abc import abstractmethod
from typing import Tuple
import struct


class BaseProtocol(object):
    @abstractmethod
    def receive_data(self, usock: socket.socket) -> Tuple[bytes, int]:
        pass

    @abstractmethod
    def send_text(self, usock: socket.socket, data: bytes):
        pass

    @abstractmethod
    def send_file(self, usock: socket.socket, data: bytes):
        pass


class TCD8(BaseProtocol):
    def receive_data(self, usock: socket.socket) -> Tuple[bool, bytes, int]:
        '''
        receive data according to protocol:
        total length [8 bytes] + command length [8 bytes] + other data length [8 bytes] + data if data length != 0

        '''
        addr = usock.getpeername()
        failed_recv = (False, b'', 0)
        try:
            r_total_len = usock.recv(8)
            r_c_length = usock.recv(8)
            r_data_len = usock.recv(8)
            (length,) = struct.unpack('>Q', r_total_len)
            (cmd_length,) = struct.unpack('>Q', r_c_length)
            (data_length,) = struct.unpack('>Q', r_data_len)
            command = usock.recv(cmd_length)
        except Exception as E:
            print(f'[x] something went wrong {E}')
            return failed_recv
        except ConnectionError:
            print(f'[x] client suddenly closed connection')
            return failed_recv
        print(f'<<... {command} from: {addr} length: {length}')
        if not command:
            print(f'[x] disconnected by, {addr}')
        return True, command, data_length

    def send_text(self, usock: socket.socket, data: bytes):
        '''
        send text as bytes to user
        protocol:
        total length [8 bytes] + data
        '''
        addr = usock.getpeername()
        try:
            length: bytes = struct.pack('>Q', len(data))
            usock.send(length)
            usock.send(data)
        except ConnectionError:
            print(f'[x] client suddenly closed, can not send')
        print(f'...>> {data} to: {addr}')

    def send_file(self, usock: socket.socket, data: bytes):
        '''

        send file as bytes to user by generator
        protocol:
        total length [8 bytes] + data chunk by chunk
        '''
        addr = usock.getpeername()
        try:
            gen, file_size = data
            length: bytes = struct.pack('>Q', file_size)
            usock.sendall(length)
            chunk = next(gen)
            while chunk:
                usock.sendall(chunk)
                print(chunk)
                chunk = next(gen)
        except StopIteration:
            print(f'[i] EOF')
        except ConnectionError:
            print(f'[x] client suddenly closed, can not send')
        print(f'...>> {data} to: {addr}')
