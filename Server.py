import os
from subprocess import Popen
from threading import Lock
from typing import Union

class Server:
    def __init__(self, id_in: str, folder_path: str, users: list[str], admins: list[str], modpack_path: Union[str, None]):
        # Provided by constructor
        self.id: str = id_in
        self.folder_path: str = folder_path
        self.users: list[str] = users
        self.admins: list[str] = admins
        self.modpack_path: Union[str, None] = modpack_path
        self.log = ""

        # Other initial fields.
        self.process: Union[Popen, None] = None
        self.lock: Lock = Lock()
        self.name = os.path.split(os.path.split(os.path.normpath(self.folder_path))[0])[1] + " - " + self.id

    def set_process(self, process: Union[Popen, None]):
        with self.lock:
            self.process = process

    def is_running(self):
        return self.process is not None

    def set_log(self, log):
        with self.lock:
            self.log = log

    def on_stop(self):
        with self.lock:
            self.log = None
            self.process = None

    def has_modpack(self):
        return self.modpack_path is not None

    def get_data(self, is_admin: bool) -> dict:
        data = {"id": self.id, "name": self.name, "running": self.is_running(), "is_admin": is_admin,
                "has_modpack": self.has_modpack()}
        if self.is_running():
            data["log"] = self.log
        return data

