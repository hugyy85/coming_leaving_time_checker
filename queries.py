from xml.etree.ElementTree import fromstring
from datetime import datetime, timedelta

from models import PersonTimeChecker, Report
from config import DATETIME_FORMAT, COUNT_PERSONS_TO_WRITE_IN_DB_FOR_ONE_QUERY, log

from sqlalchemy import func, and_
from sqlalchemy.orm import Session
from fastapi import UploadFile


def insert_data_from_xml_to_db(file: UploadFile, session: Session) -> Report:
    report = Report(report_name=file.filename)
    session.add(report)
    session.commit()
    persons_to_db = []
    first_line = '<?xml version="1.0" encoding="UTF-8"?>\n'
    new_result = first_line
    for line in file.file:
        line = line.decode("utf-8")

        if line == first_line:
            continue
        new_result += line
        if line.strip() == '</person>':
            new_result += '</people>'

            root = fromstring(new_result)
            person_tag = root.find('person')
            full_name = person_tag.attrib['full_name']
            coming_datetime = person_tag.find('start').text
            leaving_datetime = person_tag.find('end').text
            new_result = first_line + '<people>\n'

            coming_datetime = datetime.strptime(coming_datetime, DATETIME_FORMAT)
            leaving_datetime = datetime.strptime(leaving_datetime, DATETIME_FORMAT)
            assert leaving_datetime > coming_datetime, \
                f'end time - {leaving_datetime} earlier than start time {coming_datetime}'
            person_options = dict(
                full_name=full_name,
                coming_datetime=coming_datetime,
                leaving_datetime=leaving_datetime,
                report_id=report.report_id
            )

            if coming_datetime.date() != leaving_datetime.date():
                # we groups by date on coming_datetime, so we use options with coming_datetime
                options = dict(year=coming_datetime.year,
                               month=coming_datetime.month,
                               day=coming_datetime.day,
                               hour=0,
                               minute=0,
                               second=0)

                # add first day time Person
                person_options['leaving_datetime'] = datetime(**options) + timedelta(days=1)
                persons_to_db.append(PersonTimeChecker(**person_options))

                delta = leaving_datetime - coming_datetime
                count_days = 0
                while delta.days != count_days:
                    count_days += 1
                    start_next_day = datetime(**options) + timedelta(days=count_days)
                    if start_next_day.date() == leaving_datetime.date():
                        # add last day time Person
                        end_next_day = leaving_datetime
                    else:
                        end_next_day = datetime(**options) + timedelta(days=count_days + 1)
                    person_options.update({
                        'coming_datetime': start_next_day,
                        'leaving_datetime': end_next_day
                    })
                    # add every new day time Person
                    persons_to_db.append(PersonTimeChecker(**person_options))

            else:
                persons_to_db.append(PersonTimeChecker(**person_options))

            if len(persons_to_db) >= COUNT_PERSONS_TO_WRITE_IN_DB_FOR_ONE_QUERY:
                session.add_all(persons_to_db)
                session.commit()
                persons_to_db.clear()

    session.add_all(persons_to_db)
    session.commit()
    return report


def get_worked_time(report_id: int,
                    session: Session,
                    person: str = None,
                    from_date: datetime = None,
                    to_date: datetime = None) -> dict:
    seconds = func.sum(
        func.strftime('%s', PersonTimeChecker.leaving_datetime) - func.strftime('%s', PersonTimeChecker.coming_datetime)
    )
    grouped_date = func.date(PersonTimeChecker.coming_datetime).label('grouped_date')
    query = session.query(
        grouped_date, seconds) \
        .group_by('grouped_date').filter_by(report_id=report_id)
    if person:
        query = query.filter_by(full_name=person)

    if from_date and to_date:
        assert from_date < to_date, f'end time - {to_date} earlier than start time {from_date}'
        query = query.filter(and_(grouped_date >= from_date, grouped_date <= to_date))
    elif from_date and not to_date:
        query = query.filter(grouped_date >= from_date)
    elif not from_date and to_date:
        query = query.filter(grouped_date <= to_date)

    work_hours = {datetime.strptime(x[0], '%Y-%m-%d').strftime('%d.%m.%Y'): round(x[1] / 3600, 2) for x in query.all()}
    return work_hours


def get_all_reports(session: Session) -> list:
    reports = session.query(Report).all()
    return reports


def get_all_persons(session: Session) -> list:
    persons = session.query(PersonTimeChecker.full_name).group_by(PersonTimeChecker.full_name).all()
    return persons
