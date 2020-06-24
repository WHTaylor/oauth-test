from urllib.parse import quote as encode_url
import os

class Client:
    def __init__(self, client_id, redirect_url, password):
        self.id = client_id
        self.redirect_url = redirect_url
        self.password = password

# These will be registered dynamically
clients = {
    c.id: c for c in [
        Client("example-client", "http://localhost:4000/redirect", "very secure")
    ]
}


class User:
    def __init__(self, user_id, user_name, password, write_permissions):
        self.id = user_id
        self.name = user_name
        self.password = password
        self.write_permissions = write_permissions

users = [
    User(1, "user", "plaintext", False),
    User(2, "admin", "abc123", True),
]

users_by_name = {
    u.name: u for u in users
}

# Yes everything is plaintext
def user_credentials_valid(username, password):
    u = users_by_name.get(username)
    return u is not None and u.password == password

def client_credentials_valid(basic_auth):
    c = clients.get(basic_auth.username)
    return c is not None and c.password == basic_auth.password

keys_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys")
_public_key = None
_private_key = None
def public_key():
    global _public_key
    if _public_key is None:
        with open(os.path.join(keys_dir, "public"), "r") as f:
            _public_key = f.read()
    return _public_key

def private_key():
    global _private_key
    if _private_key is None:
        with open(os.path.join(keys_dir, "private"), "r") as f:
            _private_key = f.read()
    return _private_key
