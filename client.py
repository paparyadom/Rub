import socket
import struct

HOST = "localhost"  # The remote host
PORT = 5458  # The same port as used by the servers
IS_RECONNECT_ENABLED = False


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
            while True:
                command = input("[>] type command:")
                if not command:
                    command = 'nop'
                if command == "exit":
                    self.send_request(command, self.sock)
                    print("[x] close by client")
                    break
                # Send
                self.send_request(command, self.sock)
                # Receive
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

    def send_request(self, command: str, sock: socket.socket):
        length: bytes = struct.pack('>Q', len(command))
        self.sock.sendall(length)
        self.sock.sendall(command.encode())


if __name__ == '__main__':
    client = Client()
    client.connect('localhost', 5458)
    client.communicate()
