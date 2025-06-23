from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from settings import load_settings_for_file
from pdf import PDF
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
def notify_root(request: Request, filename: str):
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

    if not Auth().is_user_logged_in(request):
        result = ""
        code = 401
    else:
        # verify email found in email_addresses file
        email_settings_file = ''
        load_dotenv()
        upload_folder = os.getenv("upload_folder", "./")
        email_settings_file = os.path.join(upload_folder, filename + ".email_addresses")
  
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
            body = body.replace("{account_numbers}", accounts_text)
            data = Data()
            name = data.get_contact_name(email=email)
            body = body.replace("{email_name}", name['name'])
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
                edb.update_send_status(email, "sent")

                result = "Email sent successfully."
                code = 201
            except Exception as e:
                result = f"Error sending email: {str(e)}"
                code = 500
            finally:
                edb = None

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

@router.post("/reset-all-email-status")
async def reset_all_email_status(request: Request, 
                                 filename: str = Form(...),
                                 status: str = Form(...),
                                ):
    #
    # reset the email status in the database to calculated status
    #
    db = EmailDB(filename=filename)
    # load the email addresses from the file
    email_settings_file = ''
    load_dotenv()
    upload_folder = os.getenv("upload_folder", "./")
    email_settings_file = os.path.join(upload_folder, filename + ".email_addresses")
    # load contents of email_addresses file into account_emails
    account_emails = []
    if os.path.exists(email_settings_file):
        with open(email_settings_file, "r") as f:
            account_emails = json.load(f)
    else:
        # if the file does not exist, create an empty list
        pass
    #
    # loop through the email addresses and set the status
    for item in account_emails:
        email = item['email']
        # update the status in the database
        db.update_send_status(email, status)
    db = None 
    return {"message": "All email statuses updated successfully."}
 