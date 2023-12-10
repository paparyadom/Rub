import socket
import struct
from abc import abstractmethod
from pathlib import Path
from typing import Tuple


class BaseProtocol(object):
    # SERVER SIDE
    @abstractmethod
    def handshake(self, usock: socket.socket) -> str:
        '''

        Args:
            usock: user socket

        Returns: user id as str

        '''

    @abstractmethod
    def receive_data(self, usock: socket.socket) -> Tuple[bool, bytes, int]:
        pass

    @abstractmethod
    def send_data(self, usock: socket.socket, data: bytes):
        pass

    @abstractmethod
    def send_file(self, usock: socket.socket, data: bytes):
        pass

    @abstractmethod
    def send_request(self, csock: socket.socket, request: str):
        '''
        client method
        '''
        pass

    #client side
    @abstractmethod
    def receive_reply(self, csock: socket.socket) -> bytes:
        '''
         client method
        '''
        pass

    @abstractmethod
    def file_send_request(self, csock: socket.socket, request: str):
        pass


class TCD8(BaseProtocol):
    def handshake(self, usock: socket.socket) -> str:
        '''
        Recevie user id when user starts session
        may be should be reworked
        '''
        usock.sendall('id?'.encode())
        user_id = usock.recv(128)
        return user_id.decode()

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

    def send_data(self, usock: socket.socket, data: bytes):
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

    def send_request(self, csock: socket.socket, request: str):
        cmd_length: bytes = struct.pack('>Q', len(request))
        length: bytes = struct.pack('>Q', len(request) + 8)
        data_length: bytes = struct.pack('>Q', 0)
        packet = length + cmd_length + data_length + request.encode()
        csock.sendall(packet)

    def receive_reply(self, csock: socket.socket) -> bytes:
        rdata = csock.recv(8)
        (to_read,) = struct.unpack('>Q', rdata)
        data = b''
        while to_read:
            try:
                rdata = csock.recv(4096 if to_read > 4096 else to_read)
                data += rdata
                to_read -= len(rdata)
            except:
                break
        return data

    def file_send_request(self, csock: socket.socket, request: str):
        csock.settimeout(None)
        command, _from, *_to = request.split()
        file_size = Path(_from).stat().st_size
        t_length = struct.pack('>Q', len(request) + 8)
        req_length = struct.pack('>Q', len(request))

        def pre_send_request():
            data_length = struct.pack('>Q', 0)
            packet = t_length + req_length + data_length + request.encode()
            csock.sendall(packet)

            _ = csock.recv(8)  # get total length of reply
            r_cursor = csock.recv(8)  # get cursor value for file.seek(). 0 if no part of sending file
            (cursor,) = struct.unpack('>Q', r_cursor)
            return cursor

        def send_file(_from, cursor):
            data_length = struct.pack('>Q', file_size - cursor)
            packet = t_length + req_length + data_length + request.encode()
            csock.sendall(packet)
            with open(_from, 'rb') as f:
                f.seek(cursor)
                csock.sendall(f.read())
            csock.settimeout(.05)

        send_file(_from, pre_send_request())


class SimpleProto(BaseProtocol):
    # SERVER SIDE
    def handshake(self, usock: socket.socket) -> str:
        '''
        Recevie user id when user starts session
        may be should be reworked
        '''
        usock.sendall('id?'.encode())
        user_id = usock.recv(128)
        return user_id.decode()

    def receive_data(self, usock: socket.socket) -> Tuple[bool, bytes, int]:
        '''
        dumb reading data from socket
        '''
        addr = usock.getpeername()
        failed_recv = (False, b'', 0)
        try:
            command = usock.recv(4096)
        except Exception as E:
            print(f'[x] something went wrong {E}')
            return failed_recv
        except ConnectionError:
            print(f'[x] client suddenly closed connection')
            return failed_recv
        print(f'<<... {command} from: {addr}')
        if not command:
            print(f'[x] disconnected by, {addr}')
        return True, command, 0

    def send_data(self, usock: socket.socket, data: bytes):
        '''
        send text as bytes to user
        protocol:
        total length [8 bytes] + data
        '''
        addr = usock.getpeername()
        try:
            usock.send(data)
        except ConnectionError:
            print(f'[x] client suddenly closed, can not send')
        print(f'...>> {data} to: {addr}')

    def send_file(self, usock: socket.socket, data: bytes):
        '''
        send file as bytes to user by generator
        '''
        addr = usock.getpeername()
        try:
            gen, file_size = data
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

    #CLIENT SIDE
    def send_request(self, csock: socket.socket, request: str):
        '''
        dumb sending data to socket
        '''

        csock.sendall(request.encode())

    def receive_reply(self, csock: socket.socket) -> bytes:
        '''
        awaiting and receiving reply from server
        '''
        data = b''
        rdata = csock.recv(4096)
        while rdata:
            data += rdata
            try:
                rdata = csock.recv(4096)
            except:
                break
        return data
