import json
from functools import reduce
from pathlib import Path
from typing import Dict, Any

from UserDataHandle.BaseSaveLoader import BaseSaveLoader, UserData
from utility import walk_around_folder


class JsonSaveLoader(BaseSaveLoader):
    '''
    This class provides saving and loading data in json format
    '''

    def __init__(self, config: Dict[str, Any]):
        self.__config = config
        self.__storage_path = Path(self.__config['saveloader']['storage'])


    async def create_user(self, uid: str) -> UserData:
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
        try:
            Path.mkdir(_path.parents[0])
        except FileExistsError:
            pass

        with open(_path, 'w') as f:
            json.dump(udata, f)

        return UserData(uid, udata[uid]['current_path'], udata[uid]['restrictions'], udata[uid]['home_path'])

    async def load_user(self, uid: str) -> UserData:
        '''
        Loading user data by uid from "self.__storage_path\\uid\\udata.json"
        return namedtuple UserData
        '''
        upath = Path(self.__storage_path, uid, 'udata.json')

        try:
            with open(upath, 'r') as f:
                json_udata = json.load(f)
        except FileNotFoundError:
            return await self.create_user(uid)

        udata = UserData(uid, json_udata[uid]['current_path'], json_udata[uid]['restrictions'],
                         json_udata[uid]['home_path'])
        return udata

    async def save_user_data(self, udata: UserData):
        '''
        Save user`s data in json format in "self.__storage_path\\uid as udata.json

        '''
        upath = Path(self.__storage_path, udata.uid, 'udata.json')
        _udata = {udata.uid: {'restrictions': udata.restrictions,
                              'current_path': udata.current_path,
                              'home_path': udata.home_path
                              }
                  }

        try:
            with open(upath, 'w') as f:
                json.dump(_udata, f)
            print(f'[i] user {udata.uid} was successfully saved')
        except FileNotFoundError:
            print(f'[!] foo udata.json was deleted during the session')

    async def is_new_user(self, uid: str) -> bool:
        '''
        Check if connected user is new user or already connected before
        '''
        upath = Path(self.__storage_path, uid)
        return True if not Path.exists(upath) else False

    async def get_users(self) -> str:
        '''
        Returns: list of stored users
        '''
        path, folders, files = walk_around_folder(self.__storage_path.__str__(), as_str=False)
        users_list = 'Stored users:\n' + reduce(lambda x, y: f'{x}\n{y}', folders)
        return users_list
