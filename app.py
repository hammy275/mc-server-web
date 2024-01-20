from flask import Flask, jsonify, redirect, request, send_from_directory, session, url_for
from typing import Any, Union
import os
import requests
import secrets
from subprocess import Popen, CREATE_NEW_CONSOLE
import sys
from urllib.parse import urlencode

import config

app = Flask(__name__)


def make_message(msg: str, code: int):
    return jsonify({"message": msg}), code


def get_val(key: str, default=None):
    return request.json[key] if key in request.json else default


def get_val_err(key: str) -> Any:
    val = get_val(key)
    if val is None:
        return make_message(f"Value {key} not found!", 400)
    return val


def is_user_whitelisted(path: str) -> bool:
    """Whether the current request's user is whitelisted based on the supplied file path.

    Args:
        path: File path to whitelist file. It's okay if the file does not exist.

    Returns:
        Whether the current user is whitelisted in the whitelist, or True if the whitelist isn't found.
    """
    if not os.path.exists(path) or not os.path.isfile(path):
        return True
    with open(path, "r") as f:
        allowed_users = f.read().split(",")
        discord_token = config.session_to_discord_id[session["token"]]
        this_user = config.ALLOWED_USERS[discord_token]
        return this_user in allowed_users or discord_token in config.ADMINS


@app.before_request
def before_request():
    # If GET, handle session (clear token if server restarted, etc.)
    if request.method == "GET":
        if "token" in session and session["token"] not in config.session_to_discord_id:
            session.pop("token")
    elif request.method == "POST":
        if "token" not in session or session["token"] not in config.session_to_discord_id:
            return make_message("Not authenticated!", 403)


@app.route("/")
@app.route("/index.html")
def index():
    return send_from_directory("client", "index.html")


@app.route("/index.js")
def index_js():
    return send_from_directory("client", "index.js")


@app.route("/auth/authorize")
def oauth2_authorize():
    session["state"] = secrets.token_urlsafe(32)
    query_string = urlencode({
        "client_id": config.OAUTH_CLIENT_ID,
        "redirect_uri": url_for("oauth2_redirect", _external=True),
        "response_type": "code",
        "prompt": "none",
        "scope": "identify",
        "state": session["state"]
    })
    return redirect(config.OAUTH_AUTH_URL + "?" + query_string)


@app.route("/auth/redirect")
def oauth2_redirect():
    # If there was an error (expected) or state is missing (unexpected)
    if "error" in request.args or "state" not in request.args:
        return "There was an error (unknown) while logging in!", 500

    # If state mismatches
    if request.args["state"] != session.get("state"):
        return "There was an error (state mismatch) while logging in!", 500

    # If code not found
    if "code" not in request.args:
        return "There was an error (missing code) while logging in!", 500

    # Get access token from authorization code
    r = requests.post(config.OAUTH_TOKEN_URL, data={
        "client_id": config.OAUTH_CLIENT_ID,
        "client_secret": config.OAUTH_CLIENT_SECRET,
        "code": request.args["code"],
        "grant_type": "authorization_code",
        "redirect_uri": url_for("oauth2_redirect", _external=True)
    }, headers={"Accept": "application/json"})
    if r.status_code != 200:
        return "There was an error (failed token retrieval) while logging in!", 500
    token = r.json().get("access_token", None)
    token_type = r.json().get("token_type", None)
    if token is None or token_type is None:
        return "There was an error (token or token type not found) while logging in!", 500

    # Get user ID from token
    r = requests.get(config.API_ENDPOINT + "/users/@me", headers={
        "authorization": f"{token_type} {token}"
    })
    if r.status_code != 200:
        return "There was an error (failed to get user ID) while logging in!", 500
    discord_user_id = r.json()["id"]

    if discord_user_id not in config.ALLOWED_USERS:
        return "You are not authorized to use MC Server Web!", 403

    session_token = secrets.token_urlsafe(128)

    session["token"] = session_token
    session.pop("state")
    to_del = []
    for key in config.session_to_discord_id:
        val = config.session_to_discord_id[key]
        if val == discord_user_id:
            to_del.append(key)
    for key in to_del:
        del config.session_to_discord_id[key]
    config.session_to_discord_id[session_token] = discord_user_id
    config.maybe_write_datastore()

    return redirect(url_for("index"))


@app.route("/api/list", methods=["POST"])
def list_servers():
    servers = []
    for folder in config.SERVER_FOLDERS:
        if not is_user_whitelisted(os.path.join(folder, config.WHITELIST_FILE_NAME)):
            continue
        for f in os.listdir(folder):
            if not is_user_whitelisted(os.path.join(folder, f, config.WHITELIST_FILE_NAME)):
                continue
            if os.path.isdir(os.path.join(folder, f)):
                servers.append(f)
    return jsonify({"message": "Got servers!", "data": sorted(servers)}), 200


@app.route("/api/run", methods=["POST"])
def launch_server():
    name: str = get_val_err("name")
    path: Union[str, None] = None
    for folder in config.SERVER_FOLDERS:
        path = os.path.join(folder, name)
        if os.path.exists(path) and os.path.isdir(path):
            break
        else:
            path = None
    if path is not None and not name.isalnum():  # Before is None check so we don't leak that the path exists
        return make_message(f"Path is not alphanumeric.", 400)
    elif path is None:
        return make_message(f"Path {path} not found! This isn't a server that can be launched.", 404)
    script_path: Union[str, None] = None
    for script_name in config.STARTUP_SCRIPT_NAMES:
        script_path = os.path.join(path, script_name)
        if os.path.exists(script_path) and os.path.isfile(script_path):
            break
        else:
            script_path = None
    if script_path is None:
        return make_message(f"Server does not contain a startup script.", 500)
    try:
        p = Popen(script_path, creationflags=CREATE_NEW_CONSOLE)
    except FileNotFoundError:
        return make_message(f"Failed to start server!", 500)
    if p.poll():
        return make_message(f"Failed to start server!", 500)
    app.logger.info(f"Started server {name}")
    return make_message("Server started!", 200)


if __name__ == "__main__":
    config_err: str = config.verify_and_load_config()
    if config_err:
        app.logger.critical(config_err)
        sys.exit(1)
    app.secret_key = config.FLASK_SECRET_KEY
    app.run("0.0.0.0", config.PORT, debug=True)
