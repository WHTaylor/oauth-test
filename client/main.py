import uuid

import flask
from werkzeug.exceptions import *
import requests
import jwt

AUTH_ROOT = "http://localhost:5000"
RS_ROOT = "http://localhost:3000"
client_id = "example-client"
session_cookie = "client_session_id"

app = flask.Flask(__name__)
app.secret_key = b'something very secret'
sessions = {}

@app.route("/")
def index():
    token = get_end_user_token()

    if token:
        res = requests.get(
            f"{RS_ROOT}/numbers",
            headers={"Authorization": f"Bearer {token}"})

        data = str(res.json()) if res.ok else str(res.headers)
    else:
        data = None

    resp = flask.make_response(flask.render_template(
        'index.html',
        login_link=f"{AUTH_ROOT}/oauth/authorization?client_id={client_id}&response_type=code",
        logged_in=token is not None,
        data=data))

    if token is None:
        resp.set_cookie(session_cookie, '', expires=0)

    return resp

@app.route("/redirect")
def auth_redirect():
    error = flask.request.args.get("error")
    if error:
        flask.flash(f"Authorization failed with: {error}")
        return flask.redirect(flask.url_for('index'))

    access_code = flask.request.args.get("code")
    token_resp = requests.post(
            f"{AUTH_ROOT}/oauth/token?code={access_code}&grant_type=authorization_code",
            auth=(client_id, "very secure"))
    if not token_resp.ok:
        raise InternalServerError(f"Error returned during auth process: {token_resp.reason}")
    session_id = str(uuid.uuid4())
    sessions[session_id] = token_resp.json()["access_token"]
    resp = flask.redirect(flask.url_for("index"))
    resp.set_cookie("client_session_id",  session_id.encode("utf-8"))
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

        if resp.ok:
            body = resp.json()
            flask.flash(f"Successfully created number: {body}")
        else:
            header = resp.headers.get("WWW-Authenticate")
            error = f'{resp.status_code} {resp.reason}'
            message = f"Number creation failed - {error}" + f': {header}' if header else ''
            flask.flash(message)

    return flask.redirect(flask.url_for('index'))


def get_end_user_token():
    session_id = flask.request.cookies.get(session_cookie)
    return sessions.get(session_id) if session_id else None
