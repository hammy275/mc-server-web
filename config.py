import logging
import os
import sys
from typing import List, Type


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

# End User-Configured Settings


# Expand vars for server folders
for i in range(len(SERVER_FOLDERS)):
    SERVER_FOLDERS[i] = os.path.expanduser(os.path.expandvars(SERVER_FOLDERS[i]))


def verify_config() -> str:
    """Verify that this config file is correct, or at least correct enough.

    Returns:
        An empty string if the config file is OK or an error message if it isn't.
    """
    if len(SERVER_FOLDERS) == 0:
        return "No server folders configured!"
    for fol in SERVER_FOLDERS:
        if not os.path.exists(fol):
            return f"Server folder {fol} does not exist!"
    return ""