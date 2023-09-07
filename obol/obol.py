#!/usr/bin/python3

######################################################################
# Obol user management tool
# Copyright (c) 2016-2023  ClusterVision Solutions B.V.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License (included with the sources) for more
# details.
######################################################################


import os
import sys
import grp
import pwd
import ldap
import time
import json
import hashlib
import argparse
import configparser
import base64

from typing import List, Dict, Union
from pprint import pprint

def print_table(item: Union[List[Dict], Dict]):
    """Print a list of dicts as a table, dict as a transposed table"""

    if isinstance(item, list):
        if len(item) == 0: 
            print('No results')
            return 
        keys = item[0].keys()
        widths = [len(key) for key in keys]

        for row in item:
            for i, key in enumerate(keys):
                widths[i] = max(widths[i], len(str(row[key])))

        print(' | '.join([key.ljust(widths[i]) for i, key in enumerate(keys)]))
        print('-+-'.join(['-' * widths[i] for i, key in enumerate(keys)]))

        for row in item:
            print(' | '.join([str(row[key]).ljust(widths[i]) for i, key in enumerate(keys)]))

    elif isinstance(item, dict):
        keys = item.keys()
        widths = [len(key) for key in keys]

        max_width = max(widths)
        for key in keys:
            print(key.ljust(max_width), '|', item[key])

def show_output(func):
    '''Function decorator to print the output of a function '''
    def inner(obol, *args, **kwargs):
        output = func(obol, *args, **kwargs)
        if 'output' in kwargs:
            output_type = kwargs['output']
        else: 
            output_type = obol.output
        
        if output_type == 'json' :
            pprint(output)
        elif output_type == 'table':
            print_table(output)
        return output
    return inner


