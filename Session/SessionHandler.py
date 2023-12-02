import socket
from typing import Dict, Tuple

import Saveloader
from Saveloader.SaveLoader import JsonSaveLoader, UserData
from users import User, SuperUser


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

    def __init__(self, UserDataHandler: Saveloader.SaveLoader):
        self.__active_sessions: Dict[Tuple, User] = dict()
        self.__UserDataHandler = UserDataHandler

    @property
    def UserDataHandler(self):
        return self.__UserDataHandler

    @property
    def active_sessions(self):
        return self.__active_sessions

    def from_user(self, addr: Tuple) -> User:
        return self.__active_sessions[addr]

    def check_user(self, addr: Tuple, sock: socket.socket):
        if addr not in self.__active_sessions:
            uid: str = self.__recv_user_id(sock)
            if self.__UserDataHandler.is_new_user(uid):
                udata = self.__UserDataHandler.create_user(uid)
            else:
                udata = self.__UserDataHandler.load_user(uid)
            self.__add_user_to_session(addr, sock, udata)

    def __add_user_to_session(self, addr: Tuple, sock: socket.socket, udata: UserData):
        if udata.uid == 'superuser':
            user = SuperUser(DataHandler=self.__UserDataHandler,
                             SessionHandler=self,
                             uid=udata.uid,
                             current_path=udata.current_path,
                             home_path=udata.home_path,
                             sock=sock,
                             addr=addr)
        else:
            user = User(uid=udata.uid,
                        permissions=udata.permissions,
                        current_path=udata.current_path,
                        home_path=udata.home_path,
                        sock=sock,
                        addr=addr)

        self.__active_sessions[addr] = user

    def end_user_session(self, addr: Tuple):
        user = self.__active_sessions[addr]
        udata = UserData(user.uid, user.current_path, user.permissions, user.home_path)
        self.__UserDataHandler.save_user_data(udata)
        self.__active_sessions.pop(addr)

    def __str__(self):
        sessions = 'Active users:\n'
        for snum, session in enumerate(self.__active_sessions.keys(), start=1):
            sessions += f'[{snum}] {session} - {self.__active_sessions[session].uid}\n'
        return sessions

    @staticmethod
    def __recv_user_id(user_socket: socket.socket) -> str:
        user_socket.sendall('id?'.encode())
        user_id = user_socket.recv(128)
        return user_id.decode()
