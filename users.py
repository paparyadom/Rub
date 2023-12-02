import socket
from typing import Dict, Tuple, List

import Saveloader
from Saveloader.SaveLoader import JsonSaveLoader
# from Session import SessionHandler


class User:
    def __init__(self, uid: str, addr: Tuple, sock:socket.socket, current_path: str, permissions: Dict = {'w':[], 'r':[]}, home_path: str = None, commands = None):
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


class SuperUser(User):
    def __init__(self, DataHandler: Saveloader.SaveLoader, SessionHandler, **kwargs):
        super().__init__(**kwargs)
        self._DataHandler = DataHandler
        self._SessionHandler = SessionHandler
        self.permissions = {'godmode'}


    @property
    def DataHandler(self):
        return self._DataHandler

    @property
    def SessionHandler(self):
        return self._SessionHandler
