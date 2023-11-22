#
# def send_command(command: str, sock: socket.socket):
#     length: bytes = struct.pack('>Q', len(command))
#     sock.sendall(length)
#     sock.sendall(command.encode())
#
#
# if __name__ == "__main__":
#     print('starting')
#     is_started = False
#     while True:
#         with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
#             sock.connect((HOST, PORT))
#             print(f'[i] connected to {HOST}:{PORT}')
#             while True:
#                 # Input
#                 command = input("[>] type command:")
#                 if not command:
#                     command = 'nop'
#                 if command == "exit":
#                     send_command(command, sock)
#                     print("[x] close by client")
#                     break
#                 # Send
#                 send_command(command, sock)
#                 # Receive
#                 try:
#                     rdata = sock.recv(8)
#                     (length,) = struct.unpack('>Q', rdata)
#                     data = b''
#                     to_read = length - len(data)
#                     data += sock.recv(4096 if to_read > 4096 else to_read)
#                 except Exception as e:
#                     print(e)
#
#                 print(f'[r]\n{data.decode("utf-8")}')
#                 if not data:
#                     print("[x] closed by server")
#                     break
#             sock.close()
#             print("[x] client disconnected")
#             break


#
# activeConnections: Dict[Tuple, User] = dict()
#
#
# def check_user(addr: Tuple) -> bool:
#     if addr in activeConnections:
#         return True
#     return False
#
#
# def add_user(addr: Tuple, sock: socket.socket):
#     activeConnections[addr] = User(userName=uuid1, addr=addr, sock=sock)
#
#
# def handle(user: User):
#     try:
#         rdata = user.sock.recv(8)
#         (length,) = struct.unpack('>Q', rdata)
#         rdata = b''
#         while len(rdata) < length:
#             to_read = length - len(rdata)
#             print(to_read)
#             rdata += user.sock.recv(
#                 4096 if to_read > 4096 else to_read)
#     except ConnectionError:
#         print(f"Client suddenly closed while receiving")
#         return InputsHandler.close_connection(user.sock)
#     print(f"Received {rdata} from: {user.addr} length: {length}")
#     if not rdata:
#         print("Disconnected by", user.addr)
#         return InputsHandler.close_connection(user.sock)
#
#     answer = InputsHandler.handle_input(user, rdata)
#     print(f"Send: {answer} to: {user.addr}")
#     try:
#         length: bytes = struct.pack('>Q', len(answer))
#         user.sock.sendall(length)
#         user.sock.sendall(answer)
#     except ConnectionError:
#         print(f"Client suddenly closed, cannot send")
#         return InputsHandler.close_connection(user.sock)
#     return True

#
# HOST, PORT = "", 5458
# if __name__ == "__main__":
#     USERS: Set = set()
#     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serv_sock:
#         serv_sock.bind((HOST, PORT))
#         serv_sock.listen(10)
#         inputs = [serv_sock]
#         outputs = []
#         while True:
#             print("Waiting for connections or data...")
#             readable, writeable, exceptional = select.select(inputs, outputs, inputs)
#             for sock in readable:
#                 if sock is serv_sock:
#                     sock, addr = serv_sock.accept()  # Should be ready
#                     # sock.setblocking(False)
#                     if not check_user(addr):
#                         add_user(addr, sock)
#                     print(f'Connected by {addr}')
#                     inputs.append(sock)
#                 else:
#                     addr = sock.getpeername()
#                     if not handle(activeConnections[addr]):
#                         inputs.remove(sock)
#                         print(f'{addr} was removed from inputs')
#                         if sock in outputs:
#                             outputs.remove(sock)
#                             print(f'{addr} was removed from outputs')
#                         sock.close()
#

from typing import Generator

def read_in_chunks(path_to_file, chunk_size=2048):
    with open(path_to_file, 'r') as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            yield data


def somefunc(path_to_file):
    return read_in_chunks(path_to_file)

from types import  GeneratorType

data = somefunc('task.txt')

if isinstance(data, GeneratorType):
    print('yes')
while data:
    print(next(data))
