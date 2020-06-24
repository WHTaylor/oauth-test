import time
import http
import uuid
from collections import defaultdict

import flask
from werkzeug.exceptions import *
import jwt

import data

app = flask.Flask(__name__)
app.secret_key = b"secret bytes no one can see"

TOKEN_EXPIRY_SECONDS = 30

outstanding_codes = defaultdict(dict)

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
        return flask.render_template("auth_form.html", client_name=client.id)

    elif flask.request.method == "POST":
        if flask.request.form.get('reject-btn') is not None:
            return flask.redirect(
                add_query_params(client.redirect_url, {'error': 'access_denied'}))

        un = flask.request.form.get('username')
        pw = flask.request.form.get('password')
        if data.user_credentials_valid(un, pw):
            access_code = uuid.uuid4()
            outstanding_codes[client.id][access_code] = un
            return flask.redirect(
                add_query_params(client.redirect_url, {"code": access_code}),
                code=http.client.FOUND)
        else:
            flask.flash("Invalid credentials")
            return flask.render_template("auth_form.html", client_name=client.id)


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

    client_codes = outstanding_codes[auth.username]
    code = uuid.UUID(flask.request.args.get("code"))
    if not code or code not in client_codes:
        raise BadRequest("Invalid authorization grant code")
    user = data.users_by_name[client_codes[code]]
    token = jwt.encode({
            "some": "claims",
            "exp": int(time.time()) + TOKEN_EXPIRY_SECONDS,
            "scope": "read" + " write" if user.write_permissions else ""
        },
        data.private_key(),
        # jwt encodes as bytes, have to decode to serialize as JSON
        algorithm="RS256").decode()

    del client_codes[code]

    return no_caching(flask.make_response({
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": TOKEN_EXPIRY_SECONDS
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

def add_query_params(url, params):
    param_string = "&".join(f"{k}={v}" for k, v in params.items())
    if "?" in url:
        return f"{url}&{param_string}"
    else:
        return f"{url}?{param_string}"
