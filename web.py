from flask import Flask, make_response, redirect, request, render_template, url_for, flash
import requests
from datetime import datetime
import json
from helpers import mysql, Privileges

with open("config.json", "r") as f:
    config = json.load(f)

app = Flask(__name__)
app.secret_key = 'betterrapisawesome'


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


def get_privileges(p):
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
        perm = 4

    if (p & Privileges.UserPublic) == 0:
        text = 'Restricted'
        perm = 1

    return text, perm

def is_login(check_for_admin = False):
    ACCESS_TOKEN = request.cookies.get('ACCESS_TOKEN')

    if check_for_admin:
        p, perm = get_privileges(api_user_privileges())



        return ''

    if ACCESS_TOKEN:
        return True

    return False

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
    p, perm = get_privileges(api_user_privileges(u['user_id']))

    return render_template('home.html', user=api_user_username(u['user_id']), p=p,
                           perm=perm)


@app.route('/banappeal/', methods=['GET', 'POST'])
def request_banappeal():
    if not is_login():
        return redirect(url_for('index'))

    u = get_user()
    p, perm = get_privileges(api_user_privileges(u['user_id']))

    return render_template('banappeal.html', user=api_user_username(u['user_id']), p=p,
                           perm=perm)


@app.route('/namechange/', methods=['GET', 'POST'])
def request_namechange():
    if not is_login():
        return redirect(url_for('index'))

    u = get_user()
    p, perm = get_privileges(api_user_privileges(u['user_id']))

    if request.method == 'POST':

        username = request.form['username']

        if not username:
            flash('Username is empty!')

        if username:
            connection, cursor = mysql.connect()
            try:
                mysql.execute(connection, cursor,
                              "INSERT INTO requests (user_id, username, category, used, new_username, date) VALUES (%s, %s, %s, %s, %s, %s)",
                              [u['user_id'], api_user_username(u['user_id']), 1, 0, username,
                               datetime.now().strftime('%d.%m.%Y %H:%M')])
                flash('Your request is added to pending.')
            except:
                flash('You have still pending username change!')

    return render_template('namechange.html', user=api_user_username(u['user_id']),
                           p=p, perm=perm)

@app.route('/manage/usernamechanges/')
def manage_usernamechanges():

    if not is_login():
        return redirect(url_for('index'))

    u = get_user()
    p, perm = get_privileges(api_user_privileges(u['user_id']))

    return render_template('manageusernamechanges.html', user=api_user_username(u['user_id']),
                           p=p, perm=perm)

@app.route('/manage/banappeals/')
def manage_banappeals():

    if not is_login():
        return redirect(url_for('index'))

    u = get_user()
    p, perm = get_privileges(api_user_privileges(u['user_id']))

    return render_template('managebanappeals.html', user=api_user_username(u['user_id']),
                           p=p, perm=perm)

@app.errorhandler(404)
def not_found(error):
    return '404'


if __name__ == "__main__":
    app.run(**config)
