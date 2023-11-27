import os
from typing import Dict, Tuple
import socket
from uuid import uuid1


class User:
    def __init__(self, uid: str, addr, sock):
        self.__id = uid
        self.__current_path = os.getcwd()
        self.__permissions = None
        self.__sock = sock
        self.__addr = addr

    @property
    def current_path(self):
        return self.__current_path

    @current_path.setter
    def current_path(self, path: str):
        print('path was changed')
        self.__current_path = path

    @property
    def permissions(self):
        return self.__permissions

    @permissions.setter
    def permissions(self, permissions):
        self.__permissions = permissions

    @property
    def sock(self):
        return self.__sock

    @property
    def addr(self):
        return self.__addr


class UsersHandler:
    def __init__(self):
        self.__active_users: Dict[str, User] = dict()
        self.__stored_users = dict()

    def from_user(self, addr: Tuple) -> User:
        return self.__active_users[addr]

    def check_user(self, addr: Tuple, sock: socket.socket):
        uid = self.__get_user_id(sock)
        if addr not in self.__active_users:
            self.__add_user(uid, addr, sock)

    def __add_user(self, uid: str, addr: Tuple, sock: socket.socket):
        self.__active_users[addr] = User(uid=uid, addr=addr, sock=sock)

    @staticmethod
    def __get_user_id(user_socket: socket.socket) -> str:
        user_socket.sendall('id?'.encode())
        user_id = user_socket.recv(1024)
        return user_id

    def __load_users(self):
        ...
