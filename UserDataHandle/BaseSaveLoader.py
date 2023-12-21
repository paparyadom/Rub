from abc import abstractmethod
from typing import Dict, List, NamedTuple


class UserData(NamedTuple):
    uid: str
    current_path: str
    permissions: Dict[str, List[str]]
    home_path: str


class BaseSaveLoader:
    @abstractmethod
    async def create_user(self, uid: str) -> UserData:
        pass

    @abstractmethod
    async def load_user(self, uid: str) -> UserData:
        pass

    @abstractmethod
    async def save_user_data(self, udata: UserData):
        pass

    @abstractmethod
    async def is_new_user(self, uid: str) -> bool:
        pass

    @abstractmethod
    async def get_users(self) -> str:
        pass
