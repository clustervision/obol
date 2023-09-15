import unittest
from obol.obol import Obol

def _random_random_string(length: int = 10) -> str:
    import random
    import string
    return ''.join(random.choice(string.ascii_letters) for i in range(length))

def _random_random_int(length: int = 10) -> int:
    import random
    return random.randint(0, 10**length)

class TestObolMehods(unittest.TestCase):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def test_load_config(self):
        Obol('/etc/obol.conf')

class TestUserMethods(unittest.TestCase):

    def __init__(self, *args, **kwargs) -> None:
        self.obol = Obol('/etc/obol.conf')
        super().__init__(*args, **kwargs)

    def test_list(self):
        users = self.obol.user_list()
        assert isinstance(users, list)
        assert all(isinstance(u, dict) for u in users)
        assert all('cn' in u for u in users)
        assert all('uidNumber' in u for u in users)
        assert all('uid' in u for u in users)

    def test_add(self):
        username = _random_random_string(10)
        self.obol.user_add(username)
        user = self.obol.user_show(username)
        assert user['uid'] == username
        self.obol.user_delete(username)
        

    def test_add_with_password(self):
        username = _random_random_string(10)
        password = _random_random_string(10)
        self.obol.user_add(username, password=password)
        user = self.obol.user_show(username)
        assert user['cn'] == username
        assert user['userPassword'].startswith('{SSHA}')
        self.obol.user_delete(username)

    def test_add_with_password_and_shell(self):
        username = _random_random_string(10)
        password = _random_random_string(10)
        shell = '/bin/bash'
        self.obol.user_add(username, password=password, shell=shell)
        user = self.obol.user_show(username)
        assert user['cn'] == username
        assert user['userPassword'].startswith('{SSHA}')
        assert user['loginShell'] == shell
        self.obol.user_delete(username)

    def test_add_complete(self):
        username = _random_random_string(10)
        cn = _random_random_string(10)
        sn = _random_random_string(10)
        givenName = _random_random_string(10)
        password = _random_random_string(10)
        uid = str(_random_random_int(4))
        gid = None
        mail = _random_random_string(10)
        phone = _random_random_string(10)
        shell = '/bin/bash'
        groupname = None
        groups = None
        home = '/home/' + username
        expire = str(_random_random_int(10))
        self.obol.user_add(username,
            cn=cn,
            sn=sn,
            givenName=givenName,
            password=password,
            uid=uid,
            gid=gid,
            mail=mail,
            phone=phone,
            shell=shell,
            groupname=groupname,
            groups=groups,
            home=home,
            expire=expire,
            )

        user = self.obol.user_show(username)
        assert user['cn'] == cn
        assert user['sn'] == sn
        assert user['givenName'] == givenName
        assert user['userPassword'].startswith('{SSHA}')
        assert user['uidNumber'] == uid
        assert user['mail'] == mail
        assert user['telephoneNumber'] == phone
        assert user['loginShell'] == shell
        assert user['homeDirectory'] == home
        self.obol.user_delete(username)

    def test_modify(self):
        username = _random_random_string(10)
        cn = _random_random_string(10)
        sn = _random_random_string(10)
        givenName = _random_random_string(10)
        password = _random_random_string(10)
        uid = str(_random_random_int(4))
        gid = None
        mail = _random_random_string(10)
        phone = _random_random_string(10)
        shell = '/bin/bash'
        groupname = None
        groups = None
        home = '/home/' + username
        expire = str(_random_random_int(10))
        self.obol.user_add(username)
        self.obol.user_modify(username,
            cn=cn,
            sn=sn,
            givenName=givenName,
            password=password,
            uid=uid,
            gid=gid,
            mail=mail,
            phone=phone,
            shell=shell,
            groupname=groupname,
            groups=groups,
            home=home,
            expire=expire,
            )
        user = self.obol.user_show(username)
        assert user['cn'] == cn
        assert user['sn'] == sn
        assert user['givenName'] == givenName
        assert user['userPassword'].startswith('{SSHA}')
        assert user['uidNumber'] == uid
        assert user['mail'] == mail
        assert user['telephoneNumber'] == phone
        assert user['loginShell'] == shell
        assert user['homeDirectory'] == home
        self.obol.user_delete(username)

    def test_delete(self):
        username = _random_random_string(10)
        self.obol.user_add(username)
        self.obol.user_delete(username)
        users = self.obol.user_list()
        assert username not in [u['uid'] for u in users]

class TestGroupMethods(unittest.TestCase):

    def __init__(self, *args, **kwargs) -> None:
        self.obol = Obol('/etc/obol.conf')
        super().__init__(*args, **kwargs)
        

    def test_list(self):
        groups = self.obol.group_list()
        assert isinstance(groups, list)
        assert all(isinstance(g, dict) for g in groups)
        assert all('gidNumber' in g for g in groups)
        assert all('cn' in g for g in groups)

    def test_add(self):
        groupname = _random_random_string(10)
        self.obol.group_add(groupname)
        group = self.obol.group_show(groupname)
        assert group['cn'] == groupname
        self.obol.group_delete(groupname)
    
    def test_delete(self):
        groupname = _random_random_string(10)
        self.obol.group_add(groupname)
        self.obol.group_delete(groupname)
        groups = self.obol.group_list()
        assert groupname not in [g['cn'] for g in groups]


