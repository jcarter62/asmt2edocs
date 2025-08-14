from data import Data
import os

class upload_email_records:

    def __init__(self, filename: str):
        if not filename:
            raise ValueError("Filename cannot be empty.")
        self.filename = filename
        upload_folder = os.getenv('UPLOAD_FOLDER', 'uploads')
        # calculate json file name from the provided filename
        self.db = sqlite_filename = os.path.join(upload_folder, filename + '.emails.db')
        if not os.path.exists(sqlite_filename):
            raise FileNotFoundError(f"File {sqlite_filename} does not exist.")

    def upload_to_sql(self) -> int:
        uploaded = 0
        values = []

        data = Data()
        data.delete_email_records(filename=self.filename)

        # open sqlite database using self.db
        # and read email records from it
        import sqlite3
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()
        cursor.execute("SELECT id, email_address, send_status, timestamp FROM email_records")
        rows = cursor.fetchall()
        for row in rows:
            # convert row[3] from iso format to datetime without timezone or microseconds
            from datetime import datetime
            timestamp = datetime.fromisoformat(row[3])
            timestamp = timestamp.replace(tzinfo=None, microsecond=0)
            # append the values to the list
            uploaded += 1

            values.append((self.filename, row[0], row[1], row[2], timestamp,))

        if values:
            data.insert_email_records(values=values)

        data = None
        return uploaded

