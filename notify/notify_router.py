from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from settings import load_settings_for_file
import os
import time
import json
from auth import Auth
from .generate import calcEA, count_EA, load_email_list_EA
from data import Data
from dotenv import load_dotenv
from emailsender import EmailSender
from .emaildb import EmailDB


app_root = os.getenv("APP_ROOT", os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(app_root, "templates"))

router = APIRouter()

@router.get("/show/{filename}", response_class=HTMLResponse)
def notify_show(request: Request, filename: str):
    if not Auth().is_user_logged_in(request):
        # Redirect to the login page if not logged in
        return RedirectResponse(url="/auth/login", status_code=303)

    email_count = count_EA(filename)
    if email_count > 0:
        msg = f"{email_count} email addresses found."
    else:
        msg = "No email addresses found."

    email_list = load_email_list_EA(filename)
    if email_list:
        msg += f" {len(email_list)} email addresses loaded."
    else:
        msg += " No email addresses loaded."

    context = {
        "request": request,
        **request.state.context,
        "filename": filename,
        "message": msg,
        "email_list": email_list,
    }
    return templates.TemplateResponse("notify.html", context)

@router.post("/calcEA/{filename}")
def notify_email(request: Request, filename: str):
    calc_result = calcEA(filename)
    if calc_result:
        msg = "Email addresses calculated successfully."
    else:
        msg = "Error calculating email addresses."

    results = {
        "filename": filename,
        "message": msg,
    }
    return results 

@router.post("/email-name")
async def notify_email_name_post(request: Request, email = Form(...)):
    result = None
    if not Auth().is_user_logged_in(request):
        result = ""
    else:
        data = Data()
        name = data.get_contact_name(email=email)
        if name:
            result = name
        else:
            result = ""

    return {'result': result}

@router.post("/accounts-for-email")
async def notify_accounts_for_email_post(request: Request, 
                                         email = Form(...), 
                                         filename = Form(...)):
    accounts = []

    if not Auth().is_user_logged_in(request):
        accounts = []
    else:
        email_settings_file = ''

        load_dotenv()

        upload_folder = os.getenv("upload_folder", "./")
        account_emails = []
        email_settings_file = os.path.join(upload_folder, filename + ".email_addresses")

    # load contents of email_addresses file into account_emails

        if os.path.exists(email_settings_file):
            with open(email_settings_file, "r") as f:
                account_emails = json.load(f)

        # find the email in the account_emails list
        # and return the corresponding account numbers
        # if the email is found, return the account numbers
        # else return an empty list
        accounts = []
        try:
            for a in account_emails:
                if a['email'] == email:
                    accounts = a['accounts']
                    break
        except Exception as e:
            print(f"Error: {e}")

    result = {
        "email": email,
        "accounts": accounts,
    }
    return result

from pydantic import BaseModel, EmailStr
from typing import List

class EmailSchema(BaseModel):
    email: List[EmailStr]


@router.post("/send-one-email")
async def notify_send_one_email_post(request: Request, 
                                       email: str = Form(...), 
                                       filename: str = Form(...)):
    result = None
    code = 500
    current_user = ''

    if not Auth().is_user_logged_in(request):
        result = ""
        code = 401
    else:
        # verify email found in email_addresses file
        email_settings_file = ''
        load_dotenv()
        upload_folder = os.getenv("upload_folder", "./")
        email_settings_file = os.path.join(upload_folder, filename + ".email_addresses")
        # from .env, UPDATE_WMIS_LOG=yes/no
        update_wmis_log = os.getenv("UPDATE_WMIS_LOG", "no").lower() == "yes"

        account_emails = []
        if os.path.exists(email_settings_file):
            with open(email_settings_file, "r") as f:
                account_emails = json.load(f)

        # find the email in the account_emails list
        # and return the corresponding account numbers
        address_found = False
        accounts = []
        for item in account_emails:
            if item['email'] == email:
                address_found = True
                accounts = item['accounts']
                accounts_text = ''
                for a in accounts:
                    accounts_text += f"{a}\n"

                break
        if address_found:
            # prepare the email to be sent
            # first load template from file settings
            settings = load_settings_for_file(filename=filename)
            subject = settings.get("message_subject", "")
            body = settings.get("message_body", "")
            # add date and time to bottom of body
            body += f"\n\n{time.strftime('%Y-%m-%d %H:%M:%S')}"
            # replace the placeholders in the body with the account numbers
            if body.find("{account_numbers}") > 0:
                body = body.replace("{account_numbers}", accounts_text)

            data = Data()
            if body.find("{email_name}") > 0:
                name = data.get_contact_name(email=email)
                body = body.replace("{email_name}", name['name'])
            if body.find("{email_address}") > 0:
                body = body.replace("{email_address}", email)

            from_address = os.getenv("MAIL_FROM", "")
            # send the email

            recipients = [email]
            email_Sender = EmailSender()
            email_Sender.create_message(
                subject=subject,
                recipients=recipients,
                plain_body=body,
                html_body='',
                attachments=None,
            )

            edb = None
            try:
                edb = EmailDB(filename=filename)
                edb.update_send_status(email, "sending")
                send_result = email_Sender.send_email()
                if send_result:
                    result = "sent"
                    edb.update_send_status(email, "sent")
                else:
                    result = "not sent"
                    edb.update_send_status(email, "not sent")

                if update_wmis_log and send_result:
                    for a in accounts:
                        data.log_email_sent(email=email, account=a, filename=filename)

                result = f"Email {result}."
                code = 201
            except Exception as e:
                result = f"Error sending email: {str(e)}"
                code = 500
            finally:
                if edb:
                    edb = None
                if data:
                    data = None

        else:
            result = "Email address not found in email addresses file."
            code = 404
        
    return {'result': result, 'code': code}



@router.post("/reset-email-status")
async def reset_email_status(request: Request, 
                             filename: str = Form(...)):
    result = None
    code = 500

    if not Auth().is_user_logged_in(request):
        result = ""
        code = 401
    else:
        # reset the email status in the database
        db = EmailDB(filename=filename)
        db.reset_email_status()
        result = "Email status reset successfully."
        code = 201

@router.post("/set-email-status")
async def set_email_status(request: Request, 
                            filename: str = Form(...),
                            email: str = Form(...),
                            status: str = Form(...),
                           ):
    db = EmailDB(filename=filename)
    db.update_send_status(email, status)
    return {"message": "Email status updated successfully."}

@router.post("/get-email-status")
async def get_email_status(request: Request,
                            filename: str = Form(...),
                            email: str = Form(...)):
    db = EmailDB(filename=filename)
    record = db.get_email_record(email)
    if record:
        return {"email": email, "status": record[2], "timestamp": record[3]}
    else:
        return {"email": email, "status": "not found", "timestamp": None}

@router.post("/reset-all-email-status")
async def reset_all_email_status(request: Request, 
                                 filename: str = Form(...),
                                ):
    # remove any existing email addresses in sqlite db.
    db = EmailDB(filename=filename)
    db.reset_email_status()
    db = None
    return {"message": "All email statuses updated successfully."}


@router.get("/check-run-state")
def check_run_state(request: Request):
    if os.getenv("test_flag", "off").lower() == "on":
        rslt = {"state": "debug"}
    else:
        rslt = {"state": "production"}

    return rslt
