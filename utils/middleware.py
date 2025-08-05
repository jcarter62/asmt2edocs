import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from auth import Auth
import os
import json


class ContextProcessorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logged_in = Auth().is_user_logged_in(request)
        username = request.session.get("user", "") if logged_in else ""

        settings_loader()  # Load settings from JSON file

        # # Load settings from JSON file
        # app_data_folder = os.getenv("APP_DATA", "~/")
        #
        # settings_file = os.path.join(app_data_folder, "settings.json")
        # if os.path.exists(settings_file):
        #     with open(settings_file, "r") as f:
        #         settings = json.load(f)
        #         os.environ["base_folder"] = settings.get("base_folder", "./")
        #         os.environ["company"] = settings.get("company", "Default Company")
        #         os.environ["upload_folder"] = settings.get("upload_folder", "./")
        #         os.environ["appname"] = settings.get("appname", "A2EDocs")
        #         os.environ["search_pattern"] = settings.get("search_pattern", "Account Number\\n(\\d+)\\b")
        #         os.environ["test_flag"] = settings.get("test_flag", "off")
        #         os.environ["test_email"] = settings.get("test_email", "")
        # else:
        #     os.environ["BASE_FOLDER"] = "./"
        #     os.environ["company"] = "Default Company"
        #     os.environ["upload_folder"] = "./"
        #     os.environ["appname"] = "A2EDocs"
        #     os.environ["search_pattern"] = "Account Number\\n(\\d+)\\b"
        #     os.environ["test_flag"] = "off"
        #     os.environ["test_email"] = ""

        request.state.context = {
            "appname": os.environ.get("appname", "A2EDocs"),
            "company": os.environ.get("company", "Default Company"),
            "upload_folder": os.environ.get("upload_folder", "./"),
            "base_folder": os.environ.get("BASE_FOLDER", "./"),
            "search_pattern": os.environ.get("search_pattern", "Account Number\\n(\\d+)\\b"),
            "logged_in": logged_in,
            "username": username,
            "test_flag": os.environ.get("test_flag", "off"),
            "test_email": os.environ.get("test_email", ""),
        }
        response = await call_next(request)
        return response

class ClientIPLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host  # Extract client IP address
        logging.info(f"Client IP: {client_ip} - {request.method} {request.url}")
        response = await call_next(request)
        return response

def settings_loader():
    app_data_folder = os.getenv("APP_DATA", "~/")
    settings_file = os.path.join(app_data_folder, "settings.json")
    if os.path.exists(settings_file):
        with open(settings_file, "r") as f:
            settings = json.load(f)
            os.environ["base_folder"] = settings.get("base_folder", "./")
            os.environ["company"] = settings.get("company", "Default Company")
            os.environ["upload_folder"] = settings.get("upload_folder", "./")
            os.environ["appname"] = settings.get("appname", "A2EDocs")
            os.environ["search_pattern"] = settings.get("search_pattern", "Account Number\\n(\\d+)\\b")
            os.environ["test_flag"] = settings.get("test_flag", "off")
            os.environ["test_email"] = settings.get("test_email", "")
    else:
        os.environ["BASE_FOLDER"] = "./"
        os.environ["company"] = "Default Company"
        os.environ["upload_folder"] = "./"
        os.environ["appname"] = "A2EDocs"
        os.environ["search_pattern"] = "Account Number\\n(\\d+)\\b"
        os.environ["test_flag"] = "off"
        os.environ["test_email"] = ""
