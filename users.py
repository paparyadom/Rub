import json
import os
import socket
from typing import Dict, Tuple


class User:
    def __init__(self, uid: str, addr, sock, home_path: str, permissions: Dict = dict()):
        self.__id = uid
        self.__current_path = home_path
        self.__permissions = permissions
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

    @property
    def uid(self):
        return self.__id

    @uid.setter
    def uid(self, uid: int):
        self.__id = uid

    def get_full_info(self):
        info = (f'id = {self.__id}\n'
                f'permissions = {self.__permissions}\n'
                f'current path = {self.__current_path}\n'
                f'address = {self.__addr}\n')
        return info


class UsersHandler:
    '''
    This handler is used for process users:
    <function 'check_user'> - handles incoming user. This function calls in series follow function:
        <function '__recv_user_id'> - getting user id from user
        <function '__is_new_user'> - check if this new user or we already have data about
            <function '__create_user'> - if it is new user - creates user folder and json data
                                        return instance of class User
            <function '__load_user'> - if we already have data about this user - loads user data from
                                        user path in folder 'storage/user id'
                                        return instance of class User with parameters from json file
        <function '__add_user_to_session'> - adds user to  dict  __active_users = Dict[addr, User instance]

    <function 'save_user_data'> - if session is closed - delete user from __active_users and save user data
                                    to json file
     '''
    def __init__(self):
        self.__active_users: Dict[Tuple, User] = dict()
        self.__stored_users = dict()

    def from_user(self, addr: Tuple) -> User:
        return self.__active_users[addr]

    def check_user(self, addr: Tuple, sock: socket.socket):
        uid: str = self.__recv_user_id(sock)
        if self.__is_new_user(uid):
            user = self.__create_user(uid, sock, addr)
        else:
            user = self.__load_user(uid, sock, addr)

        if addr not in self.__active_users:
            self.__add_user_to_session(addr, user)

    def __add_user_to_session(self, addr: Tuple, user: User):
        self.__active_users[addr] = user

    def __create_user(self, uid: str, sock: socket.socket, addr: Tuple) -> User:
        _path = [os.getcwd(), 'storage', uid, 'udata.json']
        user_data = {uid: {'permissions': dict(),
                           'current_path': os.sep.join(_path[:-2])}}

        os.mkdir(os.sep.join(_path[:-1]))
        with open(os.sep.join(_path), 'w') as f:
            json.dump(user_data, f)
        user = User(uid=uid, sock=sock, addr=addr, home_path=os.getcwd(), permissions=dict())
        return user

    @staticmethod
    def __recv_user_id(user_socket: socket.socket) -> str:
        user_socket.sendall('id?'.encode())
        user_id = user_socket.recv(128)
        return user_id.decode()

    def __load_user(self, uid: str, sock: socket.socket, addr: Tuple):
        upath = 'storage' + os.sep + uid + os.sep + 'udata.json'
        with open(upath, 'r') as f:
            user_json_data = json.load(f)
        user = User(uid=uid, sock=sock, addr=addr, home_path=user_json_data[uid]['current_path'],
                    permissions=user_json_data[uid]['permissions'])
        return user

    @staticmethod
    def __is_new_user(uid: str) -> bool:
        return True if not os.path.exists(f'storage{os.sep}{uid}') else False

    def save_user_data(self, addr: Tuple):
        user = self.__active_users[addr]
        upath = 'storage' + os.sep + user.uid + os.sep + 'udata.json'
        udata = {user.uid: {'permissions': user.permissions,
                            'current_path': user.current_path}}
        with open(upath, 'w') as f:
            json.dump(udata, f)
        print(f'user {user.uid} was successfully save')

    def end_user_session(self, addr: Tuple):
        self.save_user_data(addr)
        self.__active_users.pop(addr)
