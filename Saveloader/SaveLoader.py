import functools
import json
from abc import abstractmethod
from pathlib import Path
from typing import Dict, NamedTuple

from utility import walk_around_folder


class UserData(NamedTuple):
    uid: str
    current_path: str
    restrictions: Dict
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
        self.__storage_path = Path(storage_path)

    def create_user(self, uid: str) -> UserData:
        _path: Path = Path(Path.cwd(), self.__storage_path, uid, 'udata.json')
        udata = {uid: {'restrictions': {'w': [], 'r': [], 'x': []},
                       'current_path': _path.parents[0].__str__(),
                       'home_path': _path.parents[0].__str__()
                       }
                 }
        Path.mkdir(_path.parents[0])

        with open(_path, 'w') as f:
            json.dump(udata, f)

        return UserData(uid, udata[uid]['current_path'], udata[uid]['restrictions'], udata[uid]['home_path'])

    def load_user(self, uid: str) -> UserData:
        upath = Path(self.__storage_path, uid, 'udata.json')

        with open(upath, 'r') as f:
            json_udata = json.load(f)

        udata = UserData(uid, json_udata[uid]['current_path'], json_udata[uid]['restrictions'],
                         json_udata[uid]['home_path'])
        return udata

    def save_user_data(self, udata: UserData):
        upath = Path(self.__storage_path, udata.uid, 'udata.json')
        _udata = {udata.uid: {'restrictions': udata.restrictions,
                              'current_path': udata.current_path,
                              'home_path': udata.home_path
                              }
                  }

        with open(upath, 'w') as f:
            json.dump(_udata, f)
        print(f'[i] user {udata.uid} was successfully saved')

    def is_new_user(self, uid: str) -> bool:
        upath = Path(self.__storage_path, uid)
        return True if not Path.exists(upath) else False

    def get_users(self) -> str:
        path, folders, files = walk_around_folder(self.__storage_path.__str__(), as_str=False)
        user_list = 'Stored users:\n' + functools.reduce(lambda x, y: f'{x}\n{y}', folders)
        return user_list
