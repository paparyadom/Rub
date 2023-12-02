from Commands.UserCommands import UserCommands
from users import SuperUser
from Saveloader.SaveLoader import UserData


class SuperUserCommands(UserCommands):
    @staticmethod
    def acts(user: SuperUser, packet=None) -> bytes:
        result = user.SessionHandler.__str__()
        return f'{result}\n{user.DataHandler.get_users()}'.encode()

    @staticmethod
    def uinf(user: SuperUser, packet=None) -> bytes:
        target_uid, *other = packet.cmd_tail
        for _user in user.SessionHandler.active_sessions.values():
            if _user.uid == target_uid:
                return f'User {target_uid} info:\n{_user}'.encode()
        try:
            udata: UserData = user.DataHandler.load_user(target_uid)
        except:
            return f'[!] no such user "{target_uid}"'.encode()
        return f'{target_uid} info {udata}'.encode()

    @staticmethod
    def addp(user: SuperUser, packet):
        '''
        addp - add permission to user
        '''

        target_uid, *perms = packet.cmd_tail

        for _user in user.SessionHandler.active_sessions.values():
            if _user.uid == target_uid:
                for perm in perms:
                    _user.permissions['w'].append(perm)
                return f'{target_uid} permissions was changed to {_user.permissions}'.encode()

        udata: UserData = user.DataHandler.load_user(target_uid)
        current_perms = udata.permissions
        try:
            for perm in perms:
                current_perms['w'].append(perm)
            user.DataHandler.save_user_data(UserData(uid=udata.uid,
                                                     current_path=udata.current_path,
                                                     home_path=udata.home_path,
                                                     permissions=current_perms))
        except Exception as E:
            return f'[!] something went wrong {E}'.encode()
        return str(udata).encode()

    @staticmethod
    def delp(user: SuperUser, packet):
        '''
        delp - delete permissions from user
        '''
        target_uid, *perms = packet.cmd_tail
        for _user in user.SessionHandler.active_sessions.values():
            if _user.uid == target_uid:
                for perm in perms:
                    _user.permissions['w'].remove(perm)
                return f'{target_uid} permissions was changed to {_user.permissions}'.encode()

        udata: UserData = user.DataHandler.load_user(target_uid)
        current_perms = udata.permissions
        try:
            for perm in perms:
                current_perms['w'].remove(perm)
            user.DataHandler.save_user_data(UserData(uid=udata.uid,
                                                     current_path=udata.current_path,
                                                     home_path=udata.home_path,
                                                     permissions=current_perms))
        except Exception as E:
            return f'[!] something went wrong {E}'.encode()
        return str(udata).encode()
