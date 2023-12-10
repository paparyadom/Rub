import functools
import json
from abc import abstractmethod
from pathlib import Path
from typing import Dict, List, NamedTuple

from utility import walk_around_folder


class UserData(NamedTuple):
    uid: str
    current_path: str
    restrictions: Dict[str, List[str]]
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
    '''
    This class provides saving and loading data in json format
    '''
    def __init__(self, storage_path: str):
        self.__storage_path = Path(storage_path)

    def create_user(self, uid: str) -> UserData:
        '''
        Firstly create new folder named "uid" in self.__storage_path
        Then create udata.json file with user data:
        {"uid": {"restrictions": {"w": [],
                                  "r": [],
                                  "x": []},
        "current_path": by default "self.__storage_path\\uid",
        "home_path": "self.__storage_path\\uid"}
        }

        return namedtuple UserData
        '''
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
        '''
        Loading user data by uid from "self.__storage_path\\uid\\udata.json"
        return namedtuple UserData
        '''
        upath = Path(self.__storage_path, uid, 'udata.json')

        with open(upath, 'r') as f:
            json_udata = json.load(f)

        udata = UserData(uid, json_udata[uid]['current_path'], json_udata[uid]['restrictions'],
                         json_udata[uid]['home_path'])
        return udata

    def save_user_data(self, udata: UserData):
        '''
        Save user`s data in json format in "self.__storage_path\\uid in udata.json

        '''
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
        '''
        Check if connected user is new user or already connected before
        '''
        upath = Path(self.__storage_path, uid)
        return True if not Path.exists(upath) else False

    def get_users(self) -> str:
        '''
        Returns: list of stored users
        '''
        path, folders, files = walk_around_folder(self.__storage_path.__str__(), as_str=False)
        user_list = 'Stored users:\n' + functools.reduce(lambda x, y: f'{x}\n{y}', folders)
        return user_list
