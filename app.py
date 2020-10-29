from typing import Any, Optional, Union, List
from datetime import date

from config import log

from fastapi import FastAPI, Request, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from queries import insert_data_from_xml_to_db, get_all_reports, get_worked_time, get_all_persons


app = FastAPI()

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
@app.post("/", response_class=HTMLResponse)
async def home(request: Request, file: UploadFile = File(Any)):
    context = {"request": request}
    if request.method == 'POST':
        # todo add validation to file, use only .xml
        try:
            context['report'] = insert_data_from_xml_to_db(file)
        except Exception as e:
            log.error(f'file error processing: {e}', exc_info=True)
            # only for demonstration error at review
            context['error'] = e

    return templates.TemplateResponse("home.html", context)


@app.get("/results", response_class=HTMLResponse)
async def show_results(request: Request):
    reports = get_all_reports()
    return templates.TemplateResponse("results.html", {
        "request": request,
        "reports": reports
    })


@app.get("/results/{report_id}", response_class=HTMLResponse)
async def show_results(request: Request, report_id: int,
                       from_date: Union[date, str] = None,
                       to_date: Union[date, str] = None,
                       person: Optional[str] = None):
    work_hours = get_worked_time(report_id, from_date=from_date, to_date=to_date, person=person)
    persons = get_all_persons()
    return templates.TemplateResponse("show_result.html", {
        "request": request,
        "report": report_id,
        "work_hours": work_hours,
        "persons": persons,
        "who_worked": person
    })
