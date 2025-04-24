from fastapi import Request, HTTPException, APIRouter
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from dotenv import load_dotenv
import requests
import os

router = APIRouter()

# base_dir = os.path.dirname(os.path.abspath(__file__))
# templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

@router.get("/login")
def auth_login_get(request: Request):
    context = {
        "request": request,
        **request.state.context,
    }
    return templates.TemplateResponse("login.html", context)

@router.post("/login")
def auth_login_post(request: Request, username: str, password: str):
    auth = Auth()
    if auth.log_in_user(request, username, password):
        # Redirect to the settings page after successful login
        return RedirectResponse(url="/", status_code=200)
    else:
        context = {
            "request": request,
            "error": "Invalid username or password",
            **request.state.context,
        }
        return templates.TemplateResponse("settings.html", context)

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

    def authenticate(self, username, password):
        """
        Authenticate a user.

        :param username: The username of the user.
        :param password: The password of the user.
        :return: True if authenticated, False otherwise.
        """
        # Placeholder for actual authentication logic
        # call the api with username and password and group
        results = False
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
        url = f"{url}/auth/{group}"
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
        return results

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

