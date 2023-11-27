import os
from typing import Dict, Tuple
import socket
from uuid import uuid1


class User:
    def __init__(self, user_id: int, addr, sock):
        self.__id = user_id
        self.__sock = sock
        self.__addr = addr
        self.__current_path = os.getcwd()

    @property
    def current_path(self):
        return self.__current_path

    @current_path.setter
    def current_path(self, path: str):
        print('path was changed')
        self.__current_path = path

    @property
    def sock(self):
        return self.__sock

    @property
    def addr(self):
        return self.__addr


class UsersHandler:
    def __init__(self):
        self.__active_users: Dict[Tuple, User] = dict()
        self.__authenticated = set()

    # def check_auth(self, sock) -> bool:
    #     return True if sock in self.authenticated else False
    #
    # def get_user(self, userName: str) -> User:
    #     if userName not in USERS:
    #         self._add_user(userName)
    #     return USERS[userName]

    def from_user(self, addr: Tuple) -> User:
        return self.__active_users[addr]

    def check_user(self, addr: Tuple) -> bool:
        if addr in self.__active_users:
            return True
        return False

    def add_user(self, addr: Tuple, sock: socket.socket):
        self.__active_users[addr] = User(user_id=uuid1, addr=addr, sock=sock)
