import os 
import json
from data import Data
from dotenv import load_dotenv


def calcEA(filename: str):
    results = 0
    data = Data()

    load_dotenv()

    result = ''
    upload_folder = os.getenv("upload_folder", "./")
    account_emails = []
    email_settings_file = os.path.join(upload_folder, filename + ".email_addresses")

    pages_file = os.path.join(upload_folder, filename + ".pages")
    pages = {}
    if os.path.exists(pages_file):
        with open(pages_file, "r") as f:
            pages = json.load(f)

    # for each pages object, determine email addresses for each account
    account_emails= []
    for item in pages:
        account = int(item["account"])
        ea = data.get_email_addresses(account)
        if ea:
            for email in ea:
                one_account = {
                    "account": account,
                    "email": email,
                }
                account_emails.append(one_account)

    email_list = []
    for item in account_emails:
        email = item["email"]
        if email not in email_list:
            email_list.append(email)

    email_accounts = []
    for email in email_list:
        this_email = {
            "email": email,
            "accounts": [],
        }
        accounts = []
        for ae in account_emails:
            if email == ae["email"]:
                accounts.append(ae["account"])  # changed from 'account' to 'ae["account"]'
        this_email["accounts"] = accounts
        email_accounts.append(this_email)
        results += 1
    
    try:
        with open(email_settings_file, "wb") as f:
            json_data = json.dumps(email_accounts, indent=4, sort_keys=True)
            f.write(json_data.encode("utf-8"))
    except:
        pass

    return results


# determine how many email addresses are in the file and return the number of email addresses
def count_EA(filename: str):
    results = 0
    email_settings_file = ''

    load_dotenv()

    upload_folder = os.getenv("upload_folder", "./")
    account_emails = []
    email_settings_file = os.path.join(upload_folder, filename + ".email_addresses")

    # load contents of email_addresses file into account_emails

    if os.path.exists(email_settings_file):
        with open(email_settings_file, "r") as f:
            account_emails = json.load(f)

        results = len(account_emails)

    return results

def load_email_list_EA(filename: str):
    results = []
    email_settings_file = ''

    load_dotenv()

    upload_folder = os.getenv("upload_folder", "./")
    account_emails = []
    email_settings_file = os.path.join(upload_folder, filename + ".email_addresses")

    # load contents of email_addresses file into account_emails

    if os.path.exists(email_settings_file):
        with open(email_settings_file, "r") as f:
            account_emails = json.load(f)

        for item in account_emails:
            results.append(item["email"])

    # sort the list of email addresses
    results.sort()
    # remove duplicates from the list of email addresses
    results = list(dict.fromkeys(results))

    return results
