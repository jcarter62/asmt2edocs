import os
import json

class FileState:
    """
    A class to manage the state of the application.
    """
    def __init__(self, filename=None):
        # if filename is provided, load the state from the file
        if filename:
            self.filename = filename
        else:
            self.filename = None

    def _calc_file_path(self) -> str:
        if not self.filename:
            raise ValueError("Filename must be set to calculate file path.")
        upload_folder = os.getenv("upload_folder", None)
        if not upload_folder:
            raise ValueError("upload_folder environment variable must be set to determine the file path.")
        return os.path.join(upload_folder, self.filename + ".state.json")

    def _load_state(self):
        file_path = self._calc_file_path()
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        else:
            # create an empty state if the file does not exist
            initial_state = {"state": 0}
            with open(file_path, 'w') as f:
                json.dump(initial_state, f)
            return initial_state

    def _save_state(self, state_json):
        import json
        try:
            file_path = self._calc_file_path()
            with open(file_path, 'w') as f:
                json.dump(state_json, f)
        except Exception as e:
            print(f"Error saving state to file: {e}")
            # Optionally, you can raise an exception or handle it as needed
            # raise e
        return


    def set(self, state = None):
        if state is None:
            return
        else:
            current_state = self._load_state()
            current_state['state'] = state
            self._save_state(current_state)


    def get(self):
        # Retrieve current state and return
        self._state = self._load_state()
        return self._state['state']
