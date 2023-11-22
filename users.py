import os
from typing import Dict, Tuple
import socket
from uuid import uuid1


class User:
    def __init__(self, userName, addr, sock):
        self.name = userName
        self.sock = sock
        self.addr = addr
        self.current_path = os.getcwd()

    def set_current_path(self, path: str):
        self.current_path = path


class UsersHandler:
    def __init__(self):
        self.active_users: Dict[Tuple, User] = dict()
        self.authenticated = set()

    # def check_auth(self, sock) -> bool:
    #     return True if sock in self.authenticated else False
    #
    # def get_user(self, userName: str) -> User:
    #     if userName not in USERS:
    #         self._add_user(userName)
    #     return USERS[userName]

    def from_user(self, addr: Tuple) -> User:
        return self.active_users[addr]

    def add_user(self, user_name: str):
        self.active_users.update({user_name: User(user_name)})

    def check_user(self, addr: Tuple) -> bool:
        if addr in self.active_users:
            return True
        return False

    def add_user(self, addr: Tuple, sock: socket.socket):
        self.active_users[addr] = User(userName=uuid1, addr=addr, sock=sock)
