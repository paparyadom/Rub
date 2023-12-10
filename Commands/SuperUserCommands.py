from typing import Dict, List

from Commands.UserCommands import Packet, UserCommands
from Saveloader.SaveLoader import UserData
from users import SuperUser


class SuperUserCommands(UserCommands):
    @staticmethod
    def acts(packet: Packet) -> bytes:
        '''
        acts - display list of active sessions with (IP , port) - username and
                stored users.

                e.g.:
                Active users:
                [1] ('127.0.0.1', 62393) - superuser
                [2] ('127.0.0.1', 62394) - foo

                Stored users:
                bar
                foo
                superuser
        '''
        return f'{packet.user.SessionHandler.__str__()}\n{packet.user.DataHandler.get_users()}'.encode()

    @staticmethod
    def uinf(packet: Packet) -> bytes:
        '''
        uinf - display information about concrete user

                e.g.:
                User "bar" info:
                uid - bar
                current_path - D:\current path
                restrictions - {'w': [], 'r': [], 'x': []}
                home_path - D:\programming\DEV\Filey\storage\bar
        '''
        if not packet.cmd_tail:
            return f"[!] empty username".encode()

        target_uid, *_ = packet.cmd_tail
        user_info = f'User "{target_uid}" info:\n'
        for _user in packet.user.SessionHandler.active_sessions.values():
            if _user.uid == target_uid:
                for key, value in _user.__dict__.items():
                    user_info += f'{key} - {value}\n'
                return f'"{user_info}"'.encode()
        try:
            udata: UserData = packet.user.DataHandler.load_user(target_uid)
        except:
            return f'[!] no such user "{target_uid}"'.encode()
        for key, value in udata._asdict().items():
            user_info += f'{key} - {value}\n'
        return f'{user_info}'.encode()

    @staticmethod
    def setr(packet: Packet) -> bytes:
        '''
        setr - add restrictions to user. (e.g. setr foo -rwx D:\folder)
        '''

        def __add_restricts(user_current_restrictions: Dict[str, List[str]], modes: str, *restrictions: str) -> Dict[
            str, List[str]]:
            from copy import copy

            user_restrictions = copy(user_current_restrictions)
            for mode in modes.strip('-'):
                for restr in restrictions:
                    if restr not in user_restrictions[mode]:
                        user_restrictions[mode].append(restr)
            return user_restrictions

        target_uid, modes, *restrictions = packet.cmd_tail

        # firstly check if user is now online to add restrictions in current sessions
        # if user is offline - download user json data file and add restriction in
        for _user in packet.user.SessionHandler.active_sessions.values():
            if _user.uid == target_uid:
                _user.restrictions = __add_restricts(_user.restrictions, modes, *restrictions)
                return f'"{target_uid}" restrictions was changed to "{_user.restrictions}"'.encode()

        try:
            udata: UserData = packet.user.DataHandler.load_user(target_uid)
            packet.user.DataHandler.save_user_data(UserData(uid=udata.uid,
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
    def delr(packet: Packet) -> bytes:
        '''
        delr - delete users`s restrictions (e.g. delr foo -rwx D:\folder)
        '''

        def __del_restricts(user_current_restrictions: Dict[str, List[str]], modes: str, *restrictions) -> Dict[
            str, List[str]]:
            from copy import copy
            user_restrictions = copy(user_current_restrictions)
            for mode in str(modes.strip('-')):
                for restr in restrictions:
                    try:
                        user_restrictions[mode].remove(restr)
                    except Exception as E:
                        print(E)
            return user_restrictions

        target_uid, modes, *restrictions = packet.cmd_tail

        # firstly check if user is now online to delete restrictions in current sessions
        # if user is offline - download user json data file and delete restriction in
        for _user in packet.user.SessionHandler.active_sessions.values():
            if _user.uid == target_uid:
                _user.restrictions = __del_restricts(_user.restrictions, modes, *restrictions)
                return f'"{target_uid}" restrictions was changed to "{_user.restrictions}"'.encode()

        try:
            udata: UserData = packet.user.DataHandler.load_user(target_uid)
            packet.user.DataHandler.save_user_data(UserData(uid=udata.uid,
                                                     current_path=udata.current_path,
                                                     home_path=udata.home_path,
                                                     restrictions=__del_restricts(udata.restrictions, modes,
                                                                                  *restrictions)
                                                     )
                                            )
        except Exception as E:
            return f'[!] something went wrong {E}'.encode()
        return str(udata).encode()
