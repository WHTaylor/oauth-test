import uuid
import http
import json
from functools import wraps

import flask
from werkzeug.exceptions import *
import requests
import jwt

from exceptions import *

AUTH_ROOT = "http://localhost:5000"

app = flask.Flask(__name__)
token_decoding = requests.get(f"{AUTH_ROOT}/decoding-info").json()


def validate_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = flask.request.headers.get("Authorization")
        if not auth:
            raise AuthException()

        scheme, token = auth.split(None, 1)
        if scheme != "Bearer":
            raise InvalidToken('Authorization must use "Bearer" scheme')

        try:
            decoded = jwt.decode(token, token_decoding["key"], token_decoding["alg"])
        except jwt.InvalidSignatureError:
            raise InvalidToken('Token signature was invalid')
        except jwt.ExpiredSignatureError:
            raise InvalidToken('Token has expired')

        if flask.request.method == "POST" and "write" not in decoded["scope"]:
            raise InsufficientScope('POST method requires "write" scope')

        return f(*args, **kwargs)
    return wrapper


top_secret_numbers = [123, 321, 987654321]

@app.route("/numbers", methods=["GET", "POST"])
@validate_auth
def numbers():
    if flask.request.method == "GET":
        return flask.jsonify(top_secret_numbers)
    else:
        val = flask.request.form.get("value")
        if not val:
            raise BadRequest('"value" field must be provided to create a number')
        try:
            top_secret_numbers.append(int(val))
        except ValueError:
            raise BadRequest('"value" field must be a number')

        return flask.jsonify({'id': len(top_secret_numbers) - 1, 'value': val})

@app.errorhandler(AuthException)
def handle_invalid_auth(e):
    return flask.make_response(
        (flask.jsonify(e.to_dict()),
         e.status_code,
         {'WWW-Authenticate': e.to_header_string()}))
