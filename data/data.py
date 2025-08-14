# import datetime
# import os.path
# import uuid
# import json

from .wmisdb import WMISDB, DBError
from dotenv import load_dotenv
import os
import uuid
from datetime import datetime

load_dotenv()

class Data:
    accounts = []
    email_addresses = []
    email_accounts = []

    def __init__(self):
        self.accounts = []
        self.email_addresses = []
        self.email_accounts = []
        self.load_data()


    def load_data(self):
        try:
            wmisdb = WMISDB()
            conn = wmisdb.connection
            cursor = conn.cursor()
            sql = "select " + \
                "distinct v.Email, v.Name_ID as account " + \
                "from v_CMEmailNoticeTypes v where v.NoticeType like '%Statement%' " + \
                "order by v.Email, v.Name_ID; "
            #
            # grant select on v_CMEmailNoticeTypes to user
            #
            cursor.execute(sql)
            rows = cursor.fetchall()
            if len(rows) > 0:
                for row in rows:
                    item = {
                        "email": row[0],
                        "account": int(row[1]),
                    }
                    self.email_accounts.append(item)
            wmisdb = None
        except DBError as err:
            print(f'DB Error:{err}')
        except Exception as err:
            print(f'Unexpected Error:{err}')

        # load email addresses from email_accounts
        for item in self.email_accounts:
            email = item["email"]
            if email not in self.email_addresses:
                self.email_addresses.append(email)

        # load accounts from email_accounts
        for item in self.email_accounts:
            account = item["account"]
            if account not in self.accounts:
                self.accounts.append(account)

        return

    def get_email_addresses(self, account:int):
        # Return email addresses for the given account using list comprehension
        short_list = [item["email"] for item in self.email_accounts if item["account"] == account]
        return short_list


    def get_contact_name(self, email=None):
        result = {
            "email": email,
            "name": None,
        }

        # Return contact name for the given email address using list comprehension
        if email is None:
            result = {
                "email": email,
                "name": None,
            }
        else:
            try:
                wmisdb = WMISDB()
                conn = wmisdb.connection
                cursor = conn.cursor()
                sql = '''
                    select distinct 
                        ltrim(rtrim(cme.email)) as email, 
                        ltrim(
                            rtrim(
                                isnull(cmc.FirstName,'') + ' ' + isnull(cmc.MiddleName, '')
                            ) + ' ' + isnull(cmc.LastName,'')
                        ) 
                        as ContactName 
                    from CMEmail cme
                    join CMNameContact cmn on cme.IDEmail = cmn.IDEmail
                    join CMContact cmc on cmn.IDContact = cmc.IDContact
                    where 
                        rtrim(cme.Email) = rtrim(?);
                '''
                #
                # grant select on v_CMEmailNoticeTypes to user
                #
                cursor.execute(sql, (email,))
                dataRow = cursor.fetchone()
                if dataRow is not None:
                    result = {
                        "email": dataRow[0],
                        "name": dataRow[1],
                    }
                wmisdb = None
            except DBError as err:
                print(f'DB Error:{err}')
            except Exception as err:
                print(f'Unexpected Error:{err}')

        return result

    def log_email_sent(self, email=None, account=None, filename=None, timestamp=None, user=None):
        """Log the email sent to the database."""
        if email is None or account is None or filename is None :
            return

        if timestamp is None:
            timestamp = datetime.datetime.now().isoformat()
        # remember to: grant insert on NameNotes to user
        #
        # create a guid for the log entry

        try:
            wmisdb = WMISDB()
            conn = wmisdb.connection
            txt = f"{filename} Available: {email}"

            timestamp_object = datetime.fromisoformat(timestamp)
            timestamp_object = timestamp_object.replace(microsecond=0)

            # Format to non-ISO format
            new_timestamp = timestamp_object.strftime('%Y-%m-%d %H:%M:%S')

            #
            # check to see if the log record already exists
            #
            sql = """
                select isnull(id,''), isnull(cdate,''), isnull(cuser,'') from NameNotes 
                where name_id = ? and txt = ? and cmethod = ? and topic = ?
                and cdate between dateadd(hour, -2, ?) and dateadd(hour, 2, ?);
            """
            c = conn.cursor()
            c.execute(sql, (account, txt, 'Email', 'E-Docs', new_timestamp, new_timestamp,))
            row = c.fetchone()
            if row is None:
                # No existing record found, create a new one.
                id = ''
            else:
                id = row[0]
                cdate = row[1]
                cuser = row[2]

            if id <= '':
                # Create new record.
                id = str(uuid.uuid4()).replace('-', '').replace('{', '').replace('}', '').lower()

                sql = '''
                      insert into NameNotes (id, name_id, txt, cmethod, topic)
                      values (?, ?, ?, ?, ?); \
                      '''
                cmethod = 'Email'
                topic = 'E-Docs'
                #
                # grant select on v_CMEmailNoticeTypes to user
                #
                conn.execute(sql, (id, account, txt, cmethod, topic))
                conn.commit()

                cdate = new_timestamp
                cuser = ''

            else:
                pass


            if cdate == timestamp_object and cuser == user:
                # No need to update, the record already exists with the same timestamp and user.
                pass
            else:
                # update existing record, with cdate = timestamp and cuser = current user.
                sql = """
                    update NameNotes
                    set cdate = ?, cuser = ?
                    where id = ?;
                """
                if user is None:
                    user = ''

                conn.execute(sql, (new_timestamp, user, id,))
                conn.commit()
        except DBError as err:
            print(f'DB Error:{err}')
        except Exception as err:
            print(f'Unexpected Error:{err}')
        return

    def is_email_logged(self, email=None, account=None, filename=None, timestamp=None):
        """Check if the email has already been logged."""
        rslt = False
        if email is None or account is None or filename is None:
            return rslt
        if timestamp is None:
            timestamp = datetime.now().isoformat()

        try:
            wmisdb = WMISDB()
            conn = wmisdb.connection
            txt = f"{filename} Available: {email}"

            timestamp_object = datetime.fromisoformat(timestamp)
            timestamp_object = timestamp_object.replace(microsecond=0)

            # Format to non-ISO format
            new_timestamp = timestamp_object.strftime('%Y-%m-%d %H:%M:%S')

            #
            # check to see if the log record already exists
            #
            sql = """
                  select isnull(id, ''), isnull(cdate, ''), isnull(cuser, '') \
                  from NameNotes
                  where name_id = ? \
                    and txt = ? \
                    and cmethod = ? \
                    and topic = ?
                    and cdate between dateadd(hour, -2, ?) and dateadd(hour, 2, ?); \
                  """
            c = conn.cursor()
            c.execute(sql, (account, txt, 'Email', 'E-Docs', new_timestamp, new_timestamp,))
            row = c.fetchone()
            if row is None:
                # No existing record found, create a new one.
                rslt = False
            else:
                rslt = True
        except DBError as err:
            print(f'DB Error:{err}')
        finally:
            wmisdb = None
        return rslt

    def delete_notify(self, filename=None):
        """
        Delete notification records stored in a2e_email_accts for the given filename.
        """
        if filename is None:
            raise ValueError("Filename cannot be None.")

        try:
            wmisdb = WMISDB()
            conn = wmisdb.connection
            cursor = conn.cursor()
            sql = "DELETE FROM a2e_email_accts WHERE filename = ?;"
            cursor.execute(sql, (filename,))
            conn.commit()
        except DBError as err:
            print(f'DB Error:{err}')
        finally:
            wmisdb = None

    def insert_notify_cmds(self, values=None):
        """
        Insert notification commands into the a2e_email_accts table.
        :param values: List of Tuples containing (filename, email, account).
        """
        if not values:
            raise ValueError("No commands to execute.")

        try:
            sql = "INSERT INTO a2e_email_accts (filename, email, account) VALUES (?, ?, ?);"
            wmisdb = WMISDB()
            conn = wmisdb.connection
            cursor = conn.cursor()
            cursor.fast_executemany = True
            cursor.executemany(sql, values)
            conn.commit()
        except DBError as err:
            print(f'DB Error:{err}')
        finally:
            wmisdb = None

    def delete_email_records(self, filename=None):
        """
        Delete email records from the a2e_email_records table for the given filename.
        :param filename:
        :return:
        """
        if filename is None:
            raise ValueError("Filename cannot be None.")

        try:
            wmisdb = WMISDB()
            conn = wmisdb.connection
            cursor = conn.cursor()
            sql = "DELETE FROM a2e_email_records WHERE filename = ?;"
            cursor.execute(sql, (filename,))
            conn.commit()
        except DBError as err:
            print(f'DB Error:{err}')
        finally:
            wmisdb = None

    def insert_email_records(self, values=None):
        """
        Insert email records into the a2e_email_records table.
        :param values: List of Tuples containing (filename, id, email_address, send_status, timestamp).
        Note: timestamp is expected to be a datetime object without timezone or microseconds.
        :return:
        """
        if not values:
            raise ValueError("No commands to execute.")

        try:
            sql = "INSERT INTO a2e_email_records (filename, id, email_address, send_status, timestamp) " + \
                "VALUES (?, ?, ?, ?, ?);"
            wmisdb = WMISDB()
            conn = wmisdb.connection
            cursor = conn.cursor()
            cursor.fast_executemany = True
            cursor.executemany(sql, values)
            conn.commit()
        except Exception as err:
            print(f'DB Error:{err}')
        finally:
            wmisdb = None

    def get_wmis_log_status(self, filename=None):
        """
        Get the WMIS log status for the given filename.
        :param filename: The name of the file to check.
        :return: A dictionary with email & log_status.
        """
        if filename is None:
            raise ValueError("Filename cannot be None.")

        result = []

        try:
            wmisdb = WMISDB()
            conn = wmisdb.connection
            cursor = conn.cursor()
            sql = "exec sp_a2e_wmis_log_status ?;"
            cursor.execute(sql, (filename,))
            rows = cursor.fetchall()
            for row in rows:
                result.append({
                    "email": row[0],
                    "log_status": row[1],
                })
        except Exception as err:
            print(f'Error:{err}')
        finally:
            wmisdb = None

        return result

    def set_wmis_log_status(self, filename=None):
        """
        Create missing WMIS log status for the given filename.
        :param filename: The name of the file to check.
        :return: ok if successful, else an error message.
        """
        if filename is None:
            raise ValueError("Filename cannot be None.")

        result = ''
        try:
            wmisdb = WMISDB()
            conn = wmisdb.connection
            cursor = conn.cursor()
            sql = "exec sp_a2e_wmis_log_create ?;"
            cursor.execute(sql, (filename,))
            row = cursor.fetchone()
            conn.commit()
            result = row[0]
        except Exception as err:
            print(f'Error:{err}')
        finally:
            wmisdb = None

        return result

