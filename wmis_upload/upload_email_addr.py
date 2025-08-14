import os
from data import Data

class upload_email_addr:
    """
    Class to handle email address upload.
    """

    def __init__(self, filename: str):
        if not filename:
            raise ValueError("Filename cannot be empty.")
        self.filename = filename
        self.email_address = {}
        upload_folder = os.getenv('UPLOAD_FOLDER', 'uploads')
        # calculate json file name from the provided filename
        json_filename = os.path.join(upload_folder, filename + '.email_addresses')
        if not os.path.exists(json_filename):
            raise FileNotFoundError(f"File {json_filename} does not exist.")
        with open(json_filename, 'r') as file:
            self.email_address = file.read().strip()
        if not self.email_address:
            raise ValueError("Email address cannot be empty.")

        # convert self.email_address to a list of dictionaries
        if isinstance(self.email_address, str):
            import json
            try:
                self.email_address = json.loads(self.email_address)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format in email address data: {e}")

    def upload_to_sql(self) -> int:
        uploaded = 0
        values = []

        data = Data()
        data.delete_notify(filename=self.filename)

        for record in self.email_address:
            accounts = record['accounts']
            for account in accounts:
                email = record['email']
                values.append( (self.filename, email, account,) )
                uploaded = uploaded + 1

        if values:
            data.insert_notify_cmds(values=values)

        data = None
        return uploaded

