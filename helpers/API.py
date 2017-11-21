from flask import request
import requests
import json
from datetime import datetime
from helpers import mysql

path = ''
path = '/home/ubuntu/CONFIG/'

with open(path + "ripple.json", "r") as f:
    ripple_config = json.load(f)


def api_user_full(user_id):
    user = requests.get('https://api.ripple.moe/api/v1/users/full',
                        params={'id': user_id, 'token': ripple_config['token']}).json()

    return user


def api_user_username(user_id):
    user = requests.get('https://api.ripple.moe/api/v1/users',
                        params={'id': user_id, 'token': ripple_config['token']}).json()

    return user


def api_user_check(username):
    user = requests.get('https://api.ripple.moe/api/v1/users',
                        params={'name': username, 'token': ripple_config['token']}).json()

    if int(user["code"]) == 404:
        return False

    else:
        return True


def api_osu_user_check(username):
    user = requests.get('https://osu.ppy.sh/api/get_user', params={'u': username, 'k': ripple_config['osu_api']}).json()
    print(user)
    if user:

        return True

    else:

        return False


def api_user_privileges(user_id):
    user = requests.get('https://api.ripple.moe/api/v1/users',
                        params={'id': user_id, 'token': ripple_config['token']}).json()

    return user['privileges']


def api_user_edit(params, json_data):
    return requests.post('https://api.ripple.moe/api/v1/users/edit', params=params,
                         json=json_data).json()


def user_in_db(user_id):
    connection, cursor = mysql.connect()

    result = mysql.execute(connection, cursor, "SELECT user_id FROM requests WHERE user_id = %s",
                           [user_id]).fetchone()

    if result and len(result) > 0:
        return True

    return False


def user_logged_in():
    access_token = request.cookies.get('ACCESS_TOKEN')

    if access_token:

        connection, cursor = mysql.connect()

        user = mysql.execute(connection, cursor, "SELECT user_id, perm FROM users WHERE access_token = %s",
                             [access_token]).fetchone()

        perm = api_user_privileges(user['user_id'])

        if (perm & 1) == 0:
            mysql.execute(connection, cursor, "UPDATE users SET perm = %s WHERE access_token = %s", [0, access_token])

        else:
            if user['perm'] == 0:
                mysql.execute(connection, cursor, "UPDATE users SET perm = %s WHERE access_token = %s",
                              [1, access_token])

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

    user_perm = user_exist()['perm']

    if user_perm == 0:
        badge = {'perm': 0, 'badge': 'Restricted'}

    if user_perm == 1:
        badge = {'perm': 1, 'badge': 'User'}

    if user_perm == 2:
        badge = {'perm': 2, 'badge': 'Chat Mod'}

    if user_perm == 3:
        badge = {'perm': 3, 'badge': 'Community Manager'}

    if user_perm == 4:
        badge = {'perm': 4, 'badge': 'Developer'}

    return badge


def is_restricted():
    user_perm = user_exist()['perm']

    if user_perm == 0:
        return True

    return False


def is_user():
    user_perm = user_exist()['perm']

    if user_perm >= 1:
        return True

    return False


def is_chatmod():
    user_perm = user_exist()['perm']

    if user_perm >= 2:
        return True

    return False


def is_admin():
    user_perm = user_exist()['perm']

    if user_perm >= 3:
        return True

    return False


def logging(username, user_id, text):
    connection, cursor = mysql.connect()

    mysql.execute(connection, cursor,
                  "INSERT INTO logs (username, user_id, text, date) VALUES (%s, %s, %s, %s)",
                  [username, user_id, text,
                   datetime.now().strftime('%d.%m.%Y %H:%M')])
