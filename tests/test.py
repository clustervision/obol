import random
import string
import unittest
from unittest.mock import patch
from obol.obol import *


class TestObolMehods(unittest.TestCase):
    """Test Obol methods"""
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def test_load_config(self):
        """Test load config"""
        Obol('/etc/obol.conf')

    
    @patch('obol.obol.print')
    def test_prints(self, fakeprint):
        print_error('test')
        print_warning('test')
        print_table([])
        print_table([
            {
                "uid": "testuser",
                "cn": "testuser",
                "sn": "testuser",
                "loginShell": "/bin/bash",
                "uidNumber": "1050",
                "gidNumber": "150",
                "homeDirectory": "/trinity/home/testuser",
                "shadowMin": "0",
                "shadowMax": "99999",
                "shadowWarning": "7",
                "shadowExpire": "-1",
                "shadowLastChange": "19871",
                "memberOf": [
                "testuser"
                ]
            }
        ])
        print_table(
            {
                "uid": "testuser",
                "cn": "testuser",
                "sn": "testuser",
                "loginShell": "/bin/bash",
                "uidNumber": "1050",
                "gidNumber": "150",
                "homeDirectory": "/trinity/home/testuser",
                "shadowMin": "0",
                "shadowMax": "99999",
                "shadowWarning": "7",
                "shadowExpire": "-1",
                "shadowLastChange": "19871",
                "memberOf": [
                "testuser"
                ]
            }
        )
    
    @patch('obol.obol.print')
    def test_show_output(self, fakeprint):
        """Test show output"""
        
        @show_output
        def fn(obol, *args,  **kwargs):
            return {
                "uid": "testuser",
                "cn": "testuser",
                "sn": "testuser",
                "loginShell": "/bin/bash",
                "uidNumber": "1050",
                "gidNumber": "150",
                "homeDirectory": "/trinity/home/testuser",
                "shadowMin": "0",
                "shadowMax": "99999",
                "shadowWarning": "7",
                "shadowExpire": "-1",
                "shadowLastChange": "19871",
                "memberOf": [
                "testuser"
                ]
            }
        
        fn(None, output_type='json')
        fn(None, output_type='table')

