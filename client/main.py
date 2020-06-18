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
sessions = {}

@app.route("/")
def index():
    session_id = flask.request.cookies.get(session_cookie)
    delete_cookie = False
    if session_id not in sessions:
        delete_cookie = True
        session_id = None

    if not session_id:
        body = f'<a href="{AUTH_ROOT}/oauth/authorization?{id_param}&response_type=code">Login</a>'
    else:
        token = sessions[session_id]
        logout_url = flask.url_for("logout")
        body = f'<a href="{logout_url}">Logout</a>'
        res = requests.get(
            f"{RS_ROOT}/protected-things",
            headers={"Authorization": f"Bearer {token}"})
        if res.ok:
            body += "<br>" + str(res.json())
        else:
            body += "<br>" + res.text + "<br>" + str(res.headers)
    resp = flask.make_response(body)
    if delete_cookie:
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
