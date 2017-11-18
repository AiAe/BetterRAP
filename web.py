from flask import Flask, make_response, redirect, request, render_template, url_for, flash
import json

with open("config.json", "r") as f:
    config = json.load(f)

app = Flask(__name__)
app.secret_key = ''

@app.route('/')
def index():

    return render_template('login.html')

@app.route('/home/')
def home():

    return render_template('home.html')

@app.errorhandler(404)
def not_found(error):
    return '404'


if __name__ == "__main__":
    app.run(**config)