import socket
from typing import Dict, Tuple

from Saveloader.SaveLoader import JsonSaveLoader, UserData


class User:
    def __init__(self, uid: str, addr, sock, current_path: str,  permissions: Dict = dict(), home_path: str = None, ):
        self.__id = uid
        self.__current_path = current_path
        self.__home_path = home_path
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

    @property
    def home_path(self):
        return self.__home_path

    def get_full_info(self):
        info = (f'id = {self.__id}\n'
                f'permissions = {self.__permissions}\n'
                f'current path = {self.__current_path}\n'
                f'home path = {self.__home_path}\n'
                f'address = {self.__addr}\n')
        return info


class UsersSessionHandler:
    '''
    This handler is used for process users:
    <function 'check_user'> - handles incoming user. This function calls in series follow function:
        <function '__recv_user_id'> - getting user id from user
        <function '__UserDataHandler.is_new_user'> - check if this new user or we already have data about
            <function '__UserDataHandler.create_user'> - if it is new user - creates user folder and json data
                                                         return instance of class User
            <function '__UserDataHandler.load_user'> - if we already have data about this user - loads user data from
                                                       user path in folder 'storage/user id'
                                                       return instance of class User with parameters from json file
        <function '__add_user_to_session'> - adds user to  dict  __active_users = Dict[addr, User instance]

    <function '__UserDataHandler.save_user_data'> - if session is closed - delete user from __active_users and save user data
                                                    to json file
     '''

    def __init__(self):
        self.__active_users: Dict[Tuple, User] = dict()
        self.__UserDataHandler = JsonSaveLoader('storage')

    def from_user(self, addr: Tuple) -> User:
        return self.__active_users[addr]

    def check_user(self, addr: Tuple, sock: socket.socket):
        if addr not in self.__active_users:
            uid: str = self.__recv_user_id(sock)
            if self.__UserDataHandler.is_new_user(uid):
                udata = self.__UserDataHandler.create_user(uid)
            else:
                udata = self.__UserDataHandler.load_user(uid)
            self.__add_user_to_session(addr, sock, udata)

    def __add_user_to_session(self, addr: Tuple, sock: socket.socket, udata: UserData):
        self.__active_users[addr] = User(uid=udata.uid,
                                         permissions=udata.permissions,
                                         current_path=udata.current_path,
                                         home_path=udata.home_path,
                                         sock=sock,
                                         addr=addr)

    @staticmethod
    def __recv_user_id(user_socket: socket.socket) -> str:
        user_socket.sendall('id?'.encode())
        user_id = user_socket.recv(128)
        return user_id.decode()

    def end_user_session(self, addr: Tuple):
        user = self.__active_users[addr]
        udata = UserData(user.uid, user.current_path, user.permissions, user.home_path)
        self.__UserDataHandler.save_user_data(udata)
        self.__active_users.pop(addr)
