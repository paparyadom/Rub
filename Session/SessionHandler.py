import asyncio
from typing import Dict, NamedTuple, Tuple

from UserDataHandle.BaseSaveLoader import BaseSaveLoader, UserData
from users import User, SuperUser


class URW(NamedTuple):
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter


class UsersSessionHandler:
    '''
    This handler is used for process users:
    <function 'check_user'> - handle incoming user. This function calls in series follow function:
        <function '__UserDataHandler.is_new_user'> - check if this new user or we already have data about
            <function '__UserDataHandler.create_user'> - if it is new user - creates user folder and json data
                                                         return instance of class User
            <function '__UserDataHandler.load_user'> - if we already have data about this user - loads user data from
                                                       user path in folder 'storage/user id'
                                                       return instance of class User with parameters from json file
        <function '__add_user_to_session'> - adds user to  dict  __active_users = Dict[addr, User object]

    <function '__UserDataHandler.save_user_data'> - if session is closed - delete user from __active_users and save user data
                                                    to json file
     '''

    def __init__(self, UserDataHandler: BaseSaveLoader, super_users=None):
        if super_users is None:
            super_users = set()
        self.__active_sessions: Dict[Tuple[str], User] = dict()
        self.__UserDataHandler = UserDataHandler
        self.__super_users = super_users

    @property
    def UserDataHandler(self):
        return self.__UserDataHandler

    @property
    def active_sessions(self):
        return self.__active_sessions

    def from_user(self, addr: Tuple) -> User:
        '''

        Args:
            addr: user address and port

        Returns: User object from self.__active_sessions[addr]

        '''
        return self.__active_sessions[addr]

    async def check_user(self, reader, writer, uid: str):
        '''
        Read Class doc
        '''
        addr = writer.get_extra_info("peername")
        if addr not in self.__active_sessions:
            if await self.__UserDataHandler.is_new_user(uid):
                udata = await self.__UserDataHandler.create_user(uid)
            else:
                udata = await self.__UserDataHandler.load_user(uid)
            self.__add_user_to_session(addr, reader, writer, udata)

    def __add_user_to_session(self, addr: Tuple, reader, writer, udata: UserData):
        '''
        Add User or SuperUser object (depends on uid) to session
        '''
        if udata.uid in self.__super_users:
            user = SuperUser(DataHandler=self.__UserDataHandler,
                             SessionHandler=self,
                             permissions=udata.permissions,
                             uid=udata.uid,
                             current_path=udata.current_path,
                             home_path=udata.home_path,
                             sock=URW(reader=reader, writer=writer),
                             addr=addr)
        else:
            user = User(uid=udata.uid,
                        permissions=udata.permissions,
                        current_path=udata.current_path,
                        home_path=udata.home_path,
                        sock=URW(reader=reader, writer=writer),
                        addr=addr)

        self.__active_sessions[addr] = user

    async def end_user_session(self, addr: Tuple):
        '''
        In the end of session:
        - save user data
        - delete user from session
        '''
        user = self.__active_sessions[addr]
        udata = UserData(user.uid, user.current_path, user.permissions, user.home_path)
        await self.__UserDataHandler.save_user_data(udata)
        user.sock.writer.close()
        self.__active_sessions.pop(addr)

    def __str__(self):
        sessions = 'Active users:\n'
        for snum, session in enumerate(self.__active_sessions.keys(), start=1):
            sessions += f'[{snum}] {session} - {self.__active_sessions[session].uid}\n'
        return sessions
