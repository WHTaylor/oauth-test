# OAuth 2.0 examples

This system implements a small, core subset of the OAuth 2.0 framework as a trio of example web applications, built with python and flask.

Requires python3. Install dependencies with `pip install -r requirements.txt` - a virtual environment is highly recommended (ie `python -m venv venv`, and run the appropriate activate script). If you have bash available, `run_all` will start each of the three applications in a separate job under a single process, after you've created a venv. Otherwise you'll need to run them manually with `flask run` and the env variables set in `run_all`.

## Apps and their endpoints

 - `/auth`: The Authentication Server, runs on `localhost:5000`
   - `/outh/authorization` (POST + GET): The client redirects the user-agent here. If the user provides valid credentials, redirects back to the client with an authorization grant.
   - `/outh/token` (POST): The client can request an access token by sending a valid authorization grant and it's own credetials to this endpoint.
   - `/decoding-info`: Exposes the public key and algorithm required for the resource server to verify access tokens' signatures.

 - `/client`: The Client, runs on `localhost:4000`
   - `/`: If not logged in, will provide a link to login which redirects to the `authorization` endpoint. If logged in, will try to use the associated access token to get `/numbers` from the resource server, and displays them/any errors which occur.
   - `/redirect`: The clients redirect url. Authorization code comes in, access token is acquired, then user-agent is redirected back to the home page but now has an associated access token.
   - `/logout`: Deletes the user-agent session cookie, requiring them to login again to access protected resources.
   - `/create-number`: Basically a proxy to the resource servers POST `/numbers` endpoint.

 - `/resource-server`: A Resource Server, runs on `localhost:3000`
   - `/numbers` (POST + GET): The way to access the protected data. Only a logged in user can GET this endpoint, and only a user with a token with 'write' scope can POST to it (this latter may be an abuse of scope parameters, I'm not sure). Returns fully compliant responses on auth failures (I think).

## Notes

User and client credentials are in `/auth/data.py`. You'll need to generate an RSA key pair, with filenames `public` and `private`, in `/auth/keys`, or just ask me for the private key, it's not really important to keep secret I just didn't include it in the repo on principle.

These implementations are mostly compliant with the specification, with some omissions:
 - Does not use TLS/HTTPS, which is imperative for production use (tokens are not cryptographically secure) but I didn't fancy setting up on localhost.
 - The authentication server doesn't quite return the correct errors from the `token` endpoint.
 - I'm not sure the usage of GET/POST for the auth `authorization` endpoint is totally up to spec - I'm not sure the usage of GET fulfills 'The authorization server MUST support the use of the HTTP "GET" method [RFC2616] for the authorization endpoint'.
 - Possibly more I missed.

The next most applicable things to implement are probably refresh tokens, the client credentials flow, and an app that is both a Client and a Resource Server, AKA what Schedule, vists, proposals etc, will be.
