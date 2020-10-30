from typing import Optional, Union
from datetime import date

from config import log

from fastapi import FastAPI, Request, File, UploadFile, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from queries import insert_data_from_xml_to_db, get_all_reports, get_worked_time, get_all_persons
from models import Base, engine, SessionLocal

Base.metadata.create_all(bind=engine)

app = FastAPI()

templates = Jinja2Templates(directory="templates")


# Dependency
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
@app.post("/", response_class=HTMLResponse)
async def home(request: Request, file: UploadFile = File(None), db: Session = Depends(get_db)):
    context = {"request": request}
    if request.method == 'POST':
        # todo add validation to file, use only .xml
        try:
            context['report'] = insert_data_from_xml_to_db(file, db)
        except Exception as e:
            log.error(f'file error processing: {e}', exc_info=True)
            context['error'] = e

    return templates.TemplateResponse("home.html", context)


@app.get("/results", response_class=HTMLResponse)
async def show_list_results(request: Request, db: Session = Depends(get_db)):
    reports = get_all_reports(db)
    return templates.TemplateResponse("results.html", {
        "request": request,
        "reports": reports
    })


@app.get("/results/{report_id}", response_class=HTMLResponse)
async def show_result(request: Request, report_id: int,
                      from_date: Union[date, str] = None,
                      to_date: Union[date, str] = None,
                      person: Optional[str] = None,
                      db: Session = Depends(get_db)):
    context = {
        "request": request,
        "report": report_id,
        "work_hours": '',
        "persons": '',
        "who_worked": person
    }
    try:
        context['work_hours'] = get_worked_time(report_id, session=db, from_date=from_date, to_date=to_date, person=person)
    except AssertionError:
        log.error(f'end time - {to_date} earlier than start time {from_date}')
        context['error'] = f'Дата конца периода выбрана {to_date} выбрана ранее даты начала {from_date}'
    context['persons'] = get_all_persons(db)
    return templates.TemplateResponse("show_result.html", context)
