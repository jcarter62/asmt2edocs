from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from auth import Auth
import os
import json
from fastapi.templating import Jinja2Templates
from settings import load_settings_for_file
from data import Data
from progress_status import ProgressStatus


router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates"))

# /select/ ...

@router.get("/", response_class=HTMLResponse)
def select_for_processing(request: Request):
    if not Auth().is_user_logged_in(request):
        # Redirect to the login page if not logged in
        return RedirectResponse(url="/auth/login", status_code=303)


    upload_folder = os.environ.get("UPLOAD_FOLDER", "./")
    try:
        files = []
        allFiles = os.listdir(upload_folder)
        # include only pdf files
        for f in allFiles:
            if f.endswith(".pdf") and not f.endswith(".test.pdf"):
                item = {"filename": f}
                files.append(item)

        for f in files:
            # determine if the file has been processed, and .pages file exists
            _filename = os.path.join(upload_folder, f["filename"])
            _pages_file = _filename + ".pages"
            if os.path.exists(_pages_file):
                f["processed"] = True
            else:
                f["processed"] = False

        idnum = 1001
        for f in files:
            idnum = idnum + 3
            f["id"] = idnum

        for f in files:
            # determine of there is a test.pdf file for this file
            _test_filename = os.path.join(upload_folder, f["filename"] + ".test.pdf")
            if os.path.exists(_test_filename):
                f["test"] = _test_filename
            else:
                f["test"] = ''

    except Exception:
        files = []
    context = {
        "request": request,
        "files": files,
        **request.state.context,
    }
    return templates.TemplateResponse("select-for-processing.html", context)

@router.get("/email-lookup/{filename}", response_class=HTMLResponse)
def email_lookup(request: Request, filename: str):
    if not Auth().is_user_logged_in(request):
        # Redirect to the login page if not logged in
        return RedirectResponse(url="/auth/login", status_code=303)

    data = Data()

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
    
    try:
        with open(email_settings_file, "wb") as f:
            json_data = json.dumps(email_accounts, indent=4, sort_keys=True)
            f.write(json_data.encode("utf-8"))
    except:
        pass

    return RedirectResponse(url="/select", status_code=303)

@router.get("/progress/init/{filename}")
def progress_init(request: Request, filename: str):
    ps = ProgressStatus(filename=filename)
    # Initialize the progress status with a maximum value
    ps.init()
    return {"message": "ok"}

@router.get("/progress/get_current/{filename}")
def progress_get_current(request: Request, filename: str):
    ps = ProgressStatus(filename=filename)
    cur_obj = ps.get_current()
    print(f"Current progress: {cur_obj}: for {filename}")
    return cur_obj

