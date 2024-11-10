from flask import Flask, jsonify, redirect, render_template, request, send_from_directory, session, url_for, make_response
from typing import Any, Union
import os
import psutil
import requests
import secrets
from subprocess import DEVNULL, PIPE, Popen, CREATE_NO_WINDOW, TimeoutExpired, NORMAL_PRIORITY_CLASS
import sys
from urllib.parse import urlencode
from time import sleep

import config
from Server import Server

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


def is_user_whitelisted(server: Server) -> bool:
    """Whether the current request's user is whitelist for this server.

    Args:
        server: Server to check for whitelist.

    Returns:
        Whether the current user is whitelisted in the whitelist.
    """
    token = get_cookie("token")
    this_user = config.name_from_token(token)
    discord_token = config.token_to_discord_id[token]
    return this_user in server.users or discord_token in config.ADMINS


def send_command(process: Popen, command: str):
    """Run a command on a given process representing a Minecraft server.

    Args:
        process: Process instance for a Minecraft server.
        command: The command to run.

    """
    process.stdin.write(command + "\n")
    process.stdin.flush()


def get_cookie(name: str, default: Any = None):
    """Get a cookie from the current request, or return default if the cookie isn't found.

    Args:
        name: Cookie to get
        default: Value to return if cookie isn't found. Defaults to None.

    Returns:
        The cookie value for the given name, or the value supplied to default if not found.
    """
    if name in request.cookies:
        return request.cookies.get(name)
    else:
        return default


@app.before_request
def before_request():
    # If GET, handle the token (clear token if server restarted, etc.)
    token = get_cookie("token")
    if request.method == "GET":
        if token is not None and token not in config.token_to_discord_id:
            resp = redirect(url_for("index"))
            resp.delete_cookie("token")
            return resp
    elif request.method == "POST":
        if token is None or token not in config.token_to_discord_id:
            resp = make_message("Not authenticated!", 403)
            if token is not None:
                resp[0].delete_cookie("token")
            return resp
    else:
        return make_message("Method not supported!", 405)


@app.route("/")
@app.route("/index.html")
def index():
    token = get_cookie("token")
    name = config.name_from_token(token)
    return render_template("index.html",
                           logged_in=token is not None,
                           name=name if name is not None else "",
                           admin=config.is_admin(token))


@app.route("/index.js")
def index_js():
    return send_from_directory("static", "index.js")


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

    token = secrets.token_urlsafe(128)

    session.pop("state")
    to_del = []
    for key in config.token_to_discord_id:
        val = config.token_to_discord_id[key]
        if val == discord_user_id:
            to_del.append(key)
    for key in to_del:
        del config.token_to_discord_id[key]
    config.token_to_discord_id[token] = discord_user_id
    config.maybe_write_datastore()

    resp = redirect(url_for("index"))
    resp.set_cookie("token", token, max_age=60*60*24*30)
    return resp


@app.route("/auth/logout", methods=["POST"])
def logout():
    resp = make_message("Logged out!", 200)
    resp[0].delete_cookie("token")
    return resp


@app.route("/api/refresh_servers", methods=["POST"])
def refresh_servers():
    if not config.is_admin(get_cookie("token")):
        return make_message("Only admins can refresh the list of available servers!", 403)
    else:
        config.load_servers()
        config.maybe_poll_running_servers(True)
        return make_message("Servers refreshed!", 200)


@app.route("/api/list", methods=["POST"])
def list_servers():
    config.maybe_poll_running_servers()
    servers = []
    with config.servers_lock:
        for server in config.servers:
            if is_user_whitelisted(server):
                servers.append(server.get_data())
    return jsonify({"message": "Got servers!", "data": sorted(servers, key=lambda s: s["name"])}), 200


@app.route("/api/manage", methods=["POST"])
def manage_server():
    name: str = get_val_err("name")
    action: str = get_val_err("action")
    if action not in ["start", "stop"]:
        return make_message(f"Invalid server action!", 400)

    server = config.get_server_by_name(name)
    if server is None or not is_user_whitelisted(server):
        return make_message(f"Server {name} not found!", 404)

    # Ifs for which action we're performing
    if action == "start":
        with config.start_server_lock:
            config.maybe_poll_running_servers(force_poll=True)
            if name in config.running_servers:
                return make_message(f"Server {name} already running!", 400)
            script_path: Union[str, None] = None
            for script_name in config.STARTUP_SCRIPT_NAMES:
                script_path = os.path.join(server.folder_path, script_name)
                if os.path.exists(script_path) and os.path.isfile(script_path):
                    break
                else:
                    script_path = None
            if script_path is None:
                return make_message(f"Server does not contain a startup script.", 500)
            try:
                # stdout and stderr MUST be sent to DEVNULL. From testing:
                # Vanilla 1.20.4 servers don't boot if stdout and stderr aren't sent somewhere
                # Forge 1.20.1 servers don't boot if stdout or stderr are sent to PIPE
                # Haven't checked whether "stdout and stderr" is an "or" instead.
                args = [script_path]
                if script_path.endswith(".ps1"):
                    args = ["powershell.exe", script_path]
                p = Popen(args, cwd=server.folder_path, stdin=PIPE, stdout=DEVNULL, stderr=DEVNULL,
                          creationflags=CREATE_NO_WINDOW | NORMAL_PRIORITY_CLASS, universal_newlines=True)
                server.process = p
            except FileNotFoundError:
                return make_message(f"Failed to start server!", 500)
            if p.poll():
                return make_message(f"Failed to start server!", 500)
            with config.running_servers_lock:
                config.running_servers[name] = server
            app.logger.info(f"Started server {name}")
            return make_message("Server started!", 200)
    elif action == "stop":
        config.maybe_poll_running_servers()
        if name not in config.running_servers:
            return make_message(f"Server {name} not running!", 400)
        proc = config.running_servers[name].process
        try:
            proc.communicate(input="stop\n", timeout=10)
        except TimeoutExpired:
            has_java = False
            try:
                shell_process = psutil.Process(proc.pid)
                shell_children = shell_process.children(recursive=True)
                java_child = None
                for child in shell_children:
                    if "java" in os.path.basename(child.exe()):
                        has_java = True
                        java_child = child
                        break
            except psutil.NoSuchProcess:
                pass
            if has_java:
                sleep(10)  # Give the server an extra 10 seconds in case it's still saving (unlikely)
                if java_child is not None:
                    java_child.kill()
                proc.kill()
            else:
                proc.kill()  # No Java found, so the server is definitely gone. Kill it ASAP.
        return make_message("Server stopped!", 200)


@app.route("/api/run_command", methods=["POST"])
def run_command():
    token: str = get_cookie("token")
    name: str = get_val_err("name")
    command: str = get_val_err("command")
    if not config.is_admin(token):
        return make_message("Commands can only be run by admins!", 403)
    with config.running_servers_lock:
        if name not in config.running_servers:
            return make_message("Server not found or not running!", 404)
        server: Server = config.running_servers[name]
        send_command(server.process, command)
        return make_message("Ran command successfully!", 200)


if __name__ == "__main__":
    config_err: str = config.startup()
    if config_err:
        app.logger.critical(config_err)
        sys.exit(1)
    app.secret_key = config.FLASK_SECRET_KEY
    app.run("0.0.0.0", config.PORT)
