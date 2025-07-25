import sqlite3
import os
from datetime import datetime

class EmailDB:
    def __init__(self, upload_folder=None, filename=None):
        if filename is None:
            raise ValueError("filename must be provided")

        if upload_folder is None:
            upload_folder = os.environ.get("upload_folder", "./")

        if filename is None:
            raise ValueError("filename must be provided")

        self.db_path = os.path.join(upload_folder, filename + ".emails.db")
        self._initialize_database()

    def reset_email_status(self):
        """remove all email records."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM email_records WHERE 1=1;')
            conn.commit()
        return

    def _initialize_database(self):
        """Initialize the database and create the table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS email_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email_address TEXT NOT NULL UNIQUE,
                    send_status TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            ''')
            conn.commit()

    def get_email_record(self, email_address):
        """Retrieve an email record by email address."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM email_records WHERE email_address = ?', (email_address,))
            # fetchone returns a single record or None if not found
            return cursor.fetchone()


    def add_email_record(self, email_address, send_status):
        """Add a new email record to the database."""
        timestamp = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO email_records (email_address, send_status, timestamp)
                VALUES (?, ?, ?)
            ''', (email_address, send_status, timestamp))
            conn.commit()

    def update_send_status(self, email_address, send_status):
        """Update the send status and timestamp of an email record."""
        # check to see if the email address exists in the database
        record = self.get_email_record(email_address)
        if record is None:
            self.add_email_record(email_address, send_status)
        else:
            timestamp = datetime.now().isoformat()
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE email_records
                    SET send_status = ?, timestamp = ?
                    WHERE email_address = ?
                ''', (send_status, timestamp, email_address))
                conn.commit()
        return

    def get_all_records(self):
        """Retrieve all email records from the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM email_records')
            return cursor.fetchall()

    def delete_record(self, email_address):
        """Delete an email record by its ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM email_records WHERE email_address = ?', (email_address,))
            conn.commit()
