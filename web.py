from flask import Flask, make_response, redirect, request, render_template, url_for, flash
import requests
import datetime
import json
from helpers import mysql, Privileges

with open("config.json", "r") as f:
    config = json.load(f)

app = Flask(__name__)
app.secret_key = ''


@app.route('/oauth/ripple/')
def ripple_aouth():
    with open("ripple.json", "r") as f:
        ripple_config = json.load(f)

    if not request.args:
        return 'I love hackers'

    data = {
        'client_id': ripple_config['client_id'],
        'client_secret': ripple_config['client_secret'],
        'grant_type': 'authorization_code',
        'code': request.args['code'],
    }

    ripple_token = requests.post("https://ripple.moe/oauth/token", data=data).json()

    headers = {'Authorization': 'Bearer ' + ripple_token['access_token']}

    user = requests.get('https://ripple.moe/api/v1/users/self', headers=headers).json()

    expire_date = datetime.datetime.now()
    expire_date = expire_date + datetime.timedelta(days=1)

    red = make_response(redirect('/'))
    red.set_cookie('ACCESS_TOKEN', ripple_token['access_token'], expires=expire_date)

    connection, cursor = mysql.connect()

    try:
        mysql.execute(connection, cursor,
                      "INSERT INTO users (user_id, username, privileges, access_token) VALUES (%s, %s, %s, %s)",
                      [user['id'], user['username'], user['privileges'],
                       ripple_token['access_token']])
    except:
        mysql.execute(connection, cursor,
                      "UPDATE users SET access_token = %s WHERE user_id = %s",
                      [ripple_token['access_token'], user['id']])

        return 'User in db...'

    return red


def is_login():
    ACCESS_TOKEN = request.cookies.get('ACCESS_TOKEN')

    if ACCESS_TOKEN:
        return True

    return False


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


def get_privileges(p):
    text = ''
    staff = 0

    if (p & Privileges.UserNormal) > 0:
        text = 'User'

    if (p & Privileges.AdminChatMod) > 0:
        text = 'Chat mod'
        staff = 1

    if (p & Privileges.AdminBanUsers) > 0:
        text = 'Community Manager'
        staff = 2

    if (p & Privileges.AdminManagePrivileges) > 0:
        text = 'Developer'
        staff = 2

    if (p & Privileges.UserPublic) == 0:
        text = 'Restricted'

    return text, staff


@app.route('/oauth/ripple/logout/')
def ripple_logout():
    if is_login():

        ACCESS_TOKEN = request.cookies.get('ACCESS_TOKEN')

        headers = {'Authorization': 'Bearer ' + ACCESS_TOKEN}

        requests.post('https://ripple.moe/api/v1/tokens/self/delete',
                      headers=headers).json()

        connection, cursor = mysql.connect()
        mysql.execute(connection, cursor, "DELETE from users WHERE access_token = %s",
                      [ACCESS_TOKEN])

        red = make_response(redirect(url_for('index')))
        red.set_cookie('ACCESS_TOKEN', '', expires=0)
        return red
    else:

        return 'Gotta love hackers...'


@app.route('/')
def index():
    with open("ripple.json", "r") as f:
        ripple_config = json.load(f)

    if is_login():
        return redirect(url_for('home'))

    return render_template('login.html', client_id=ripple_config['client_id'],
                           redirect_url=ripple_config['redirect_url'])


@app.route('/home/')
def home():
    if not is_login():
        return redirect(url_for('index'))

    u = get_user()
    p, staff = get_privileges(u['privileges'])

    return render_template('home.html', user=get_user(), p=p, staff=staff)


@app.errorhandler(404)
def not_found(error):
    return '404'


if __name__ == "__main__":
    app.run(**config)
