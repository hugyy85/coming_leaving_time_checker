from fastapi import FastAPI, Request, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from time_checker import insert_data_from_xml_to_db


app = FastAPI()

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.post('/upload')
async def process_xml(file: UploadFile = File(...)):
    # todo add validation to file, use only .xml
    insert_data_from_xml_to_db(file.file)
    return {"filename": file.filename}