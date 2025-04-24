# import datetime
# import os.path
# import uuid
# import json

from .wmisdb import WMISDB, DBError
from dotenv import load_dotenv
import os

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
                    select distinct cme.email, 
                    ltrim(
                    rtrim(
                        rtrim(
                        isnull(cmc.FirstName,'') + ' ' + isnull(cmc.MiddleName, '') 
                        ) + ' ' + isnull(cmc.LastName,'')
                    )
                    ) as ContactName 
                    from CMEmail cme
                    join CMNameContact cmn on cme.IDEmail = cmn.IDEmail
                    join CMContact cmc on cmn.IDContact = cmc.IDContact
                    where cme.Email = ? ;
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
    