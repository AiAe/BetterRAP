from flask import Flask, make_response, redirect, request, render_template, url_for, flash
import requests
import datetime
import json

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
    red.set_cookie('USERID', str(user['id']), expires=expire_date)
    red.set_cookie('USERNAME', user['username'], expires=expire_date)
    red.set_cookie('PRIVILEGES', str(user['privileges']), expires=expire_date)

    return red

def is_login():
    ACCESS_TOKEN = request.cookies.get('ACCESS_TOKEN')
    USERID = request.cookies.get('USERID')
    USERNAME = request.cookies.get('USERNAME')
    PRIVILEGES = request.cookies.get('PRIVILEGES')

    if all(v is not None for v in [ACCESS_TOKEN, USERID, USERNAME, PRIVILEGES]):

        return True

    return False

@app.route('/oauth/ripple/logout/')
def ripple_logout():
    if is_login():

        ACCESS_TOKEN = request.cookies.get('ACCESS_TOKEN')

        headers = {'Authorization': 'Bearer ' + ACCESS_TOKEN}

        requests.post('https://ripple.moe/api/v1/tokens/self/delete', headers=headers).json()

        red = make_response(redirect(url_for('index')))

        red.set_cookie('ACCESS_TOKEN', '', expires=0)
        red.set_cookie('USERID', '', expires=0)
        red.set_cookie('USERNAME', '', expires=0)
        red.set_cookie('PRIVILEGES', '', expires=0)

        return red
    else:

        return 'Gotta love hackers...'

@app.route('/')
def index():
    with open("ripple.json", "r") as f:
        ripple_config = json.load(f)

    if is_login():

        return redirect(url_for('home'))

    return render_template('login.html', client_id=ripple_config['client_id'], redirect_url=ripple_config['redirect_url'])

@app.route('/home/')
def home():

    return render_template('home.html')

@app.errorhandler(404)
def not_found(error):
    return '404'


if __name__ == "__main__":
    app.run(**config)