class Obol:
    user_fields = [
        'cn',
        'uid',
        'uidNumber',
        'gidNumber',
        'homeDirectory',
        'loginShell',
        'shadowExpire',
        'shadowLastChange',
        'shadowMax',
        'shadowMin',
        'shadowWarning',
        'sn',
        'userPassword',
        'givenName',
        'mail',
        'telephoneNumber',
    ]
    group_fields = [
        'cn',
        'gid',
        'gidNumber',
        'member'
    ]

    def __init__(self, config_path, output=None, overrides={}):
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        # override from cli

        for key, value in overrides.items():
            if value and (key in self.config['ldap']):
                print(key, value)
                self.config.set('ldap', key, value)
        # bind to LDAP
        self.conn = ldap.initialize(self.config.get("ldap", "host"))
        self.conn.simple_bind_s(self.config.get("ldap", "bind_dn"),
                                self.config.get("ldap", "bind_pass"))
        self.output = output

    @property
    def base_dn(self):
        return self.config.get("ldap", "base_dn")

    @property 
    def users_dn(self):
        return 'ou=People,%s' % self.base_dn

    @property
    def groups_dn(self):
        return 'ou=Group,%s' % self.base_dn

    @classmethod
    def _make_secret(cls, password):
        """Encodes the given password as a base64 SSHA hash+salt buffer"""
        if password.startswith('{SSHA}'):
            return password

        salt = os.urandom(4)
        # Hash the password and append the salt
        sha = hashlib.sha1(password.encode('utf-8'))
        sha.update(salt)
        # Create a base64 encoded string of the concatenated digest + salt
        digest_b64 = base64.b64encode(sha.digest() + salt).decode('utf-8')

        # Tag the digest above with the {SSHA} tag
        tagged_digest = f'{{SSHA}}{digest_b64}'

        return tagged_digest
    
    @classmethod
    def _next_id(cls, idlist):
        available_ids = [i for i in range(1000, 10000) if str(i) not in idlist]
        next_id = str(min(available_ids))

        return next_id


    ###### List
    @show_output
    def user_list(self, **kwargs):
        """List users defined in the system"""

        base_dn = self.users_dn
        filter = '(objectclass=posixAccount)'

        users = []
        for _, attrs in self.conn.search_s(base_dn, ldap.SCOPE_SUBTREE, filter):
            fields = ['cn', 'uid', 'uidNumber', ]
            user = { k:[vi.decode('utf8') for vi in v][0] for k,v in attrs.items() if k in fields }
            users.append(user)

        return users


    @show_output
    def group_list(self, **kwargs):
        """List groups defined in the system"""

        base_dn = self.groups_dn
        filter = '(objectclass=posixGroup)'

        groups = []
        for _, attrs in self.conn.search_s(base_dn, ldap.SCOPE_SUBTREE, filter):
            fields = ['cn', 'gidNumber', ]
            group = { k:[vi.decode('utf8') for vi in v][0] for k,v in attrs.items() if k in fields }
            groups.append(group)

        return groups


    ###### Show
    @show_output
    def user_show(self, username, **kwargs):
        """Show system user details"""

        base_dn = self.users_dn
        filter = '(uid=%s)' % username

        for _, attrs in self.conn.search_s(base_dn, ldap.SCOPE_SUBTREE, filter, self.user_fields):
            user = { k:[vi.decode('utf8') for vi in v][0] for k,v in attrs.items() if k in self.user_fields }
            return user

        raise LookupError("User '%s' does not exist" % username)


    @show_output
    def group_show(self, groupname, **kwargs):
        base_dn = self.groups_dn
        filter = '(cn=%s)' % groupname

        for _, attrs in self.conn.search_s(base_dn, ldap.SCOPE_SUBTREE, filter, self.group_fields):
            group = { k:[vi.decode('utf8') for vi in v] for k,v in attrs.items() if k in self.group_fields }
            group = { k:v[0] if not (k=='member') else v for k,v in group.items() }
            members = group.get('member', [])
            group['member'] = [m.split(',')[0].split('=')[1] for m in members]
            return group

        raise LookupError("Group '%s' does not exist" % groupname)


    ###### Add
    def user_add(self,
                username,
                cn=None,
                sn=None,
                givenName=None,
                password=None,
                uid=None,
                gid=None,
                mail=None,
                phone=None,
                shell=None,
                groupname=None,
                groups=None,
                home=None,
                expire=None,
                **kwargs):
        """Add a user to the LDAP directory"""
        # Ensure username's uniqueness
        usernames = [u['uid'] for u in self.user_list(output=None)]
        if username in usernames:
            raise ValueError('Username %s already exists' % username)

        # Ensure uid's correctness
        uids = [u['uidNumber'] for u in self.user_list(output=None)]
        if uid:
            # if uid is supplied user should not exist
            if uid in uids:
                raise ValueError('UID %s already exists' % uid)
        else:
            # if uid is not supplied, generate one
            uid = self._next_id(uids)

        # Ensure groups correctness
        create_group = False
        existing_groups = self.group_list(output=None)
        if groupname and gid:
            # if both groupname and gid are specified: should refer to same group
            existing_group = self.group_show(groupname, output=None)
            if existing_group['gidNumber'] != gid:
                raise ValueError('Group %s does not have gid %s' % (groupname, gid))
        elif groupname:
            # if only groupname is specified: groupname should exist
            if groupname not in [g['cn'] for g in existing_groups]:
                raise ValueError('Group %s does not exist' % groupname)
            gid = self.group_show(groupname, output=None)['gidNumber']
        elif gid:
            # if only gid is specified: gid should exist
            if gid not in [g['gidNumber'] for g in existing_groups]:
                raise ValueError('GID %s does not exist' % gid)
            existing_groups = self.group_list(output=None)
            groupname = [g['cn'] for g in existing_groups if g['gidNumber'] == gid][0]
        else:
            # neither groupname or gid is specified: groupname <- username
            groupname = username
            if groupname in [g['cn'] for g in existing_groups]:
                # groupname exists: use it
                gid = self.group_show(groupname, output=None)['gidNumber']
            if groupname not in [g['cn'] for g in existing_groups]:
                # groupname does not exist: create it
                create_group = True
                gids = [g['gidNumber'] for g in existing_groups]
                gid = self._next_id(gids)


        # Add the user
        dn = 'uid=%s,ou=People,%s' % (username, self.base_dn)
        cn = cn or username
        sn = sn or username
        home = home or self.config.get("users", "home") + '/' + username
        shell = shell or self.config.get("users", "shell")

        if (expire is not None) and (expire != '-1'):
            expire = str(int(expire) + int(time.time() / 86400))
        else:
            expire = '-1'
        user_record = [
        ('objectclass', [b'top', b'person', b'organizationalPerson',
                        b'inetOrgPerson', b'posixAccount', b'shadowAccount']),
        ('uid', [username.encode('utf-8')]),
        ('cn', [cn.encode('utf-8')]),
        ('sn', [sn.encode('utf-8')]),
        ('loginShell', [shell.encode('utf-8')]),
        ('uidNumber', [uid.encode('utf-8')]),
        ('gidNumber', [gid.encode('utf-8')]),
        ('homeDirectory', [home.encode('utf-8')]),
        ('shadowMin', [b'0']),
        ('shadowMax', [b'99999']),
        ('shadowWarning', [b'7']),
        ('shadowExpire', [str(expire).encode('utf-8')]),
        ('shadowLastChange', [str(int(time.time() / 86400)).encode('utf-8')])
        ]

        if givenName:
            user_record.append(('givenName', [givenName.encode('utf-8')]))

        if mail:
            user_record.append(('mail', [mail.encode('utf-8')]))

        if phone:
            user_record.append(('telephoneNumber', [phone.encode('utf-8')]))

        if password:
            hashed_password = self._make_secret(password).encode('utf-8')
            user_record.append(('userPassword', [hashed_password]))

        # Add the user
        self.conn.add_s(dn, user_record)

        if create_group:
            # Add the group
            dn = 'cn=%s,ou=Group,%s' % (groupname, self.base_dn)
            group_record = [
                ('objectclass', [b'top', b'groupOfMembers', b'posixGroup']),
                ('cn', [username.encode('utf-8')]),
                ('member', [str('uid=%s,ou=People,%s' % (username, self.base_dn)).encode('utf-8')]),
                ('gidNumber', [gid.encode('utf-8')])
            ]

            self.conn.add_s(dn, group_record)

        else:
            self.group_addusers(groupname, [username])

        if groups:
            for group in groups:
                self.group_addusers(group, [username])


    def group_add(self,
                groupname=None,
                gid=None,
                users=None,
                **kwargs):
        """Add a group to the LDAP"""

        # Ensure groupname's uniqueness
        groupnames = [g['cn'] for g in self.group_list(output=None)]
        if groupname in groupnames:
            raise ValueError('Groupname %s already exists' % groupname)
        
        # Ensure gid's uniqueness
        gids = [g['gidNumber'] for g in self.group_list(output=None)]
        if gid:
            if gid in gids:
                raise ValueError('GID %s already exists' % gid)
        else:
            gid = self._next_id(gids)

        if users:
            # Ensure users exist
            existing_usernames = [u['uid'] for u in self.user_list(output=None)]
            non_existing_usernames = [u for u in users if u not in existing_usernames]
            if len(non_existing_usernames) > 0:
                raise ValueError("Users '%s' do not exist" % ', '.join(non_existing_usernames))

        # Add group
        dn = 'cn=%s,ou=Group,%s' % (groupname, self.base_dn)
        group_record = [
            ('objectclass', [b'top', b'groupOfMembers', b'posixGroup']),
            ('cn', [groupname.encode('utf-8')]),
            ('gidNumber', [gid.encode('utf-8')])
        ]
        self.conn.add_s(dn, group_record)
        
        # Add users to group 
        if users:
            self.group_addusers(groupname, users)


    ###### Delete
    def user_delete(self, username, **kwargs):
        """Delete a user from the system"""

        # Ensure user exists
        usernames = [u['uid'] for u in self.user_list(output=None)]
        if username not in usernames:
            raise LookupError("User '%s' does not exist" % username)

        # Delete the user
        dn = 'uid=%s,ou=People,%s' % (username, self.base_dn)
        self.conn.delete_s(dn)

        # Delete the default group if it exists and has no other members
        try:
            group = self.group_show(username, output=None)
            if len(group['member']) == 0:
                dn = 'cn=%s,ou=Group,%s' % (group['cn'], self.base_dn)
                self.conn.delete_s(dn)
        except LookupError:
            pass

    def group_delete(self, groupname, **kwargs):
        """Delete a user from the system"""

        # Ensure group exists
        gropunames = [g['cn'] for g in self.group_list(output=None)]
        if groupname not in gropunames:
            raise LookupError("Group '%s' does not exist" % groupname)
        
        # Ensure group has no members
        group = self.group_show(groupname, output=None)
        if len(group['member']) > 0:
            raise ValueError("Group '%s' has members" % groupname)
        # Delete the group
        dn = 'cn=%s,ou=Group,%s' % (groupname, self.base_dn)
        self.conn.delete_s(dn)


    ###### Modify
    def user_modify(self,
            username,
            cn=None,
            sn=None,
            givenName=None,
            password=None,
            uid=None,
            gid=None,
            mail=None,
            phone=None,
            shell=None,
            groupname=None,
            groups=None,
            home=None,
            expire=None,
            **kwargs):
        """Modify a user"""

        # Ensure user exists
        old_user = self.user_show(username, output=None)
        
        primary_group_changed = False
        mod_attrs = []
        groups_to_add = []
        groups_to_del = []

        if cn:
            mod_attrs.append((ldap.MOD_REPLACE, 'cn', cn.encode('utf-8')))
        if sn:
            mod_attrs.append((ldap.MOD_REPLACE, 'sn', sn.encode('utf-8')))
        if givenName:
            mod_attrs.append((ldap.MOD_REPLACE, 'givenName', givenName.encode('utf-8')))
        if uid:
            # Ensure uid's uniqueness
            uids = [u['uidNumber'] for u in self.user_list(output=None)]
            if uid in uids:
                raise ValueError('UID %s already exists' % uid)
            mod_attrs.append((ldap.MOD_REPLACE, 'uidNumber', uid.encode('utf-8')))
        if gid and groupname:
            # if both groupname and gid are specified: should refer to same group
            existing_group = self.group_show(groupname, output=None)
            if existing_group['gidNumber'] != gid:
                raise ValueError('Group %s does not have gid %s' % (groupname, gid))
            mod_attrs.append((ldap.MOD_REPLACE, 'gidNumber', gid.encode('utf-8')))
            primary_group_changed = True
        elif groupname:
            # if only groupname is specified: groupname should exist
            if groupname not in [g['cn'] for g in existing_groups]:
                raise ValueError('Group %s does not exist' % groupname)
            gid = self.group_show(groupname, output=None)['gidNumber']
            primary_group_changed = True
        elif gid:
            # if only gid is specified: gid should exist
            if gid not in [g['gidNumber'] for g in existing_groups]:
                raise ValueError('GID %s does not exist' % gid)
            existing_groups = self.group_list(output=None)
            groupname = [g['cn'] for g in existing_groups if g['gidNumber'] == gid][0]
            primary_group_changed = True
        if mail:
            mod_attrs.append((ldap.MOD_REPLACE, 'mail', mail.encode('utf-8')))
        if phone:
            mod_attrs.append((ldap.MOD_REPLACE, 'telephoneNumber', phone.encode('utf-8')))
        if shell:
            mod_attrs.append((ldap.MOD_REPLACE, 'loginShell', shell.encode('utf-8')))
        if home:
            mod_attrs.append((ldap.MOD_REPLACE, 'homeDirectory', home.encode('utf-8')))
        if expire:
            if expire != '-1':
                expire = str(int(expire) + int(time.time() / 86400))
            mod_attrs.append((ldap.MOD_REPLACE, 'shadowExpire', expire.encode('utf-8')))
        if password:
            hashed_password = self._make_secret(password).encode('utf-8')
            mod_attrs.append((ldap.MOD_REPLACE, 'userPassword', hashed_password))
        if groups:
            # Ensure groups exist
            existing_groupnames = [g['cn'] for g in self.group_list(output=None)]
            non_existing_groupnames = [g for g in groups if g not in existing_groupnames]
            if len(non_existing_groupnames) > 0:
                raise ValueError("Groups '%s' do not exist" % ', '.join(non_existing_groupnames))
            groups_to_add.append([g for g in groups if g not in self.user_show(username, output=None)['memberOf']])
            groups_to_del.append([g for g in self.user_show(username, output=None)['memberOf'] if g not in groups])
        if primary_group_changed:
            old_groups = self.group_list(output=None)
            old_groupname = [g['cn'] for g in old_groups if g['gidNumber'] == old_user['gidNumber']][0]
            groups_to_add.append([groupname])
            groups_to_del.append([old_groupname])
        dn = 'uid=%s,ou=People,%s' % (username, self.base_dn)
        self.conn.modify_s(dn, mod_attrs)
        for group in groups_to_add:
            self.group_addusers(group, [username])
        for group in groups_to_del:
            self.group_delusers(group, [username])

    def group_modify(self,
            groupname,
            gid=None,
            users=None,
            **kwargs):
        """Modify a group"""

        # Ensure group exists
        old_group = self.group_show(groupname, output=None)

        group_mod_attrs = []
        users_mod_attrs = {}
        users_to_add = []
        users_to_del = []
        
        if gid:
            gids = [g['gidNumber'] for g in self.group_list(output=None)]
            # Ensuer gid's uniqueness
            if gid in gids:
                raise ValueError('GID %s already exists' % gid)
            group_mod_attrs.append((ldap.MOD_REPLACE, 'gidNumber', gid.encode('utf-8')))

            # Update gid on groups whoose primaryGroup is this group
            for username in old_group['member']:
                user = self.user_show(username, output=None)
                if user['gidNumber'] == old_group['gidNumber']:
                    user_dn = 'uid=%s,ou=People,%s' % (user['uid'], self.base_dn)
                    users_mod_attrs[user_dn] = [(ldap.MOD_REPLACE, 'gidNumber', gid.encode('utf-8'))]
       
        if users:
            # Ensure users exist
            existing_usernames = [u['uid'] for u in self.user_list(output=None)]
            non_existing_usernames = [u for u in users if u not in existing_usernames]
            if len(non_existing_usernames) > 0:
                raise ValueError("Users '%s' do not exist" % ', '.join(non_existing_usernames))
            users_to_add = [u for u in users if u not in old_group['member']]
            users_to_del = [u for u in old_group['member'] if u not in users]

        # Modify the group
        group_dn = 'cn=%s,ou=Group,%s' % (groupname, self.base_dn)
        self.conn.modify_s(group_dn, group_mod_attrs)
        self.group_addusers(groupname, users_to_add)
        self.group_delusers(groupname, users_to_del)
        # Modify the users that use this group as primaryGroup
        for user_dn, user_mod_attrs in users_mod_attrs.items():
            self.conn.modify_s(user_dn, user_mod_attrs)


    def group_addusers(self, groupname, usernames, **kwargs):
        """Add users to a group"""

        # Ensure group exists
        _ = self.group_show(groupname, output=None)

        # Ensure users exist
        existing_usernames = [u['uid'] for u in self.user_list(output=None)]
        non_existing_usernames = [u for u in usernames if u not in existing_usernames]
        if len(non_existing_usernames) > 0:
            raise LookupError("Users '%s' do not exist" % ', '.join(non_existing_usernames))

        mod_attrs = []
        for name in usernames:
            mod_attrs.append((ldap.MOD_ADD, 'member',
                            str('uid=%s,ou=People,%s' % (name, self.base_dn)).encode('utf-8')))
        
        group_dn = 'cn=%s,ou=Group,%s' % (groupname, self.base_dn)
        self.conn.modify_s(group_dn, mod_attrs)


    def group_delusers(self, groupname, usernames, **kwargs):
        """Remove users from a group"""

        # Ensure group exists
        _ = self.group_show(groupname, output=None)

        # Ensure users exist
        existing_usernames = [u['uid'] for u in self.user_list(output=None)]
        non_existing_usernames = [u for u in usernames if u not in existing_usernames]
        if len(non_existing_usernames) > 0:
            raise LookupError("Users '%s' do not exist" % ', '.join(non_existing_usernames))

        mod_attrs = []
        for name in usernames:
            mod_attrs.append((ldap.MOD_DELETE, 'member',
                            str('uid=%s,ou=People,%s' % (name, self.base_dn)).encode('utf-8')))
        
        group_dn = 'cn=%s,ou=Group,%s' % (groupname, self.base_dn)
        self.conn.modify_s(group_dn, mod_attrs)

