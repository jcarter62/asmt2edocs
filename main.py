from fastapi import FastAPI, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.sessions import SessionMiddleware
from utils.logging_config import configure_logging
from utils.middleware import ContextProcessorMiddleware, ClientIPLoggingMiddleware
from settings import router as settings_router
from upload import router as upload_router
from auth import router as auth_router
from select_route import router as select_router
from extract.extract_router import router as extract_router
from notify.notify_router import router as notify_router
from pdf import PDF
import os
import platform
import json
from PyPDF2 import PdfReader, PdfWriter
import time
from starlette.requests import Request
from settings import load_settings_for_file
from auth import Auth
import logging

if platform.system() == "Windows":
    pass
else:
    pass

load_dotenv()

# Configure logging
configure_logging()

app_root = os.getenv("APP_ROOT", os.path.dirname(os.path.abspath(__file__)))

base_dir = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))


app = FastAPI()
app.mount("/static", StaticFiles(directory=os.path.join(base_dir, "static")), name="static")
app.include_router(settings_router, tags=["settings"], prefix="/settings")
app.include_router(upload_router, tags=["upload"], prefix="/upload")
app.include_router(auth_router, tags=["auth"], prefix="/auth")
app.include_router(select_router, tags=["select"], prefix="/select")
app.include_router(extract_router, tags=["extract"], prefix="/extract")
app.include_router(notify_router, tags=["notify"], prefix="/notify")

# Add middleware
app.add_middleware(ClientIPLoggingMiddleware)
app.add_middleware(ContextProcessorMiddleware)
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", ""))

@app.get("/", response_class=HTMLResponse)
def landing_page(request: Request):
    context = {
        "request": request,
        **request.state.context,
    }
    return templates.TemplateResponse("landing.html", context)

def process_the_pdf(filename):
    pdf = PDF(filename)
    result = pdf.process_pdf()
    return

def process_pdf_test(filename):
    pdf = PDF(filename)
    result = pdf.process_pdf_test()
    return result

@app.post("/process")
async def process_file(filename: str = Form(...)):
    upload_folder = os.environ.get("UPLOAD_FOLDER", "./")
    file_path = os.path.join(upload_folder, filename)
    if not os.path.exists(file_path):
        return {"error": f"File '{filename}' not found."}
    # ...perform processing on file_path...
    process_the_pdf(file_path)
    return {"info": f"File '{filename}' processing completed."}


@app.post("/process/test")
async def process_test_file(filename: str = Form(...)):
    upload_folder = os.environ.get("UPLOAD_FOLDER", "./")
    file_path = os.path.join(upload_folder, filename)
    if not os.path.exists(file_path):
        return {"error": f"File '{filename}' not found."}

    result = process_pdf_test(file_path)
    return result;

@app.post("/delete/all/files")
async def delete_all_files(filename: str = Form(...)):  # changed function name
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


@app.get("/favicon.ico", include_in_schema=False)
async def send_favicon_file():
    # send /static/favicon.ico file
    file_path = os.path.join(base_dir, "static", "favicon.ico")
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            content = f.read()
        return HTMLResponse(content=content, media_type="image/x-icon")
    else:
        return HTMLResponse(content="", status_code=404)

@app.get("/dumpfile/{filename}", response_class=HTMLResponse)
async def dump_file(filename: str):
    test_file=os.environ.get("UPLOAD_FOLDER", "./")
    test_file = os.path.join(test_file, filename)
    test_file = test_file + ".test.pdf"
    if not os.path.exists(test_file):
        return {"error": f"File '{test_file}' not found."}

    return FileResponse(test_file, media_type="application/pdf", filename=f"{filename}.test.pdf")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
