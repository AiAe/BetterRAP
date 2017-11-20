from flask import Flask, make_response, redirect, request, render_template, url_for, flash
import requests
import datetime
from datetime import datetime as dt
import json
from flask_mail import Mail, Message
from helpers import mysql, API

with open("config.json", "r") as f:
    config = json.load(f)

with open("email.json", "r") as f:
    config_email = json.load(f)

app = Flask(__name__)
app.secret_key = 'betterrapisawesome'

app.config['MAIL_SERVER'] = config_email['MAIL_SERVER']
app.config['MAIL_PORT'] = "7337"
app.config['MAIL_USERNAME'] = config_email['MAIL_USERNAME']
app.config['MAIL_PASSWORD'] = config_email['MAIL_PASSWORD']
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_DEFAULT_SENDER'] = config_email['MAIL_USERNAME']
app.config['MAIL_DEBUG'] = True

mail = Mail()
mail.init_app(app)


def send_email(email, d):

    with open("drafts.json", "r") as f:
        draft = json.load(f)

    if d == 0:
        text = draft['accept_appeal_cheating']
    elif d == 1:
        text = draft['accept_appeal_multi']
    elif d == 2:
        text = draft['accept_username']
    elif d == 3:
        text = draft['deny_appeal_multi']
    elif d == 4:
        text = draft['deny_appeal']
    elif d == 5:
        text = draft['deny_username']

    list = []
    list.append(email)

    msg = Message('Ripple Support', recipients=list)
    msg.body = text
    mail.send(msg)


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
                      "INSERT INTO users (user_id, access_token) VALUES (%s, %s)",
                      [user['id'], ripple_token['access_token']])
    except:
        mysql.execute(connection, cursor,
                      "UPDATE users SET access_token = %s WHERE user_id = %s",
                      [ripple_token['access_token'], user['id']])

    return red


@app.route('/oauth/ripple/logout/')
def ripple_logout():
    if API.is_login():

        access_token = request.cookies.get('ACCESS_TOKEN')

        headers = {'Authorization': 'Bearer ' + access_token}

        requests.post('https://ripple.moe/api/v1/tokens/self/delete',
                      headers=headers).json()

        connection, cursor = mysql.connect()
        mysql.execute(connection, cursor, "DELETE from users WHERE access_token = %s",
                      [access_token])

        red = make_response(redirect(url_for('index')))
        red.set_cookie('ACCESS_TOKEN', '', expires=0)
        return red
    else:

        return 'Gotta love hackers...'


@app.route('/')
def index():
    with open("ripple.json", "r") as f:
        ripple_config = json.load(f)

    if API.user_logged_in():
        return redirect(url_for('home'))

    return render_template('login.html', client_id=ripple_config['client_id'],
                           redirect_url=ripple_config['redirect_url'])


@app.route('/home/')
def home():
    if not API.user_logged_in():
        return redirect(url_for('index'))

    user_id = API.api_user_username(API.user_exist()['user_id'])
    user_privilege = API.user_privilege()

    return render_template('home.html', user=user_id, user_privilege=user_privilege)


@app.route('/request/')
def api_user_edit():
    if not request.args:
        return 'I love hackers'

    with open("ripple.json", "r") as f:
        ripple_config = json.load(f)

    params = {
        'token': ripple_config['token'],
    }

    json_data = {
        'id': int(request.args['user_id']),
        'username': str(request.args['username'])
    }

    user = API.api_user_edit(params, json_data)
    u = API.user_exist()
    username = API.api_user_username(u['user_id'])
    connection, cursor = mysql.connect()

    text = 'Changed username from {} to {}'.format(user["username"],request.args['username'])

    API.logging(username, u["user_id"], text)

    mysql.execute(connection, cursor, "DELETE from requests WHERE new_username = %s",
                  [request.args['username']])

    send_email('bgdppeu@gmail.com', 2)

    flash('Changed username from {} to {}.'.format(user["username"],
                                                   request.args['username']))
    return redirect(url_for('manage_usernamechanges'))


