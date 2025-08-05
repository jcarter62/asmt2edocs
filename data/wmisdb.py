"""
A module for connecting to the WMIS database using pyodbc.

This module contains a class called WMISDB which provides an easy way to connect to the WMIS database.
The class reads the connection details from the environment variables or .env file (using the decouple library)
and establishes a connection using the ODBC driver for SQL Server. The connection object can be used to
interact with the database.

Classes:
WMISDB: A class for connecting to the WMIS database, providing a connection object.

Example usage:
wmis_db = WMISDB()
connection = wmis_db.connection
# Use the connection object to interact with the database.
# Note that the WMISDB class also includes commented out examples of methods for specific database operations.

"""
import pyodbc
from dotenv import load_dotenv
from os import getenv

from utils.middleware import settings_loader

load_dotenv()

class DBError(Exception):
    """
    Exception class for database errors.
    """

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class WMISDB:
    """
    This class is used to connect to the WMIS database, and provide a connection object.
    """
    _server = ''
    _instance = ''
    _database = ''
    _username = ''
    _password = ''
    connection = None

    def __init__(self) -> None:
        """
        Constructor for the WMISDB class.
        depends on the decouple library to read the connection details from the environment variables or .env file.
        :return: None
        """
        # determine if running in test mode

        settings_loader()  # Load settings into environment variables
        if getenv('TEST_FLAG', 'off').lower() == 'on':
            # if test_flag is set, then use the test database
            self._server = getenv('TEST_SQLSERVER', default='localhost')
            self._instance = getenv('TEST_INSTANCE', default='')
            self._database = getenv('TEST_DATABASE', default='test_database')
            self._username = getenv('TEST_UID', default='test_username')
            self._password = getenv('TEST_PASSWORD', default='test_password')
        else:
            # if test_flag is not set, then use the production database
            self._server = getenv('SQLSERVER', default='localhost')
            self._instance = getenv('INSTANCE', default='')
            self._database = getenv('DATABASE', default='database')
            self._username = getenv('UID', default='username')
            self._password = getenv('PASSWORD', default='password')

        self.connection = self._connection_()
        super().__init__()
        return

    def _conn_str_(self, ):
        con_str = 'Driver={ODBC Driver 17 for SQL Server};'

        con_str += 'SERVER=' + self._server
        if self._instance != '':
            con_str += '\\' + self._instance
        con_str += ';'

        con_str += 'DATABASE=' + self._database + ';'
        con_str += 'UID=' + self._username + ';'
        con_str += 'PWD=' + self._password + ';'
        con_str += 'PORT=1433;ENCRYPT=NO;'
        con_str += 'MARS_Connection=Yes;'
        return con_str

    def __del__(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None
        self._server = ''
        self._instance = ''
        self._database = ''
        self._username = ''
        self._password = ''


    def _connection_(self):
        if self.connection is None:
            self.connection = pyodbc.connect(self._conn_str_())
        return self.connection

    @staticmethod
    def extract_row(row: pyodbc.Cursor):
        """
        extract_row is a static method that takes a pyodbc cursor object and returns a dictionary of the row data.
        each field in the row is converted to a string and the dictionary keys are converted to lower case.
        """
        r = {}
        i = 0
        try:
            for item in row.cursor_description:
                name = item[0]
                val = str(row[i])
                name = name.lower()
                i += 1
                r[name] = val
        except DBError as err:
            print(f'Error in extract_row: {err}')
            r['error'] = f'Error in extract_row: {err}'

        return r


