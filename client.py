import socket
import struct
import os

UUID = '628c93f2-8d44-11ee-9706-07b2e7b92ea1'

class Client:
    def __init__(self):
        self.host = None
        self.port = None
        self.sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False

    def connect(self, host: str, port: int):
        self.sock.connect((host, port))
        self.host, self.port = host, port
        self.connected = True

    def communicate(self):
        while self.connected:
            print(f'[i] connected to {self.host}:{self.port}')
            self.__auth()
            while True:
                input_command = input("[...] type:")
                if not input_command:
                    input_command = 'nop'

                if input_command.startswith('exit'):
                    self.send_request(input_command)
                    print("[x] close by client")
                    break
                elif input_command.startswith('send'):
                    try:
                        self.send_file(input_command)
                    except Exception as E:
                        print(E)
                        input()
                else:
                    self.send_request(input_command)

                try:
                    rdata = self.sock.recv(8)
                    (length,) = struct.unpack('>Q', rdata)
                    print(f'awaiting {length} bytes')
                    data = b''
                    to_read = length - len(data)
                    data += self.sock.recv(4096 if to_read > 4096 else to_read)
                except Exception as e:
                    print(e)

                try:
                    print(f'[r]\n{data.decode()}')
                except:
                    print(f'[r]\n{data}')

                if not data:
                    print("[x] closed by server")
                    break
            self.sock.close()
            self.connected = False
            print("[x] client disconnected")
            break

    def send_request(self, input_command: str):
        cmd_length: bytes = struct.pack('>Q', len(input_command))
        length: bytes = struct.pack('>Q', len(input_command) + 8)
        data_length: bytes = struct.pack('>Q', 0)

        packet = length + cmd_length + data_length + input_command.encode()
        self.sock.sendall(packet)
        # self.sock.sendall(length)
        # self.sock.sendall(cmd_length)
        # self.sock.sendall(data_length)
        # self.sock.sendall(input_command.encode())

    def send_file(self, input_command):
        command, *_from, _to = input_command.split()
        file_size = os.stat(' '.join(_from))

        with open(' '.join(_from), 'rb') as f:
            file_data = f.read()

        total_len = len(input_command) + 8 + file_size.st_size

        length = struct.pack('>Q', total_len)
        cmd_length = struct.pack('>Q', len(input_command))
        data_length = struct.pack('>Q', file_size.st_size)

        # packet = length + cmd_length + data_length + input_command.encode()
        self.sock.sendall(length)
        self.sock.sendall(cmd_length)
        self.sock.sendall(data_length)
        self.sock.sendall(input_command.encode())
        self.sock.sendall(file_data)

    def __auth(self):
        auth = self.sock.recv(1024)
        print(auth.decode())
        self.sock.sendall(UUID.encode())



if __name__ == '__main__':
    import sys
    try:
        host, port = sys.argv[1:]
    except:
        host, port = '', 5458
    finally:
        client = Client()
        client.connect(host,int(port))
    try:
        client.communicate()
    except Exception as E:
        print(E)

