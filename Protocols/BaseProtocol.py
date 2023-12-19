import socket
import struct
from abc import abstractmethod
from pathlib import Path
from typing import Tuple


class BaseProtocol(object):
    # SERVER SIDE
    @abstractmethod
    async def handshake(self, reader, writer) -> str:
        '''
        Recevie user id when user starts session
        '''
        writer.write('id?'.encode())
        user_id = await reader.read(128)
        return user_id.decode()

    @abstractmethod
    async def receive_data(self, reader, writer) -> Tuple[bytes, int]:
        pass

    @abstractmethod
    async def send_data(self, reader, writer, data: bytes, with_ack=False, ack=False):
        pass

    @abstractmethod
    async def send_file(self, reader, writer, data: bytes):
        pass

    # client side
    @abstractmethod
    def send_request(self, csock: socket.socket, request: str):
        '''
        client method
        '''
        pass

    @abstractmethod
    def receive_reply(self, csock: socket.socket, with_ack=False) -> bytes | Tuple[bool, bytes]:
        '''
         client method
        '''
        pass

    @abstractmethod
    def file_send_request(self, csock: socket.socket, request: str):
        '''
         client method
        '''
        pass


class TCD8(BaseProtocol):

    async def receive_data(self, reader, writer) -> Tuple[bytes, int]:
        '''
        receive data according to protocol:
        total length [8 bytes] + command length [8 bytes] + other data length [8 bytes] + data if data length != 0

        '''
        addr = writer.get_extra_info("peername")
        failed_recv = (b'', 0)
        try:
            r_total_len = await reader.read(8)
            r_c_length = await reader.read(8)
            r_data_len = await reader.read(8)
            (length,) = struct.unpack('>Q', r_total_len)
            (cmd_length,) = struct.unpack('>Q', r_c_length)
            (data_length,) = struct.unpack('>Q', r_data_len)
            command = await reader.read(cmd_length)
        except Exception as E:
            print(f'[x] something went wrong {E}')
            return failed_recv
        except ConnectionError:
            print(f'[x] client suddenly closed connection')
            return failed_recv
        print(f'<<... {command} from: {addr} length: {length}')
        if not command:
            print(f'[x] disconnected by, {addr}')
        return command, data_length

    async def send_data(self, reader, writer, data: bytes, with_ack=False, ack=False):
        '''
        send text as bytes to user
        protocol:
        total length [8 bytes] + data if with_ack == False
        total length [8 bytes] + acknowledge [1 byte] + data if with_ack == True
        '''
        addr = writer.get_extra_info("peername")
        print(data)
        try:
            if not with_ack:
                length: bytes = struct.pack('>Q', len(data))
                writer.write(length)
                writer.write(data)
                await writer.drain()
            else:
                length: bytes = struct.pack('>Q', len(data) + 1)
                _ack: bytes = struct.pack('?', ack)
                writer.write(length)
                writer.write(_ack)
                writer.write(data)
                await writer.drain()
        except ConnectionError:
            print(f'[x] client suddenly closed, can not send')
        print(f'...>> {data} to: {addr}')

    async def send_file(self, reader, writer, data: bytes):
        '''
        send file as bytes to user by generator
        protocol:
        total length [8 bytes] + data chunk by chunk
        '''
        addr = writer.get_extra_info("peername")
        print(data)
        try:
            gen, file_size = data
            length: bytes = struct.pack('>Q', file_size)
            writer.write(length)
            await writer.drain()
            async for chunk in gen:
                writer.write(chunk)
                await writer.drain()
                print(chunk)
            # chunk = next(gen)
            # while chunk:
            #     writer.write(chunk)
            #     await writer.drain()
            #     print(chunk)
            #     chunk = next(gen)

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

    def receive_reply(self, csock: socket.socket, with_ack=False) -> Tuple[bytes, bool] | bytes:
        # ack = False
        rdata = csock.recv(8)
        if with_ack:
            (ack,) = csock.recv(1)
            (to_read,) = struct.unpack('>Q', rdata)
            to_read -= 1
        else:
            (to_read,) = struct.unpack('>Q', rdata)
        data = b''
        while to_read:
            try:
                rdata = csock.recv(4096 if to_read > 4096 else to_read)
                data += rdata
                to_read -= len(rdata)
            except:
                break
        return (data, ack) if with_ack else data

    def file_send_request(self, csock: socket.socket, request: str):
        _, _from, *_to = request.split()

        def pre_send_request():
            self.send_request(csock, request)
            return self.receive_reply(csock, with_ack=True)

        def send_file(_from, cursor):
            (_cursor,) = struct.unpack('>Q', cursor)
            file_size = Path(_from).stat().st_size
            if _cursor > file_size:
                _cursor = 0
            t_length = struct.pack('>Q', len(request) + 8)
            req_length = struct.pack('>Q', len(request))
            data_length = struct.pack('>Q', file_size - _cursor)
            packet = t_length + req_length + data_length + request.encode()
            csock.sendall(packet)
            with open(_from, 'rb') as f:
                f.seek(_cursor)
                csock.sendall(f.read())

        data, ack = pre_send_request()
        if ack:
            send_file(_from, data)


class SimpleProto(BaseProtocol):
    # SERVER SIDE
    async def receive_data(self, reader, writer) -> Tuple[bytes, int]:
        '''
        dumb reading data from socket
        '''
        addr = writer.get_extra_info("peername")
        failed_recv = (b'', 0)
        try:
            command = await reader.read(4096)
        except Exception as E:
            print(f'[x] something went wrong {E}')
            return failed_recv
        except ConnectionError:
            print(f'[x] client suddenly closed connection')
            return failed_recv
        print(f'<<... {command} from: {addr}')
        if not command:
            print(f'[x] disconnected by, {addr}')
        return command, 0

    async def send_data(self, reader, writer, data: bytes, with_ack=False, ack=False):
        '''
        send text as bytes to user
        protocol:
        total length [8 bytes] + data
        '''
        addr = writer.get_extra_info("peername")
        try:
            writer.write(data)
            await writer.drain()
        except ConnectionError:
            print(f'[x] client suddenly closed, can not send')
        print(f'...>> {data} to: {addr}')

    async def send_file(self, reader, writer, data: bytes):
        '''
        send file as bytes to user by generator
        '''
        addr = writer.get_extra_info("peername")
        try:
            gen, file_size = data
            chunk = next(gen)
            while chunk:
                writer.write(chunk)
                await writer.drain()
                print(chunk)
                chunk = next(gen)
        except StopIteration:
            print(f'[i] EOF')
        except ConnectionError:
            print(f'[x] client suddenly closed, can not send')
        print(f'...>> {data} to: {addr}')

    # CLIENT SIDE
    def send_request(self, csock: socket.socket, request: str):
        '''
        dumb sending data to socket
        '''

        csock.sendall(request.encode())

    def receive_reply(self, csock: socket.socket, with_ack=False) -> bytes:
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
