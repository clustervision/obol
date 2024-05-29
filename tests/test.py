import random
import string
import unittest
from unittest.mock import patch
from obol.obol import *


class TestObolMehods(unittest.TestCase):
    """Test Obol methods"""

    def test_load_config(self):
        """Test load config"""
        Obol('/etc/obol.conf')

    @patch('obol.obol.print')
    def test_prints(self, mocked_print):
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
    def test_show_output(self, mocked_print):
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
    
    def setUp(self):
        self.obol = Obol('/etc/obol.conf')
    
    def tearDown(self):
        self.obol.erase_()
        
    @patch('obol.obol.print_warning')
    def test_group_simple1(self, mocked_print_warning):
        """Test simple"""
        self.obol.group_add('testgroup')
        testgroup = self.obol.group_show('testgroup')

        assert testgroup['cn'] == 'testgroup'
        
    @patch('obol.obol.print_warning')
    def test_user_simple1(self, mocked_print_warning):
        """Test simple"""
        self.obol.user_add('testuser')
        testuser = self.obol.user_show('testuser')
        
        assert testuser['uid'] == 'testuser'
        assert testuser['homeDirectory'] == self.obol.config.get('users', 'home') +  '/testuser'
        assert testuser['loginShell'] == self.obol.config.get('users', 'shell')

    @patch('obol.obol.print_warning')
    def test_user_simple2(self, mocked_print_warning):
        self.obol.user_add('testuser1', uid="1000")
        self.obol.user_add('testuser2', uid=1001)
        
        testuser1 = self.obol.user_show('testuser1')
        testuser2 = self.obol.user_show('testuser2')
        
        assert testuser1['cn'] == 'testuser1'
        assert testuser1['uidNumber'] == "1000"
        
        assert testuser2['cn'] == 'testuser2'
        assert testuser2['uidNumber'] == "1001"        
        
    @patch('obol.obol.print_warning')
    def test_group_complex1(self, mocked_print_warning):
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

    @patch('obol.obol.print_warning')
    def test_user_complex1(self, mocked_print_warning):
        self.obol.user_add('testuser1', cn='cn', sn='sn', given_name='given_name', mail='mail', phone='phone', shell='shell')
        
        testuser1 = self.obol.user_show('testuser1')
        
        assert testuser1['cn'] == 'cn'
        assert testuser1['sn'] == 'sn'
        assert testuser1['givenName'] == 'given_name'
        assert testuser1['mail'] == 'mail'
        assert testuser1['telephoneNumber'] == 'phone'
        assert testuser1['loginShell'] == 'shell'
        
    @patch('obol.obol.print_warning')
    def test_user_complex2(self, mocked_print_warning):
        """Test complete"""
        self.obol.group_add('testgroup1')
        self.obol.group_add('testgroup2')
        self.obol.group_add('testgroup3')
        
        self.obol.user_add('testuser1', groupname='testgroup1', groups=['testgroup2', 'testgroup3'])
        
        testuser1 = self.obol.user_show('testuser1')

        assert testuser1['uid'] == 'testuser1'
        assert all([x in testuser1['memberOf'] for x in ['testgroup1', 'testgroup2', 'testgroup3']])
        assert not any([x not in ['testgroup1', 'testgroup2', 'testgroup3'] for x in testuser1['memberOf'] ])

    @patch('obol.obol.print_warning')
    def test_combined_complex1(self, mocked_print_warning):
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
    
    @patch('obol.obol.print_warning')
    def test_combined_complex2(self, mocked_print_warning):
        
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

        groups = self.obol.group_list()
        assert not any([x in ['testgroup01', 'testgroup02', 'testgroup03'] for x in groups])
   
    @patch('obol.obol.print_warning')
    def test_combined_complex3(self, mocked_print_warning):
        
        self.obol.group_add('testgroup1')
        self.obol.group_add('testgroup2')
        
        self.obol.user_add('testuser1', groupname='testgroup1')
        self.obol.user_add('testuser2', groups=['testgroup1', 'testgroup2'])
        
        self.obol.group_modify('testgroup1', users=[])
        self.obol.group_modify('testgroup2', users=[])
        
        testuser1 = self.obol.user_show('testuser1')
        testuser2 = self.obol.user_show('testuser2')
        testgroup1 = self.obol.group_show('testgroup1')
        testgroup2 = self.obol.group_show('testgroup2')
        
        assert testuser1['memberOf'] == ['testgroup1']
        assert testuser2['memberOf'] == ['testuser2']
        assert testgroup1['member'] == ['testuser1']
        assert testgroup2.get('member', []) == []
        
    
    @patch('obol.obol.print')
    def test_import_erase_export(self, mocked_print):
        
        self.obol.group_add('testgroup1')
        self.obol.group_add('testgroup2')
        self.obol.group_add('testgroup3')
        
        self.obol.user_add('testuser1', groupname='testgroup1')
        self.obol.user_add('testuser2', groups=['testgroup1', 'testgroup2'])
        self.obol.user_add('testuser3', groupname='testgroup1', groups=['testgroup2', 'testgroup3'])
        
        data = self.obol.export_()
        self.obol.erase_()
        self.obol.import_(data)
        
        data_new = self.obol.export_()
        
        assert data == data_new


    @patch('obol.obol.os.urandom')
    def test_password(self, mocked_os_urandom):
        mocked_os_urandom.return_value = b'\x7f.jZ'
        self.obol.user_add('testuser1', password='testpassword')
        self.obol.user_add('testuser2') 
        
        password_hash = self.obol._make_secret('testpassword')
        
        testuser1 = self.obol.user_show('testuser1')
        testuser2 = self.obol.user_show('testuser2')
        
        assert testuser1['userPassword'] == password_hash
        assert testuser2.get('userPassword', None) == None
        
# if __name__ == '__main__':
#     unittest.main()