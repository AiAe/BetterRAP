from flask import request
import requests
from datetime import datetime
from helpers import mysql, Privileges


def api_user_username(user_id):
    user = requests.get('https://ripple.moe/api/v1/users', params={'id': user_id}).json()

    return user['username']


def api_user_privileges(user_id):
    user = requests.get('https://ripple.moe/api/v1/users', params={'id': user_id}).json()

    return user['privileges']


def api_user_edit(params, json_data):
    return requests.post('https://ripple.moe/api/v1/users/edit', params=params,
                         json=json_data).json()


def user_logged_in():
    access_token = request.cookies.get('ACCESS_TOKEN')

    if access_token:
        return True

    return False


def user_exist():
    if user_logged_in():

        connection, cursor = mysql.connect()
        access_token = request.cookies.get('ACCESS_TOKEN')

        result = mysql.execute(connection, cursor, "SELECT user_id, perm FROM users WHERE access_token = %s",
                               [access_token]).fetchone()

        if result and len(result) > 0:
            return result

    return False


def user_privilege():
    if not user_exist():
        return {'perm': 0, 'badge': 'Nothing'}

    p = api_user_privileges(user_exist()['user_id'])

    if (p & Privileges.UserNormal) > 0:
        badge = {'perm': 1, 'badge': 'User'}

    if (p & Privileges.AdminChatMod) > 0:
        badge = {'perm': 1, 'badge': 'Chat Mod'}

    if (p & Privileges.AdminBanUsers) > 0:
        badge = {'perm': 3, 'badge': 'Community Manager'}

    if (p & Privileges.AdminManagePrivileges) > 0:
        badge = {'perm': 3, 'badge': 'Developer'}

    if (p & Privileges.UserPublic) == 0:
        badge = {'perm': 69, 'badge': 'Restricted'}

    return badge


def is_chatmod():

    user_perm = user_exist()['perm']

    if user_perm == 2:

        return True

    return False


def is_admin():
    p = user_privilege()

    if p['perm'] >= 3:
        return True

    return False


def logging(username, user_id, text):
    connection, cursor = mysql.connect()

    mysql.execute(connection, cursor,
                  "INSERT INTO logs (username, user_id, text, date) VALUES (%s, %s, %s, %s)",
                  [username, user_id, text,
                   datetime.now().strftime('%d.%m.%Y %H:%M')])
