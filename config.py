import json
import logging
import os
import sys
from threading import Lock
import time
from typing import List, Type, Union

from RunningServer import RunningServer


def get_env(key: str, typ: Type) -> any:
    value = os.getenv(key, default=None)
    if value is None:
        logging.critical(f"Environment variable {key} not provided!")
        sys.exit(1)
    if not isinstance(key, typ):
        try:
            value = typ(value)
        except ValueError:
            logging.critical(f"Value {value} from environment variable {key} cannot be converted to new type.")
    return value


# User-Configured Settings

# Port to run this web server on. Example: "25565".
PORT: int = get_env("MC_SERVER_WEB_PORT", int)
# Comma-separated list of all folders that servers are contained in. Example: "C:\MyDir1,C:\MyDir2"
SERVER_FOLDERS: List[str] = get_env("MC_SERVER_WEB_FOLDERS", str).split(",")
# Comma-separated list of all names of potential startup scripts to start the server. Example: "run.bat,start.bat"
STARTUP_SCRIPT_NAMES: List[str] = get_env("MC_SERVER_WEB_SCRIPTS", str).split(",")
# OAuth Client ID from the Discord application.
OAUTH_CLIENT_ID = get_env("MC_SERVER_WEB_OAUTH_CLIENT_ID", str)
# OAuth Client Secret from the Discord application.
OAUTH_CLIENT_SECRET = get_env("MC_SERVER_WEB_OAUTH_CLIENT_SECRET", str)
# Redirect URI. Example: http://mydomain.com/auth/redirect
OAUTH_REDIRECT_URI = get_env("MC_SERVER_WEB_OAUTH_REDIRECT_URI", str)
# Flask secret key. Can be anything. Example: The output of secrets.token_urlsafe(32)
FLASK_SECRET_KEY = get_env("MC_SERVER_WEB_FLASK_SECRET_KEY", str)
# Datastore file name. Used to store the session_to_discord_id map to persist between server restarts.
DATASTORE_NAME = "datastore.json"
# Maximum number of lines to send from the log to clients
MAX_LOG_LINES = 10

# End User-Configured Settings

OAUTH_AUTH_URL = "https://discord.com/oauth2/authorize"
OAUTH_TOKEN_URL = "https://discord.com/api/oauth2/token"
API_ENDPOINT = "https://discord.com/api/v10"
ALLOWED_USERS: dict[str, str] = {}  # Key is Discord ID, value is friendly name
ADMINS: dict[str, str] = {}  # Same format as ALLOWED_USERS
WHITELIST_FILE_NAME = "mc_server_web.txt"

session_to_discord_id: dict[str, str] = {}  # Key is sessions sent to web clients, value is Discord IDs
last_datastore_write: int = 0
running_servers: dict[str, RunningServer] = {}
last_server_poll: int = 0
running_servers_lock = Lock()

# Expand vars for server folders
for i in range(len(SERVER_FOLDERS)):
    SERVER_FOLDERS[i] = os.path.expanduser(os.path.expandvars(SERVER_FOLDERS[i]))


def maybe_poll_running_servers():
    global last_server_poll
    current_time = time.time()
    if current_time - last_server_poll > 3:
        last_server_poll = current_time
        running_servers_lock.acquire()
        to_remove = []
        for name, running_server in running_servers.items():
            process = running_server.process
            if process.poll() is not None:
                to_remove.append(name)
        for name in to_remove:
            del running_servers[name]
        for name, running_server in running_servers.items():
            logs_path = os.path.join(running_server.folder_path, "logs")
            if os.path.isdir(logs_path):
                log_path = os.path.join(logs_path, "latest.log")
                if os.path.isfile(log_path):
                    with open(log_path, "r") as f:
                        lines = f.readlines()
                        if len(lines) >= MAX_LOG_LINES:
                            lines = lines[-MAX_LOG_LINES:]
                        running_server.last_log_lines = "".join(lines)
        running_servers_lock.release()


def maybe_write_datastore():
    global last_datastore_write
    current_time = time.time()
    if current_time - last_datastore_write > 10:
        last_datastore_write = current_time
        with open(DATASTORE_NAME, "w") as f:
            f.write(json.dumps(session_to_discord_id))


def name_from_session_token(token: str) -> Union[str, None]:
    if token not in session_to_discord_id:
        return None
    discord_id = session_to_discord_id[token]
    if discord_id not in ALLOWED_USERS:
        return None
    name = ALLOWED_USERS[discord_id]
    return name


def is_admin(token: str) -> bool:
    if token not in session_to_discord_id:
        return False
    discord_id = session_to_discord_id[token]
    return discord_id in ADMINS


def verify_and_load_config() -> str:
    """Verify that this config file is correct, or at least correct enough, then load config files.

    Returns:
        An empty string if the config file is OK or an error message if it isn't.
    """
    if len(SERVER_FOLDERS) == 0:
        return "No server folders configured!"
    for fol in SERVER_FOLDERS:
        if not os.path.exists(fol):
            return f"Server folder {fol} does not exist!"
    if not os.path.isfile("user_ids.txt"):
        with open("user_ids.txt", "w") as f:
            f.write("123456789012345678~MeTheAdmin\n876543210987654321=MyFriend")
        return "Generated user_ids.txt. Please fill it in with Discord User IDs and friendly names for you to use!"
    else:
        with open("user_ids.txt", "r") as f:
            lines = f.readlines()
        for line in lines:
            admin: bool = False
            if "=" in line:
                discord_id, friendly_name = line.split("=")
            elif "~" in line:
                discord_id, friendly_name = line.split("~")
                admin = True
            friendly_name = friendly_name.rstrip()
            if discord_id in ALLOWED_USERS:
                return f"Discord ID {discord_id} found multiple times in user_ids.txt!"
            elif friendly_name in ALLOWED_USERS.values():
                return f"Friendly name {friendly_name} found multiple times in user_ids.txt!"
            ALLOWED_USERS[discord_id] = friendly_name
            if admin:
                ADMINS[discord_id] = friendly_name
        if len(ALLOWED_USERS) == 0:
            return "No allowed users added!"

    if os.path.isfile(DATASTORE_NAME):
        with open(DATASTORE_NAME, "r") as f:
            session_to_discord_id.update(json.load(f))

    return ""
