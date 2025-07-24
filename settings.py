from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
import os
from auth import Auth

router = APIRouter()

base_dir = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

@router.get("/")
def get_settings(request: Request):
    if not Auth().is_user_logged_in(request):
        # Redirect to the login page if not logged in
        return RedirectResponse(url="/auth/login", status_code=303)

    context = {
        "request": request,
        **request.state.context,
    }
    return templates.TemplateResponse("settings.html", context)

@router.post("/")
async def update_settings(request: Request,
                          base_folder: str = Form(...),
                          company: str = Form(...),
                          upload_folder: str = Form(...),
                          appname: str = Form(...),
                          # search_pattern: str = Form(...)
                          ):
    # Update the BASE_FOLDER environment variable
    os.environ["base_folder"] = base_folder
    os.environ["company"] = company
    os.environ["upload_folder"] = upload_folder
    os.environ["appname"] = appname
    # os.environ["search_pattern"] = search_pattern
    # Optionally, save the updated setting to a file or database
    app_data_folder = os.getenv("APP_DATA", "~/")
    # save settings to a json file named settings.json
    settings_file = os.path.join(app_data_folder, "settings.json")
    with open(settings_file, "w") as f:
        # convert the settings to a json string
        settings = {
            "base_folder": base_folder,
            "company": company,
            "upload_folder": upload_folder,
            "appname": appname,
            # "search_pattern": search_pattern
        }
        f.write(json.dumps(settings, indent=4, sort_keys=True))

    home_url = request.url_for("get_settings")
    return RedirectResponse(home_url, status_code=303)

@router.get("/load/{filename}")
def get_settings_for_file(request: Request, filename: str):
    return load_settings_for_file(filename)

import json

@router.post("/save/{filename}")
def save_settings_for_file(request: Request, filename: str,
                            search_pattern: str = Form(...),
                            save_as: str = Form(...),
                            save_date: str = Form(...),
                            process_date: str = Form(...),
                            message_subject: str = Form(...),
                            message_body: str = Form(...),
                            include_account_names: bool = Form(...),
                            include_account_numbers: bool = Form(...),
                           ):
    
    result = {"message": "save_settings_for_file called."}
    upload_folder = os.getenv("upload_folder", "./")
    settings_file = os.path.join(upload_folder, filename + ".settings")

    try:
        with open(settings_file, "w") as f:
            # convert the settings to a json string
            settings = {
                "search_pattern": search_pattern,
                "save_as": save_as,
                "save_date": save_date,
                "process_date": process_date,
                "message_subject": message_subject,
                "message_body": message_body,
                "include_account_names": include_account_names,
                "include_account_numbers": include_account_numbers,
            }
            f.write(json.dumps(settings, indent=4, sort_keys=True))

        result = {"message": "Settings saved successfully."}
    except Exception as e:
        result = {"error": f"Error saving settings: {str(e)}"}

    # remove test file if it exists
    test_file = os.path.join(upload_folder, filename + ".test.pdf")
    if os.path.exists(test_file):
        try:
            os.remove(test_file)
        except Exception as e:
            result["error"] = f"Error removing test file: {str(e)}"

    return result

def load_settings_for_file(filename: str):
    result = {
    }
    upload_folder = os.getenv("upload_folder", "./")
    settings_file = os.path.join(upload_folder, filename + ".settings")

    if not os.path.exists(settings_file):
        # create file with default values
        with open(settings_file, "w") as f:
            settings = {
                "search_pattern": "Account Number\\n(\\d+)\\b",
                "save_as": "",
                "save_date": "",
                "process_date": "",
                "message_subject": "",
                "message_body": "",
                "include_account_names": False,
                "include_account_numbers": False,
            }
            f.write(json.dumps(settings, indent=4, sort_keys=True))

    settings = {}
    with open(settings_file, "r") as f:
        # load the settings from the file
        settings = json.load(f)

    return settings

@router.get("/check-exist/{filename}")
def check_exist_filename(request: Request, filename: str):
    result = {"result": -1}
    try:
        upload_folder = os.getenv("upload_folder", "./")

        file_path = os.path.join(upload_folder, filename)

        if os.path.exists(file_path):
            result = {"result": 1}
        else:
            result = {"result": 0}
    except Exception as e:
        result = {"result": -2}

    return result
