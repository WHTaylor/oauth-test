import uuid
import http
import json
from functools import wraps

import flask
from werkzeug.exceptions import *
import requests
import jwt

AUTH_ROOT = "http://localhost:5000"

app = flask.Flask(__name__)
token_decoder = requests.get(f"{AUTH_ROOT}/public-key").json()


def validate_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        valid, reason = is_auth_valid()
        if not valid:
            error_message = f', error="invalid_token", error_description="{reason}"' if reason else ''
            header = f'Bearer realm="notsurewhatthisis"{error_message}'
            raise Unauthorized("Valid bearer token must be supplied", www_authenticate=header)
        return f(*args,  **kwargs)
    return wrapper

def is_auth_valid():
    auth = flask.request.headers.get("Authorization")
    if not auth:
        return False, None

    scheme, token = auth.split(None, 1)
    if scheme != "Bearer":
        return False, 'Authorization must use "Bearer" scheme'

    try:
        decoded = jwt.decode(token, token_decoder["key"], token_decoder["alg"])
    except jwt.InvalidSignatureError:
        return False, 'Token signature was invalid'
    except jwt.ExpiredSignatureError:
        return False, 'Token has expired'

    return True, None

class ProtectedThing:
    def __init__(self, seq_num, name):
        self.id = seq_num
        self.name = name

things = [
    ProtectedThing(1, "Sam"),
    ProtectedThing(2, "Sally"),
    ProtectedThing(3, "Someone"),
]

things_by_id = { t.id: t for t in things }

@app.route("/protected-things", methods=["GET", "POST"])
@validate_auth
def all_protected_things():
    return flask.jsonify([t.__dict__ for t in things])


@app.route("/protected-things/<int:seq_num>", methods=["GET", "POST"])
@validate_auth
def protected_thing(seq_num):
    try:
        return flask.jsonify(things_by_id[seq_num].__dict__)
    except KeyError:
        flask.abort(404)
