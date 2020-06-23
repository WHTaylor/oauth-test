import time
import os
import datetime
import http
import uuid
from collections import defaultdict

import flask
from werkzeug.exceptions import *
import jwt

import data

app = flask.Flask(__name__)
app.secret_key = b"secret bytes no one can see"
outstanding_codes = defaultdict(dict)

@app.route("/")
def index():
    return "will have client management stuff"


@app.route("/oauth/authorization", methods=["GET", "POST"])
def authorize():
    response_type = flask.request.args.get("response_type")
    if not response_type or response_type != "code":
        raise BadRequest("Authorization request must include response_type parameter"\
                         " as a query parameter. Only 'code' is currently allowed.")

    client = data.clients.get(flask.request.args.get("client_id"))
    if not client:
        raise BadRequest("Authorization request must include a client_id for an existing client as a query parameter")

    if flask.request.method == "GET":
        # TODO: Try to get existing session as credentials
        return flask.render_template("auth_form.html")
    elif flask.request.method == "POST":
        un, pw =  flask.request.form['username'], flask.request.form['password']
        if data.user_credentials_valid(un, pw):
            print(un, pw)
            # Hack: This should be cryptographically secure
            code = uuid.uuid4()
            outstanding_codes[client.id][code] = un
            # Hack: shoudln't assume no query params in redirect url
            return flask.redirect(f"{client.redirect_url}?code={code}",
                                  code=http.client.SEE_OTHER)
        else:
            return "Invalid credentials (this should be a nice little notification)"
    else:
        return "How'd you get here"


@app.route("/oauth/token", methods=["POST"])
def token():
    # TODO: Proper errors
    grant_type = flask.request.args.get("grant_type")
    if not grant_type or grant_type != "authorization_code":
        raise BadRequest("Token request must be before authorization_code grant type")

    auth = flask.request.authorization
    if not auth or not auth.username or not auth.password:
        raise BadRequest("Client must authorize with HTTP basic auth.")

    if not data.client_credentials_valid(auth):
        raise BadRequest("Client credentials invalid.")

    # TODO: Code expiry
    client_codes = outstanding_codes[auth.username]
    code = uuid.UUID(flask.request.args.get("code"))
    if not code or code not in client_codes:
        raise BadRequest("Invalid authorization grant code")
    token = generate_token(data.users_by_name[client_codes[code]])
    del client_codes[code]

    return no_caching(flask.make_response({
        "access_token": token,
        "token_type": "Bearer"
    }))


@app.route("/decoding-info")
def decoding_info():
    return {
        "key": data.public_key(),
        "alg": "RS256",
    }

def no_caching(resp):
    resp.headers.set("Cache-Control", "no-store")
    resp.headers.set("Pragma", "no-cache")
    return resp

def generate_token(user):
    print(user)
    return jwt.encode({
            "some": "claims",
            "exp": int(time.time()) + 30,
            "scope": "read" + " write" if user.write_permissions else ""
        },
        data.private_key(),
        algorithm="RS256").decode()   # jwt is encoding to bytes, which can't be JSON serialized
