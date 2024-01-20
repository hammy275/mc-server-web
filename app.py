from flask import Flask, jsonify, request
from typing import Any, Union
import logging
import os
from subprocess import Popen, CREATE_NEW_CONSOLE
import sys

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
    config_err: str = config.verify_config()
    if config_err:
        app.logger.critical(config_err)
        sys.exit(1)
    app.run("0.0.0.0", config.PORT, debug=True)
