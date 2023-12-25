from Protocols.BaseProtocol import *


class Client:
    def __init__(self, proto: BaseProtocol):
        self.host = None
        self.port = None
        self.sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
        self.__proto = proto

    def connect(self, host: str, port: int):
        self.sock.connect((host, port))
        self.host, self.port = host, port
        self.connected = True

    @staticmethod
    def printer(data:bytes):
        if len(data) == 0:
            print(f'...>> no data')
        else:
            try:
                print(f'...>> {data.decode()}')
            except:
                print(f'...>> {data}')

    def end_connection(self):
        self.sock.close()
        self.connected = False
        print("[x] client disconnected")

    def communicate(self):
        while self.connected:
            print(f'[i] connected to {self.host}:{self.port}')
            self.__auth()
            self.sock.settimeout(.05)


            while True:
                request = input("[...] type:")
                if not request:
                    request = 'nop'
                if request.startswith('exit'):
                    self.__proto.send_request(csock=self.sock, request=request)
                    break
                elif request.startswith(('rawsend', 'send')):
                    try:
                        # self.sock.settimeout(1)
                        self.__proto.file_send_request(csock=self.sock, request=request)
                    except Exception as E:
                        print(E)
                        input()
                else:
                    self.__proto.send_request(csock=self.sock, request=request)
                try:
                    data = self.__proto.receive_reply(self.sock)
                except Exception as e:
                    data = b'no data'
                    print(e)
                Client.printer(data)
            self.end_connection()
            break

    def __auth(self):
        auth = self.sock.recv(4)
        print(auth.decode())
        self.sock.sendall(UUID.encode())


if __name__ == '__main__':
    import sys
    Protocols = {'simple': SimpleProto,
                 'tcd8': TCD8}

    try:
        host, port, proto, UUID = sys.argv[1:]
    except:
        host, port, proto, UUID = 'localhost', 3333, 'simple', 'test'
    try:
        client = Client(proto=Protocols[proto]())
        client.connect(host, int(port))
        client.communicate()
    except Exception as E:
        print('No response from server', {E})
