import uuid

import flask
from werkzeug.exceptions import *
import requests
import jwt

AUTH_ROOT = "http://localhost:5000"
RS_ROOT = "http://localhost:3000"
id_param = "client_id=test"
session_cookie = "client_session_id"

app = flask.Flask(__name__)
app.secret_key = b'something very secret'
sessions = {}

def get_end_user_token():
    session_id = flask.request.cookies.get(session_cookie)
    return sessions.get(session_id) if session_id else None

@app.route("/")
def index():
    token = get_end_user_token()

    if token:
        res = requests.get(
            f"{RS_ROOT}/numbers",
            headers={"Authorization": f"Bearer {token}"})

        logged_in_data = str(res.json()) if res.ok else str(res.headers)
    else:
        logged_in_data = None

    resp = flask.make_response(flask.render_template(
        'index.html',
        login_link=f"{AUTH_ROOT}/oauth/authorization?{id_param}&response_type=code",
        logged_in=token is not None,
        logged_in_data=logged_in_data))

    if token is None:
        resp.set_cookie(session_cookie, '', expires=0)

    return resp

@app.route("/foo")
def auth_redirect():
    access_code = flask.request.args.get("code")
    token_resp = requests.post(
            f"{AUTH_ROOT}/oauth/token?code={access_code}&grant_type=authorization_code",
            auth=("test", "very secure"))
    if not token_resp.ok:
        raise InternalServerError(f"Error returned during auth process: {token_resp.reason}")
    session_id = str(uuid.uuid4())
    sessions[session_id] = token_resp.json()["access_token"]
    resp = flask.redirect(flask.url_for("index"))
    resp.set_cookie("client_session_id",  session_id.encode('utf-8'))
    return resp

@app.route("/logout")
def logout():
    session_id = flask.request.cookies.get("client_session_id")
    if session_id and session_id in sessions:
        del sessions[session_id]
    return flask.redirect(flask.url_for("index"))

@app.route("/create-number", methods=["POST"])
def create_number():
    token = get_end_user_token()
    if not token:
        flask.flash("Must be logged in to create numbers")
    else:
        resp = requests.post(
            f'{RS_ROOT}/numbers',
            data={'value': flask.request.form['num_val']},
            headers={"Authorization": f"Bearer {token}"})
        app.logger.info(resp.status_code)
        app.logger.info(resp.reason)
        app.logger.info(resp.text)
        app.logger.info(resp.headers)
        app.logger.info("Header type:")
        app.logger.info(type(resp.headers))

        if resp.ok:
            body = resp.json()
            flask.flash(f"Successfully created number: {body}")
        else:
            header = resp.headers.get("WWW-Authenticate")
            error = f'{resp.status_code} {resp.reason}'
            message = f"Number creation failed - {error}" + f': {header}' if header else ''
            flask.flash(message)

    return flask.redirect(flask.url_for('index'))

