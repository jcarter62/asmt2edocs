from fastapi import Request, HTTPException, APIRouter, Form
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from dotenv import load_dotenv
import requests
import os
import json

router = APIRouter()

base_dir = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

@router.get("/login")
def auth_login_get(request: Request):
    load_dotenv()
    security_group = os.getenv("AUTH_API_GROUP")
    context = {
        "request": request,
        **request.state.context,
        "security_group": security_group,
    }
    return templates.TemplateResponse("login.html", context)

@router.post("/login")
def auth_login_post(request: Request,
                    username: str = Form(...),
                    password: str = Form(...)):
    auth = Auth()
    is_logged_in, message = auth.authenticate(username, password)
    if is_logged_in:
        # Redirect to the settings page after successful login
        request.session["user"] = username
        request.session["authenticated"] = True
        return RedirectResponse(url="/settings", status_code=303)
    else:
        if message:
            msg_obj = json.loads(message)
            msg_text = msg_obj['message']
            if message:
                errmsg = msg_text
            else:
                errmsg = None
        else:
            errmsg = "Other Error"
        context = {
            "request": request,
            "error": "Invalid username or password",
            "message": errmsg,
            **request.state.context,
        }
        return templates.TemplateResponse("login.html", context)

@router.get("/logout")
def auth_logout_get(request: Request):
    request.session["user"] = None
    request.session["authenticated"] = False
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

class Auth:
    """
    AUTH class to handle authentication and authorization.
    """

    def __init__(self):
        """
        Initialize the AUTH class.
        """
        self.authenticated = False
        self.authorized = False

    def authenticate(self, username, password)-> ( bool, str):
        """
        Authenticate a user.

        :param username: The username of the user.
        :param password: The password of the user.
        :return: True if authenticated, False otherwise.
        """
        # Placeholder for actual authentication logic
        # call the api with username and password and group
        results = False
        message = ""
        load_dotenv()
        api_url = os.getenv("AUTH_API")
        group = os.getenv("AUTH_API_GROUP")

        if not api_url:
            raise ValueError("AUTH_API environment variable is not set.")
        if not group:
            raise ValueError("AUTH_API_GROUP environment variable is not set.")

        # create post request to the api

        url = f"{api_url}"
        if url.endswith("/"):
            url = url[:-1]
        url = f"{url}/{group}"
        headers = {
            "Content-Type": "application/json",
        }
        body = {
            "username": username,
            "password": password,
        }
        response = requests.post(url, json=body, headers=headers)
        if response.status_code == 200:
            self.authenticated = True
            results = True
        else:
            self.authenticated = False
            results = False
            message = response.text
        return results, message

    @staticmethod
    def is_user_logged_in(request: Request) -> bool:
        """
        Check if the user is logged in.

        :return: True if logged in, False otherwise.
        """
        if "user" in request.session and request.session["authenticated"]:
            return True
        else:
            return False

    def log_in_user(self, request: Request,username, password):
        """
        Log in a user.

        :param username: The username of the user.
        :param password: The password of the user.
        :param request: The request object.
        """
        if self.authenticate(username, password):
            request.session["user"] = username
            request.session["authenticated"] = True
            return True
        else:
            request.session["user"] = None
            request.session["authenticated"] = None
            return False

    @staticmethod
    def log_out_user(request: Request):
        """
        Log out a user.

        :param request: The request object.
        """
        request.session["user"] = None
        request.session["authenticated"] = None
        request.session.clear()
        return

