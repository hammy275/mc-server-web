from subprocess import Popen


class RunningServer:
    def __init__(self, name: str, folder_path: str, process: Popen):
        # Provided by constructor
        self.name: str = name
        self.folder_path: str = folder_path
        self.process: Popen = process

        # Other initial fields.
        self.last_log_lines = ""

    def get_running_data(self) -> dict:
        return {"log": self.last_log_lines}