class TestLdapMethods(unittest.TestCase):
    """Test User methods"""
    def __init__(self, *args, **kwargs) -> None:
        self.obol = Obol('/etc/obol.conf')
        super().__init__(*args, **kwargs)
        
        
    def test_group_simple1(self):
        """Test simple"""
        self.obol.group_add('testgroup')
        testgroup = self.obol.group_show('testgroup')

        assert testgroup['cn'] == 'testgroup'
        self.obol.group_delete('testgroup')
        
        
    def test_user_simple1(self):
        """Test simple"""
        self.obol.user_add('testuser')
        testuser = self.obol.user_show('testuser')
        
        assert testuser['uid'] == 'testuser'
        assert testuser['homeDirectory'] == self.obol.config.get('users', 'home') +  '/testuser'
        assert testuser['loginShell'] == self.obol.config.get('users', 'shell')
        
        self.obol.user_delete('testuser')
    
    
    def test_user_simple2(self):
        self.obol.user_add('testuser1', uid="1000")
        self.obol.user_add('testuser2', uid=1001)
        
        testuser1 = self.obol.user_show('testuser1')
        testuser2 = self.obol.user_show('testuser2')
        
        assert testuser1['cn'] == 'testuser1'
        assert testuser1['uidNumber'] == "1000"
        
        assert testuser2['cn'] == 'testuser2'
        assert testuser2['uidNumber'] == "1001"        

        self.obol.user_delete('testuser1')
        self.obol.user_delete('testuser2')
        
        
    def test_group_complex1(self):
        """Test complete"""
        self.obol.user_add('testuser1')
        self.obol.user_add('testuser2')
        self.obol.group_add('testgroup1', gid="1000", users=['testuser1'])
        self.obol.group_add('testgroup2', gid=1001, users=['testuser1', 'testuser2'])
        
        testgroup1 = self.obol.group_show('testgroup1')
        testgroup2 = self.obol.group_show('testgroup2')

        assert testgroup1['cn'] == 'testgroup1'
        assert testgroup1['gidNumber'] == "1000"
        assert testgroup1['member'] == ['testuser1']
        
        assert testgroup2['cn'] == 'testgroup2'
        assert testgroup2['gidNumber'] == "1001"
        assert testgroup2['member'] == ['testuser1', 'testuser2']
        
        self.obol.user_delete('testuser1')
        self.obol.user_delete('testuser2')
        self.obol.group_delete('testgroup1')
        self.obol.group_delete('testgroup2')


    def test_user_complex1(self):
        self.obol.user_add('testuser1', cn='cn', sn='sn', given_name='given_name', mail='mail', phone='phone', shell='shell')
        
        testuser1 = self.obol.user_show('testuser1')
        
        assert testuser1['cn'] == 'cn'
        assert testuser1['sn'] == 'sn'
        assert testuser1['givenName'] == 'given_name'
        assert testuser1['mail'] == 'mail'
        assert testuser1['telephoneNumber'] == 'phone'
        assert testuser1['loginShell'] == 'shell'
        
        self.obol.user_delete('testuser1')
        
        
    def test_user_complex2(self):
        """Test complete"""
        self.obol.group_add('testgroup1')
        self.obol.group_add('testgroup2')
        self.obol.group_add('testgroup3')
        
        self.obol.user_add('testuser1', groupname='testgroup1', groups=['testgroup2', 'testgroup3'])
        
        testuser1 = self.obol.user_show('testuser1')

        assert testuser1['uid'] == 'testuser1'
        assert all([x in testuser1['memberOf'] for x in ['testgroup1', 'testgroup2', 'testgroup3']])
        assert not any([x not in ['testgroup1', 'testgroup2', 'testgroup3'] for x in testuser1['memberOf'] ])

        self.obol.user_delete('testuser1')
        self.obol.group_delete('testgroup1')
        self.obol.group_delete('testgroup2')
        self.obol.group_delete('testgroup3')
    
    def test_combined_complex1(self):
        self.obol.group_add('testgroup1')
        self.obol.group_add('testgroup2')
        self.obol.group_add('testgroup3')
        
        self.obol.user_add('testuser1')
        self.obol.user_add('testuser2')
        self.obol.user_add('testuser3')
        
        self.obol.group_addusers('testgroup1', ['testuser1', 'testuser2'])
        
        testgroup1 = self.obol.group_show('testgroup1')
        
        assert all([x in testgroup1['member'] for x in ['testuser1', 'testuser2']])
        assert not any([x not in ['testuser1', 'testuser2'] for x in testgroup1['member'] ])
        
        self.obol.group_delusers('testgroup1', ['testuser1', 'testuser2'])
        
        testgroup1 = self.obol.group_show('testgroup1')
        
        assert not any([x in testgroup1.get('member', []) for x in ['testuser1', 'testuser2']])


        self.obol.user_delete('testuser1')
        self.obol.user_delete('testuser2')
        self.obol.user_delete('testuser3')
        self.obol.group_delete('testgroup1')
        self.obol.group_delete('testgroup2')
        self.obol.group_delete('testgroup3')
        
    def test_combined_complex2(self):
        
        self.obol.group_add('testgroup1')
        self.obol.group_add('testgroup2')
        self.obol.group_add('testgroup3')
        
        self.obol.user_add('testuser1', groupname='testgroup1')
        self.obol.user_add('testuser2', groups=['testgroup2', 'testgroup3']) 
        self.obol.user_add('testuser3', groupname='testgroup1', groups=['testgroup2', 'testgroup3'])
        
        self.obol.group_rename('testgroup1', 'testgroup01')
        self.obol.group_rename('testgroup2', 'testgroup02')
        self.obol.group_rename('testgroup3', 'testgroup03')
        
        testuser1 = self.obol.user_show('testuser1')
        testuser2 = self.obol.user_show('testuser2')
        testuser3 = self.obol.user_show('testuser3')
        testgroup1 = self.obol.group_show('testgroup01')
        testgroup2 = self.obol.group_show('testgroup02')
        testgroup3 = self.obol.group_show('testgroup03')
        
        assert testgroup1['cn'] == 'testgroup01'
        assert testgroup2['cn'] == 'testgroup02'
        assert testgroup3['cn'] == 'testgroup03'
            
        assert all([x in testuser1['memberOf'] for x in ['testgroup01']])
        assert not any([x not in ['testgroup01'] for x in testuser1['memberOf'] ])
        
        assert all([x in testuser2['memberOf'] for x in ['testuser2', 'testgroup02', 'testgroup03']])
        assert not any([x not in ['testuser2', 'testgroup02', 'testgroup03'] for x in testuser2['memberOf'] ])
        
        assert all([x in testuser3['memberOf'] for x in ['testgroup01', 'testgroup02', 'testgroup03']])
        assert not any([x not in ['testgroup01', 'testgroup02', 'testgroup03'] for x in testuser3['memberOf'] ])
        
        self.obol.user_delete('testuser1')
        self.obol.user_delete('testuser2')
        self.obol.user_delete('testuser3')
        self.obol.group_delete('testgroup01')
        self.obol.group_delete('testgroup02')
        self.obol.group_delete('testgroup03')
        
        groups = self.obol.group_list()
        assert not any([x in ['testgroup01', 'testgroup02', 'testgroup03'] for x in groups])
   
    def test_combined_complex3(self):
        
        self.obol.group_add('testgroup1')
        self.obol.group_add('testgroup2')
        
        self.obol.user_add('testuser1', groupname='testgroup1')
        self.obol.user_add('testuser2', groups=['testgroup1', 'testgroup2'])
        
        self.obol.group_modify('testgroup1', users=['testuser2'])
        self.obol.group_modify('testgroup2', users=[])
        
        assert self.obol.group_show('testgroup1')['member'] == ['testuser2']
        assert self.obol.group_show('testgroup2')['member'] == []
        
        self.obol.group_modify('testgroup2', users=[])
        self.obol.user_add('testuser2', groups=['testgroup1', 'testgroup2'])
        
        
        
        self.obol.user_delete('testuser1')
        self.obol.user_delete('testuser2')
        self.obol.group_delete('testgroup1')
        self.obol.group_delete('testgroup2')
    
# if __name__ == '__main__':
#     unittest.main()