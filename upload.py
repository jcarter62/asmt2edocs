from fastapi import APIRouter, Request, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
import os
import json
from auth import Auth

router = APIRouter()

base_dir = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

# Optionally, add a route to render the upload page
@router.get("/", response_class=HTMLResponse)
def upload_form(request: Request):
    if not Auth().is_user_logged_in(request):
        # Redirect to the login page if not logged in
        return RedirectResponse(url="/auth/login", status_code=303)

    # list all .pdf files in the upload_folder and add to the context
    upload_folder = os.environ.get("UPLOAD_FOLDER", "./")
    try:
        files = []
        allFiles = os.listdir(upload_folder)
        # include only pdf files
        for f in allFiles:
            if f.endswith(".pdf") and ( not f.endswith(".test.pdf")):
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
    except Exception as e:
        files = []

    # if files is not empty, sort ascending by filename
    if len(files) > 0:
        files = sorted(files, key=lambda x: x["filename"])

    context = {
        "request": request,
        "files": files,
        **request.state.context,
    }
    return templates.TemplateResponse("upload.html", context)

@router.post("/")
async def upload_pdf(request: Request, file: UploadFile = File(...)):
    upload_folder = os.environ.get("UPLOAD_FOLDER", "./")
    file_location = os.path.join(upload_folder, file.filename)
    with open(file_location, "wb") as f:
        f.write(await file.read())

    upload_form_url = request.url_for("upload_form")
    return RedirectResponse(upload_form_url, status_code=303)

@router.post("/delete/{filename}")
async def delete_file(request: Request, filename: str):
    upload_folder = os.environ.get("UPLOAD_FOLDER", "./")

    # for all files that start with filename, delete them
    for f in os.listdir(upload_folder):
        if f.startswith(filename):
            os.remove(os.path.join(upload_folder, f))

    result = {"success": True}

    return result

