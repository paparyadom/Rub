import json
from functools import reduce
from pathlib import Path
from typing import Dict, Any

from UserDataHandle.BaseSaveLoader import BaseSaveLoader, UserData
from utility import walk_around_folder, trim_path


class JsonSaveLoader(BaseSaveLoader):
    '''
    This class provides saving and loading data in json format
    '''

    def __init__(self, config: Dict[str, Any]):
        self.__config = config
        self.__storage_path = Path(Path.cwd(), self.__config['storage'])
        self.__json_config_path = Path(Path.cwd(), 'Users')

        if not Path('Users').exists():
            Path('Users').mkdir()

    async def create_user(self, uid: str) -> UserData:
        '''
        Firstly create new folder named "uid" in self.__storage_path
        Then create udata.json file with user data:
        {"uid": {"permissions": {"w": [],
                                  "r": [],
                                  "x": []},
        "current_path": by default "self.__storage_path\\uid",
        "home_path": "self.__storage_path\\uid"}
        }

        return namedtuple UserData
        '''
        spath: Path = Path(Path.cwd(), self.__storage_path, uid)  #  path to user storage
        upath: Path = Path(self.__json_config_path, f'{uid}.json')  #  path to user json config
        udata = {uid: {'permissions': {'w': [spath.__str__()], 'r': [spath.__str__()], 'x': [spath.__str__()]},
                       'current_path': spath.__str__(),
                       'home_path': spath.__str__()
                       }
                 }
        try:
            Path.mkdir(spath)
        except FileExistsError:
            pass

        with open(upath, 'w') as f:
            json.dump(udata, f)

        return UserData(uid, udata[uid]['current_path'], udata[uid]['permissions'], udata[uid]['home_path'])

    async def load_user(self, uid: str) -> UserData:
        '''
        Loading user data by uid from "self.__storage_path\\uid\\udata.json"
        return namedtuple UserData
        '''
        # upath = Path(self.__storage_path, uid, 'udata.json')
        upath: Path = Path(self.__json_config_path, f'{uid}.json')  # path to json config

        try:
            with open(upath, 'r') as f:
                json_udata = json.load(f)
        except FileNotFoundError:
            return await self.create_user(uid)

        udata = UserData(uid, json_udata[uid]['current_path'], json_udata[uid]['permissions'],
                         json_udata[uid]['home_path'])
        return udata

    async def save_user_data(self, udata: UserData):
        '''
        Save user`s data in json format in "self.__storage_path\\uid as udata.json

        '''
        upath: Path = Path(self.__json_config_path, f'{udata.uid}.json')  # path to json config
        _udata = {udata.uid: {'permissions': udata.permissions,
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
        spath: Path = Path( self.__storage_path, uid)  #  path to user storage
        upath: Path = Path(self.__json_config_path, f'{uid}.json')  #  path to user json config
        return True if not Path.exists(upath) and Path.exists(spath) else False

    async def get_users(self) -> str:
        '''
        Returns: list of stored users
        '''
        path, folders, files = walk_around_folder(self.__json_config_path.__str__(), as_str=False, trimmed_path=None)
        users_list = 'Stored users:\n' + reduce(lambda x, y: f'{x}\n{y}', files)
        return users_list
