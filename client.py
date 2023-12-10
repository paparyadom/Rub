from Protocols.BaseProtocol import *

# UUID = '628c93f2-8d44-11ee-9706-07b2e7b92ea1'
UUID = 'superuser'
# UUID = 'foo'
# UUID = 'bar'

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
    def printer(data):
        if len(data) == 0:
            print(f'[r]\nno data')
        else:
            try:
                print(f'[r]\n{data.decode()}')
            except:
                print(f'[r]\n{data}')

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
                elif request.startswith('send'):
                    try:
                        self.__proto.file_send_request(csock=self.sock, request=request)
                    except Exception as E:
                        print(E)
                        input()
                else:
                    self.__proto.send_request(csock=self.sock, request=request)
                try:
                    data = self.__proto.receive_reply(self.sock)
                except Exception as e:
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

    try:
        host, port = sys.argv[1:]
    except:
        host, port = '', 5454
    finally:
        client = Client(proto=SimpleProto())
        client.connect('localhost', 5454)
    try:
        client.communicate()
    except Exception as E:
        print(E)