class TestMixedMethods(unittest.TestCase):
    def __init__(self, *args, **kwargs) -> None:
        self.obol = Obol('/etc/obol.conf')
        super().__init__(*args, **kwargs)
    
    def test_add_user_with_group(self):
        username = _random_random_string(10)
        groupname = _random_random_string(10)
        self.obol.group_add(groupname)
        self.obol.user_add(username, groupname=groupname)
        user = self.obol.user_show(username)
        group = self.obol.group_show(groupname)
        assert user['cn'] == username
        assert user['gidNumber'] == group['gidNumber']
        assert username in group['users']
        self.obol.user_delete(username)
        self.obol.group_delete(groupname)

    def test_add_user_with_gid(self):
        username = _random_random_string(10)
        groupname = _random_random_string(10)
        self.obol.group_add(groupname)
        _group = self.obol.group_show(groupname)
        self.obol.user_add(username, gid=_group['gidNumber'])
        user = self.obol.user_show(username)
        group = self.obol.group_show(groupname)
        assert user['cn'] == username
        assert user['gidNumber'] == group['gidNumber']
        assert username in group['users']
        self.obol.user_delete(username)
        self.obol.group_delete(groupname)

    def test_add_user_with_groups(self):
        username = _random_random_string(10)
        groupname1 = _random_random_string(10)
        groupname2 = _random_random_string(10)
        self.obol.group_add(groupname1)
        self.obol.group_add(groupname2)
        self.obol.user_add(username, groups=[groupname1, groupname2])
        user = self.obol.user_show(username)
        group1 = self.obol.group_show(groupname1)
        group2 = self.obol.group_show(groupname2)
        assert user['cn'] == username
        assert username in group1['users']
        assert username in group2['users']
        self.obol.user_delete(username)
        self.obol.group_delete(groupname1)
        self.obol.group_delete(groupname2)

    def test_modify_gid(self):
        username = _random_random_string(10)
        new_gid = str(_random_random_int(4))
        self.obol.user_add(username)
        self.obol.group_modify(username, new_gid)
        user = self.obol.user_show(username)
        group = self.obol.group_show(username)
        assert user['gidNumber'] == new_gid
        assert group['gidNumber'] == new_gid
        assert username in group['users']
        self.obol.user_delete(username)

    def test_addusers(self):
        username1 = _random_random_string(10)
        username2 = _random_random_string(10)
        groupname = _random_random_string(10)
        self.obol.group_add(groupname)
        self.obol.user_add(username1)
        self.obol.user_add(username2)
        self.obol.group_addusers(groupname, [username1, username2])
        group = self.obol.group_show(groupname)
        assert username1 in group['users']
        assert username2 in group['users']
        self.obol.user_delete(username1)
        self.obol.user_delete(username2)
        self.obol.group_delete(groupname)
    
    def test_delusers(self):
        username1 = _random_random_string(10)
        username2 = _random_random_string(10)
        groupname = _random_random_string(10)
        self.obol.group_add(groupname)
        self.obol.user_add(username1)
        self.obol.user_add(username2)
        self.obol.group_addusers(groupname, [username1, username2])
        self.obol.group_delusers(groupname, [username1, username2])
        group = self.obol.group_show(groupname)
        assert username1 not in group['users']
        assert username2 not in group['users']
        self.obol.user_delete(username1)
        self.obol.user_delete(username2)
        self.obol.group_delete(groupname)

    def test_group_modify_users(self):
        username1 = _random_random_string(10)
        username2 = _random_random_string(10)
        groupname = _random_random_string(10)
        self.obol.group_add(groupname)
        self.obol.user_add(username1)
        self.obol.user_add(username2)
        self.obol.group_modify(groupname, users=[username1, username2])
        group = self.obol.group_show(groupname)
        assert username1 in group['users']
        assert username2 in group['users']
        self.obol.user_delete(username1)
        self.obol.user_delete(username2)
        self.obol.group_delete(groupname)

    def test_user_modify_groups(self):
        username = _random_random_string(10)
        groupname1 = _random_random_string(10)
        groupname2 = _random_random_string(10)
        self.obol.group_add(groupname1)
        self.obol.group_add(groupname2)
        self.obol.user_add(username)
        self.obol.user_modify(username, groups=[groupname1, groupname2])
        user = self.obol.user_show(username)
        group1 = self.obol.group_show(groupname1)
        group2 = self.obol.group_show(groupname2)
        assert username in group1['users']
        assert username in group2['users']
        self.obol.user_delete(username)
        self.obol.group_delete(groupname1)
        self.obol.group_delete(groupname2)



if __name__ == '__main__':
    unittest.main()
