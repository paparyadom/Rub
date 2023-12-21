from functools import reduce
from pathlib import Path
from typing import Any, Dict

from motor.motor_asyncio import AsyncIOMotorClient

from UserDataHandle.BaseSaveLoader import BaseSaveLoader, UserData


class MongoSaveLoader(BaseSaveLoader):
    def __init__(self, config: Dict[str, Any]):
        self.__storage_path = None
        self.__cfg = config
        self.__client: AsyncIOMotorClient = None
        self.__collection = None

        self.configure(self.__cfg['connection'],
                       self.__cfg['db']['database'],
                       self.__cfg['db']['collection'],
                       self.__cfg['storage'])

    async def create_user(self, uid: str) -> UserData:
        spath: Path = Path(Path.cwd(), self.__storage_path, uid)
        udata = {"_id": uid,
                 "permissions": {'w': [spath.__str__()], 'r': [spath.__str__()], 'x': [spath.__str__()]},
                 "current_path": spath.__str__(),
                 "home_path": spath.__str__()}

        try:
            Path.mkdir(spath)
        except FileExistsError:
            pass
        await self.__collection.insert_one(udata)

        return UserData(uid, udata['current_path'], udata['permissions'], udata['home_path'])

    async def load_user(self, uid: str) -> UserData:
        db_data = await self.__collection.find_one({'_id': uid})

        udata = UserData(uid, db_data['current_path'], db_data['permissions'], db_data['home_path'])
        return udata

    async def save_user_data(self, udata: UserData):
        db_data = {'_id': udata.uid,
                   'permissions': udata.restrictions,
                   'current_path': udata.current_path,
                   'home_path': udata.home_path}

        try:
            await self.__collection.replace_one({'_id': udata.uid}, db_data)
            print(f'[i] user {udata.uid} was successfully saved')
        except Exception as E:
            print(f'something went wrong {E}')

    async def is_new_user(self, uid: str) -> bool:
        _is = await self.__collection.find_one({'_id': uid})
        return True if _is is None else False

    async def get_users(self) -> str:
        '''
        Returns: list of stored users
        '''
        users = await self.__collection.find({}, {'_id': 1}).to_list(length=None)
        users = [user for dcts in users for _, user in dcts.items()]
        users_list = 'Stored users:\n' + reduce(lambda x, y: f'{x}\n{y}', users)
        return users_list

    def configure(self, connection: Dict[str, Any], database: str, collection: str, storage_path: str):
        self.__client = AsyncIOMotorClient(self.__mongo_uri(**connection), uuidRepresentation='standard')
        self.__collection = self.__client[database][collection]
        self.__storage_path = Path(Path.cwd(), storage_path)

    def __mongo_uri(self, host: str, port: int, user: str, password: str, auth = False) -> str:

        return f'mongodb://{user}:{password}@{host}:{port}' if auth else f'mongodb://{host}:{port}'
