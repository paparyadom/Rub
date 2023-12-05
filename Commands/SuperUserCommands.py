from Commands.UserCommands import UserCommands
from users import SuperUser
from Saveloader.SaveLoader import UserData
from typing import Dict


class SuperUserCommands(UserCommands):
    @staticmethod
    def acts(user: SuperUser, packet=None) -> bytes:
        result = user.SessionHandler.__str__()
        return f'{result}\n{user.DataHandler.get_users()}'.encode()

    @staticmethod
    def uinf(user: SuperUser, packet=None) -> bytes:
        target_uid, *other = packet.cmd_tail
        user_info = f'User "{target_uid}" info:\n'

        for _user in user.SessionHandler.active_sessions.values():
            if _user.uid == target_uid:
                for key, value in _user.__dict__.items():
                    user_info += f'{key} - {value}\n'
                return f'"{user_info}"'.encode()
        try:
            udata: UserData = user.DataHandler.load_user(target_uid)
        except:
            return f'[!] no such user "{target_uid}"'.encode()
        for key, value in udata._asdict().items():
            user_info += f'{key} - {value}\n'
        return f'{user_info}'.encode()

    @staticmethod
    def setr(user: SuperUser, packet):
        '''
        setr - add restrictions to user
        '''

        def __add_restricts(user_current_restrictions: Dict, modes: str, *restrictions):
            from copy import copy
            user_restrictions = copy(user_current_restrictions)
            for mode in modes.strip('-'):
                for perm in restrictions:
                    if perm not in user_restrictions[mode]:
                        user_restrictions[mode].append(perm)
            return user_restrictions

        target_uid, modes, *restrictions = packet.cmd_tail

        for _user in user.SessionHandler.active_sessions.values():
            if _user.uid == target_uid:
                return f'"{target_uid}" restrictions was changed to "{__add_restricts(_user.restrictions, modes, *restrictions)}"'.encode()

        try:
            udata: UserData = user.DataHandler.load_user(target_uid)
            user.DataHandler.save_user_data(UserData(uid=udata.uid,
                                                     current_path=udata.current_path,
                                                     home_path=udata.home_path,
                                                     restrictions=__add_restricts(udata.restrictions, modes,
                                                                                  *restrictions)
                                                     )
                                            )

        except Exception as E:
            return f'[!] something went wrong {E}'.encode()
        return str(udata).encode()

    @staticmethod
    def delr(user: SuperUser, packet):
        '''
        delr - delete restriction from user
        '''

        def __del_restricts(user_current_restrictions: Dict, modes: str, *restrictions):
            from copy import copy
            user_restrictions = copy(user_current_restrictions)
            for mode in str(modes.strip('-')):
                for perm in restrictions:
                    try:
                        user_restrictions[mode].remove(perm)
                    except Exception as E:
                        print(E)
            return user_restrictions

        target_uid, modes, *restrictions = packet.cmd_tail

        for _user in user.SessionHandler.active_sessions.values():
            if _user.uid == target_uid:
                return f'"{target_uid}" restrictions was changed to "{__del_restricts(_user.restrictions, modes, *restrictions)}"'.encode()

        try:
            udata: UserData = user.DataHandler.load_user(target_uid)
            user.DataHandler.save_user_data(UserData(uid=udata.uid,
                                                     current_path=udata.current_path,
                                                     home_path=udata.home_path,
                                                     restrictions=__del_restricts(udata.restrictions, modes,
                                                                                  *restrictions)
                                                     )
                                            )
        except Exception as E:
            return f'[!] something went wrong {E}'.encode()
        return str(udata).encode()
