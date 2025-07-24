from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from settings import load_settings_for_file
from pdf import PDF
import os
import time
from pdf import PDF
from PyPDF2 import PdfReader, PdfWriter
import pikepdf
import json

app_root = os.getenv("APP_ROOT", os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(app_root, "templates"))

router = APIRouter()

@router.get("/pages/{filename}", response_class=HTMLResponse)
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

@router.get("/one-account/{params}")
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
    destination_file = os.path.join(target_folder, save_as)

    # extract pages from source_file, from page_start to page_end, and save to destination_file
    source_file = os.path.join(os.environ.get("UPLOAD_FOLDER", "./"), filename)

    save_result = False
    try:
        with pikepdf.Pdf.open(source_file) as src_pdf:
            with pikepdf.Pdf.new() as dest_pdf:
                for i in range(page_start - 1, page_end):
                    dest_pdf.pages.append(src_pdf.pages[i])
                dest_pdf.save(destination_file)
                result = True
                save_result = True
    except Exception as e:
        save_result = False

    # update the destination file's date
    if save_result:
        date_and_time = save_date + " 00:00:00"
        set_file_dates(destination_file, date_and_time)

    return {"result": result}

def set_file_dates(file_path, new_date_time):
    # Convert the time to the required format
    date_time = time.mktime(time.strptime(new_date_time, '%Y-%m-%d %H:%M:%S'))
    # Set the file times
    os.utime(file_path, (date_time, date_time))
    return

