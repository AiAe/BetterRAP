import requests
from helpers import mysql, Privileges
from flask import request

def get_user():
    connection, cursor = mysql.connect()

    ACCESS_TOKEN = request.cookies.get('ACCESS_TOKEN')

    if ACCESS_TOKEN:
        user = mysql.execute(connection, cursor,
                             "SELECT * FROM users WHERE access_token = %s",
                             [ACCESS_TOKEN]).fetchone()

        return user
    else:
        return 'ERROR'


def api_user_username(user_id):
    user = requests.get('https://ripple.moe/api/v1/users', params={'id': user_id}).json()

    return user['username']


def api_user_privileges(user_id):
    user = requests.get('https://ripple.moe/api/v1/users', params={'id': user_id}).json()

    return user['privileges']


def get_privileges():
    p = api_user_privileges(get_user()['user_id'])
    text = ''
    perm = 0

    if (p & Privileges.UserNormal) > 0:
        text = 'User'
        perm = 1

    if (p & Privileges.AdminChatMod) > 0:
        text = 'Chat mod'
        perm = 2

    if (p & Privileges.AdminBanUsers) > 0:
        text = 'Community Manager'
        perm = 3

    if (p & Privileges.AdminManagePrivileges) > 0:
        text = 'Developer'
        perm = 3

    if (p & Privileges.UserPublic) == 0:
        text = 'Restricted'
        perm = 1

    return text, perm


def is_login(check_for_admin=False):
    ACCESS_TOKEN = request.cookies.get('ACCESS_TOKEN')

    if check_for_admin:
        p, perm = get_privileges()

        if perm >= 3:
            return True

        return False

    if ACCESS_TOKEN:
        return True

    return False
