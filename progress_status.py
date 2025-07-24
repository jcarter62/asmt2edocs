import sqlite3
import os
from datetime import datetime

class ProgressStatus:
    """
    A class to represent the progress status of a task.
    """
    def __init__(self, upload_folder=None, filename=None, activity=None):
        if filename is None:
            raise ValueError("filename must be provided")

        if upload_folder is None:
            upload_folder = os.environ.get("upload_folder", "./")

        if filename is None:
            raise ValueError("filename must be provided")

        self.activity = activity if activity else "default_activity"

        self.db_path = os.path.join(upload_folder, filename + ".progress.db")
        self._initialize_database()

    def _initialize_database(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    activity TEXT NOT NULL UNIQUE,
                    current INTEGER NOT NULL,
                    total INTEGER NOT NULL,
                    txt TEXT NULL
                )
            ''')
            conn.commit()

    def init(self, activity: str = None):
        if activity:
            self.activity = activity

        with sqlite3.connect(self.db_path) as conn:
            # determine if a record for this activity already exists
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM progress WHERE activity = ?', (self.activity,))
            record = cursor.fetchone()
            if record:
                # delete the record if it exists
                cursor.execute('DELETE FROM progress WHERE activity = ?', (self.activity,))
            cursor.execute('''
                INSERT INTO progress (activity, current, total, txt)
                VALUES (?, 0, 100, NULL)
            ''', (self.activity,))
            conn.commit()

    def set_max(self, max_value: int):
        # find if a record for this activity already exists
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM progress WHERE activity = ?', (self.activity,))
            record = cursor.fetchone()
            if record:
                # If a record exists, update it
                cursor.execute('''
                    UPDATE progress
                    SET current = 0, total = ?
                    WHERE activity = ?
                ''', (max_value, self.activity))
            else:
                # If no record exists, insert a new one
                cursor.execute('''
                    INSERT INTO progress (activity, current, total, txt)
                    VALUES (?, ?, ?, ?)
                ''', (self.activity, 0, max_value, None))
            conn.commit()

    def set_current(self, current: int):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE progress SET current = ? WHERE activity = ?', (current, self.activity))
            conn.commit()


    def delete(self, activity: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM progress WHERE activity = ?', (activity,))
            conn.commit()

    def get_current(self):
        with (sqlite3.connect(self.db_path) as conn):
            cursor = conn.cursor()
            cursor.execute('SELECT id, current, total, txt FROM progress WHERE activity = ?', (self.activity,))
            record = cursor.fetchone()
            if record:
                return {
                    "current": record[1],
                    "total": record[2],
                    "txt": record[3],
                }
            else:
                return {
                    "current": 0,
                    "total": 100,
                    "txt": "No record found",
                }
