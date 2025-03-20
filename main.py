from fastapi import FastAPI, Request, File, UploadFile, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.responses import RedirectResponse
from  pdf import PDF
import os
import json
import threading
import platform
from PyPDF2 import PdfReader, PdfWriter
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from settings import router as settings_router
from upload import router as upload_router
from settings import load_settings_for_file


if platform.system() == "Windows":
    import msvcrt
else:
    import fcntl

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(settings_router, tags=["settings"], prefix="/settings")
app.include_router(upload_router, tags=["upload"], prefix="/upload")
# Use an absolute path for the templates directory to fix the Jinja2 error
base_dir = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))


class ContextProcessorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # load base_folder from json file
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
        else:
            os.environ["BASE_FOLDER"] = "./"
            os.environ["company"] = "Default Company"
            os.environ["upload_folder"] = "./"
            os.environ["appname"] = "A2EDocs"
            os.environ["search_pattern"] = "Account Number\\n(\\d+)\\b"

        request.state.context = {
            "appname": os.environ.get("appname", "A2EDocs"),
            "company": os.environ.get("company", "Default Company"),
            "upload_folder": os.environ.get("upload_folder", "./"),
            "base_folder": os.environ.get("BASE_FOLDER", "./"),
            "search_pattern": os.environ.get("search_pattern", "Account Number\\n(\\d+)\\b"),
        }
        response = await call_next(request)
        return response

app.add_middleware(ContextProcessorMiddleware)

@app.get("/", response_class=HTMLResponse)
def landing_page(request: Request):
    context = {
        "request": request,
        **request.state.context,
    }
    return templates.TemplateResponse("landing.html", context)



@app.get("/select", response_class=HTMLResponse)
def select_for_processing(request: Request):
    upload_folder = os.environ.get("UPLOAD_FOLDER", "./")
    try:
        files = []
        allFiles = os.listdir(upload_folder)
        # include only pdf files
        for f in allFiles:
            if f.endswith(".pdf"):
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
        
    except Exception:
        files = []
    context = {
        "request": request,
        "files": files,
        **request.state.context,
    }
    return templates.TemplateResponse("select-for-processing.html", context)

def process_the_pdf(filename):
    pdf = PDF(filename)
    result = pdf.process_pdf()
    return

@app.post("/process")
async def process_file(filename: str = Form(...)):
    upload_folder = os.environ.get("UPLOAD_FOLDER", "./")
    file_path = os.path.join(upload_folder, filename)
    if not os.path.exists(file_path):
        return {"error": f"File '{filename}' not found."}
    # ...perform processing on file_path...
    process_the_pdf(file_path)
    return {"info": f"File '{filename}' processing completed."}


@app.post("/delete/all/files")
async def process_file(filename: str = Form(...)):
    # load file settings
    settings = load_settings_for_file(filename)
    save_as = settings.get("save_as", "")
    base_folder = os.environ.get("BASE_FOLDER", "./")
    file_count = 0
    # for each folder in base_folder, delete all files that equal save_as value
    for root, dirs, files in os.walk(base_folder):
        for file in files:
            if file == save_as:
                fullpath = os.path.join(root, file)
                print (f"Deleting file: {fullpath}")
                os.remove(fullpath)
                file_count += 1
    return {"info": f"All files with name '{save_as}' deleted. Total files deleted: {file_count}."}


@app.get("/extract-pages/{filename}", response_class=HTMLResponse)
def extract_info(request: Request, filename: str):
    msg = ''
    upload_folder = os.environ.get("UPLOAD_FOLDER", "./")
    file_path = os.path.join(upload_folder, filename)
    pages_file = os.path.join(upload_folder, filename + ".pages")
    if not os.path.exists(pages_file):
        msg = f"File '{filename}' not processed yet."

    settings_file = os.path.join(upload_folder, filename + ".settings")
    settings = {}
    if os.path.exists(settings_file):
        with open(settings_file, "r") as f:
            settings = json.load(f)

    # load pages_file into pages variable
    pages = []
    try:
        with open(pages_file, "r") as f:
            pages = json.load(f)
    except Exception as e:
        msg = f"Error loading pages file: {str(e)}"
        pages = []

    context = {
        "request": request,
        "pdf": filename,
        "pages_file": pages_file,
        "pages": pages,
        "message": msg,
        "settings": settings,
        **request.state.context,
    }

    return templates.TemplateResponse("extract-pages.html", context)

import base64
import json 

@app.get("/extract-one-account/{params}") 
def extract_one_account(params):
    def b32_to_obj(inp):
        decoded = base64.b32decode(inp)
        decoded = decoded.decode("utf-8")
        item = json.loads(decoded)
        return item

    if len(params) % 8 != 0:
        params = params + "=" * (8 - len(params) % 8)

    item = b32_to_obj(params)
    account = item["account"]
    filename = item["filename"]
    page_start = item["page_start"]
    page_end = item["page_end"]

    file_settings = load_settings_for_file(filename)

    save_as = file_settings["save_as"]
    save_date = file_settings["save_date"]

    result = False
    
    pdf = PDF()
    target_folder = pdf.calculate_target_folder(account)
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
    desination_file = os.path.join(target_folder, save_as)

    # extract pages from source_file, from page_start to page_end, and save to desination_file
    source_file = os.path.join(os.environ.get("UPLOAD_FOLDER", "./"), filename)

    reader = PdfReader(source_file)
    writer = PdfWriter()

    for i in range(page_start-1, page_end):
        onepage = reader.pages[i]
        writer.add_page(onepage)

    save_result = False
    try:
        with open(desination_file, "wb") as f:
            writer.write(f)
            result = True
            save_result = True
    except:
        save_result = False

    # update the destination file's date
    if save_result:
        date_and_time = save_date + " 00:00:00"
        set_file_dates(desination_file, date_and_time)

    reader = None 
    writer = None
    return { "result": result }

def set_file_dates(file_path, new_date_time):
    # Convert the time to the required format
    date_time = time.mktime(time.strptime(new_date_time, '%Y-%m-%d %H:%M:%S'))
    # Set the file times
    os.utime(file_path, (date_time, date_time))
    return

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
