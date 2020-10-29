from xml.etree.ElementTree import iterparse
from datetime import datetime, timedelta

from models import PersonTimeChecker, Session, Report
from config import DATETIME_FORMAT, COUNT_PERSONS_TO_WRITE_IN_DB_FOR_ONE_QUERY, log

from sqlalchemy import func, and_


def insert_data_from_xml_to_db(file):
    session = Session()
    report = Report(report_name=file.filename)
    session.add(report)
    session.commit()
    full_name = coming_datetime = leaving_datetime = None
    persons_to_db = []
    context = iterparse(file.file, events=("start", "end"))
    for event, elem in context:
        if event == 'start' and elem.tag == 'person':
            full_name = elem.attrib['full_name']
        elif elem.tag == 'start':
            coming_datetime = elem.text
        elif elem.tag == 'end':
            leaving_datetime = elem.text

        if event == 'end' and elem.tag == 'person':
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

            elem.clear()

    session.add_all(persons_to_db)
    session.commit()
    del context
    return report


def get_worked_time(report_id: int, person: str = None, from_date: datetime = None, to_date: datetime = None) -> dict:
    session = Session()
    seconds = func.sum(
        func.strftime('%s', PersonTimeChecker.leaving_datetime) - func.strftime('%s', PersonTimeChecker.coming_datetime)
    )
    grouped_date = func.date(PersonTimeChecker.coming_datetime).label('grouped_date')
    query = session.query(
        grouped_date, seconds)\
        .group_by('grouped_date').filter_by(report_id=report_id)
    if person:
        query = query.filter_by(full_name=person)

    if from_date and to_date:
        query = query.filter(and_(grouped_date >= from_date.date(), grouped_date <= to_date.date()))
    elif from_date and not to_date:
        query = query.filter(grouped_date >= from_date)
    elif not from_date and to_date:
        query = query.filter(grouped_date <= to_date)

    work_hours = {datetime.strptime(x[0], '%Y-%m-%d'): round(x[1] / 3600, 2) for x in query.all()}
    return work_hours


def get_all_reports():
    session = Session()
    reports = session.query(Report).all()
    return reports


def get_all_persons():
    session = Session()
    persons = session.query(PersonTimeChecker.full_name).group_by(PersonTimeChecker.full_name).all()
    return persons
