@app.route('/banappeal/', methods=['GET', 'POST'])
def request_banappeal():
    if not API.user_logged_in():
        return redirect(url_for('index'))

    user_id = API.api_user_username(API.user_exist()['user_id'])
    user_privilege = API.user_privilege()

    if request.method == 'POST':

        q1 = request.form['q1']
        q2 = request.form['q2']
        q3 = request.form['q3']
        q4 = request.form['q4']
        q5 = request.form['q5']
        q6 = request.form['q6']

        if not all([q1, q2, q3, q4, q5, q6]):
            flash('Please fill everything!')
        else:
            text = "List any and all other accounts you have used or created: {}\n" \
                   "Is this your first time being restricted: {}\n" \
                   "If this isn't your first time being restricted, why were you restricted in the past: {}\n" \
                   "Let us know what caused your most recent restriction/ban: {}\n" \
                   "Why should we allow you back into Ripple? (3-6 sentences): {}\n" \
                   "Write a 1-2 paragraphs (6-12 sentences) about how if we let you back into Ripple, you won't break anymore rules: {}".format(
                q1, q2, q3, q4, q5, q6)

            connection, cursor = mysql.connect()

            try:
                mysql.execute(connection, cursor,
                              "INSERT INTO requests (user_id, username, category, text, date) VALUES (%s, %s, %s, %s, %s)",
                              [user_id, API.api_user_username(user_id), 2, text,
                               datetime.now().strftime('%d.%m.%Y %H:%M')])

                flash('Thanks for appealing, it can take up to 7 days for us to review.')

            except:
                flash("I see you really want to get unrestricted, don't we will review your appeal soon.")

    return render_template('banappeal.html', user=user_id, user_privilege=user_privilege)


@app.route('/namechange/', methods=['GET', 'POST'])
def request_namechange():
    if not API.user_logged_in():
        return redirect(url_for('index'))

    user_id = API.api_user_username(API.user_exist()['user_id'])
    user_privilege = API.user_privilege()

    if request.method == 'POST':

        username = request.form['username']

        if not username:
            flash('Username is empty!')

        if username:
            connection, cursor = mysql.connect()
            try:
                mysql.execute(connection, cursor,
                              "INSERT INTO requests (user_id, username, category, used, new_username, date) VALUES (%s, %s, %s, %s, %s, %s)",
                              [API.user_exist()['user_id'], user_id, 1, 0,
                               username,
                               dt.now().strftime('%d.%m.%Y %H:%M')])
                flash('Your request is added to pending.')
            except:
                flash('You have still pending username change!')

    return render_template('namechange.html', user=user_id, user_privilege=user_privilege)


@app.route('/manage/usernamechanges/')
def manage_usernamechanges():
    if not API.is_chatmod():
        return redirect(url_for('index'))

    user_id = API.api_user_username(API.user_exist()['user_id'])
    user_privilege = API.user_privilege()

    connection, cursor = mysql.connect()
    get_requests = mysql.execute(connection, cursor,
                                 "SELECT * FROM requests WHERE category = 1").fetchall()
    return render_template('manageusernamechanges.html', user=user_id, user_privilege=user_privilege, r=get_requests)


@app.route('/manage/banappeals/')
def manage_banappeals():
    if not API.is_admin():
        return redirect(url_for('index'))

    user_id = API.api_user_username(API.user_exist()['user_id'])
    user_privilege = API.user_privilege()

    connection, cursor = mysql.connect()
    get_requests = mysql.execute(connection, cursor,
                                 "SELECT * FROM requests WHERE category = 2").fetchall()
    return render_template('managebanappeals.html', user=user_id, user_privilege=user_privilege, r=get_requests)


@app.route('/logs/')
def logs():
    if not API.is_admin():
        return redirect(url_for('index'))

    user_id = API.api_user_username(API.user_exist()['user_id'])
    user_privilege = API.user_privilege()

    connection, cursor = mysql.connect()
    get_requests = mysql.execute(connection, cursor,
                                 "SELECT username, text, date FROM logs ORDER BY id desc").fetchall()
    return render_template('logs.html', user=user_id, user_privilege=user_privilege, r=get_requests)


@app.errorhandler(404)
def not_found(error):
    return '404'


if __name__ == "__main__":
    app.run(**config)