def run():
    parser = argparse.ArgumentParser(prog='obol',
                                    description='Manage Cluster Users.')

    # LDAP bind parameters
    parser.add_argument('--bind-dn', '-D', metavar="BIND DN")
    parser.add_argument('--bind-pass', '-w', metavar="BIND PASSWORD")
    parser.add_argument('--host', '-H', metavar="HOST")
    parser.add_argument('--base-dn', '-b', metavar="BASE_DN")
    parser.add_argument('--json', '-J', action="store_true")

    # Obol command categories
    subparsers = parser.add_subparsers(help='commands', dest='target')

    user_parser = subparsers.add_parser('user', help='User commands')
    user_commands = user_parser.add_subparsers(dest='command')

    group_parser = subparsers.add_parser('group', help='Group commands')
    group_commands = group_parser.add_subparsers(dest='command')

    # User commands
    command = user_commands.add_parser('add', help='Add a user')
    command.add_argument('username')
    command.add_argument('--password', '-p')
    command.add_argument('--cn', metavar="COMMON NAME")
    command.add_argument('--sn', metavar="SURNAME")
    command.add_argument('--givenName')
    command.add_argument('--group', '-g', metavar='PRIMARY GROUP', dest='groupname')
    command.add_argument('--uid', metavar='USER ID')
    command.add_argument('--gid', metavar='GROUP ID')
    command.add_argument('--mail', metavar="EMAIL ADDRESS")
    command.add_argument('--phone', metavar="PHONE NUMBER")
    command.add_argument('--shell')
    command.add_argument('--groups', type=lambda s: s.split(','),
                        help='A comma separated list of group names')
    command.add_argument('--expire', metavar="DAYS",
                        help=('Number of days after which the account expires. '
                            'Set to -1 to disable'))
    command.add_argument('--home', metavar="HOME")

    command = user_commands.add_parser('delete', help='Delete a user')
    command.add_argument('username')

    command = user_commands.add_parser('show', help='Show user details')
    command.add_argument('username')

    command = user_commands.add_parser('modify', help='Modify a user attribute')
    command.add_argument('username')
    command.add_argument('--password', '-p')
    command.add_argument('--cn', metavar="COMMON NAME")
    command.add_argument('--sn', metavar="SURNAME")
    command.add_argument('--givenName')
    command.add_argument('--group', '-g', metavar='PRIMARY GROUP', dest='groupname')
    command.add_argument('--uid', metavar='USER ID')
    command.add_argument('--gid', metavar='GROUP ID')
    command.add_argument('--shell')
    command.add_argument('--mail', metavar="EMAIL ADDRESS")
    command.add_argument('--phone', metavar="PHONE NUMBER")
    command.add_argument('--groups', type=lambda s: s.split(','),
                        help='A comma separated list of group names')
    command.add_argument('--expire', metavar="DAYS",
                        help=('Number of days after which the account expires. '
                            'Set to -1 to disable'))
    command.add_argument('--home', metavar="HOME")

    command = user_commands.add_parser('list', help='List users')

    # Group commands
    command = group_commands.add_parser('add', help='Add a group')
    command.add_argument('groupname')
    command.add_argument('--gid', metavar='GROUP ID')
    command.add_argument('--users', type=lambda s: s.split(','),
                        help='A comma separated list of usernames')
    
    command = group_commands.add_parser('modify', help='Modify a group')
    command.add_argument('groupname')
    command.add_argument('--gid', metavar='GROUP ID')
    command.add_argument('--users', type=lambda s: s.split(','),
                        help='A comma separated list of usernames')

    command = group_commands.add_parser('show', help='Show group details')
    command.add_argument('groupname')

    command = group_commands.add_parser('addusers', help='Add users to a group')
    command.add_argument('groupname')
    command.add_argument('usernames', nargs='+')

    command = group_commands.add_parser('delete', help='Delete a group')
    command.add_argument('groupname')

    command = group_commands.add_parser('delusers',
                                        help='Delete users from a group')
    command.add_argument('groupname')
    command.add_argument('usernames', nargs='+')

    command = group_commands.add_parser('list', help='List groups')

    args = vars(parser.parse_args())
    output = 'json' if args['json'] else 'table'
    obol = Obol('/etc/obol.conf', output=output, overrides=args)

    # Run command

    try:
        method_name = '%s_%s' % (args['target'], args['command'])
        function = getattr(obol, method_name, None)
        function(**args)
    except:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    run()