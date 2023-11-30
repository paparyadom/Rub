import functools
import json
import os
from abc import abstractmethod
from typing import Dict, NamedTuple

from utility import walk_around_folder


class UserData(NamedTuple):
    uid: str
    current_path: str
    permissions: Dict
    home_path: str


class SaveLoader:
    @abstractmethod
    def create_user(self, uid: str) -> UserData:
        pass

    @abstractmethod
    def load_user(self, uid: str) -> UserData:
        pass

    @abstractmethod
    def save_user_data(self, udata: UserData):
        pass


class JsonSaveLoader(SaveLoader):
    def __init__(self, storage_path: str):
        self.__storage_path = storage_path
        self.__sep = os.sep

    def create_user(self, uid: str) -> UserData:
        _path = [os.getcwd(), self.__storage_path, uid, 'udata.json']
        udata = {uid: {'permissions': dict(),
                       'current_path': self.__sep.join(_path[:-1]),
                       'home_path': self.__sep.join(_path[:-1])
                       }
                 }

        os.mkdir(self.__sep.join(_path[:-1]))

        with open(self.__sep.join(_path), 'w') as f:
            json.dump(udata, f)

        return UserData(uid, udata[uid]['current_path'], dict(), udata[uid]['home_path'])

    def load_user(self, uid: str) -> UserData:
        upath = self.__sep.join((self.__storage_path, uid, 'udata.json'))

        with open(upath, 'r') as f:
            json_udata = json.load(f)

        udata = UserData(uid, json_udata[uid]['current_path'], json_udata[uid]['permissions'],
                         json_udata[uid]['home_path'])
        return udata

    def save_user_data(self, udata: UserData):
        upath = self.__sep.join((self.__storage_path, udata.uid, 'udata.json'))
        _udata = {udata.uid: {'permissions': udata.permissions,
                              'current_path': udata.current_path,
                              'home_path': udata.home_path
                              }
                  }

        with open(upath, 'w') as f:
            json.dump(_udata, f)
        print(f'[i] user {udata.uid} was successfully saved')

    @staticmethod
    def is_new_user(uid: str) -> bool:
        return True if not os.path.exists(f'storage{os.sep}{uid}') else False

    def get_users(self) -> str:
        path, folders, files = walk_around_folder(self.__storage_path, as_str=False)
        user_list = 'Stored users:\n' + functools.reduce(lambda x, y: f'{x}\n{y}', folders)
        return user_list

