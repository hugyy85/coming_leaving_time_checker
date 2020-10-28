from xml.etree.ElementTree import iterparse
from datetime import datetime, timedelta
import logging
import sys

from models import PersonTimeChecker, Session
from config import DATETIME_FORMAT, COUNT_PERSONS_TO_WRITE_IN_DB_FOR_ONE_QUERY, DEBUG


log = logging.getLogger(__name__)
log.level = logging.DEBUG if DEBUG else logging.ERROR
log.addHandler(logging.StreamHandler(sys.stderr))
log.debug('ATTENTION!!! YOU USE DEBUG-MODE')


def insert_data_from_xml_to_db(file_name):
    session = Session()
    q = session.query(PersonTimeChecker).order_by(PersonTimeChecker.report_id.desc())
    if not session.query(q.exists()).scalar():
        report_id = 1
    else:
        report_id = q.first().report_id + 1

    full_name = coming_datetime = leaving_datetime = None
    persons_to_db = []
    context = iterparse(file_name, events=("start", "end"))
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
                report_id=report_id
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
    return


def calculate_time():
    session = Session()
    query = session.query(PersonTimeChecker).all()
    # q = int(query.leaving_datetime.strftime('%s')) - int(query.coming_datetime.strftime('%s'))
    a = session.query(PersonTimeChecker).group_by(query.coming_datetime.date())
    query = query.sum().all()
    q = ''
    """
    SELECT date(coming_datetime) as dc,
        sum(strftime('%s' , leaving_datetime) - strftime('%s' , coming_datetime)) as diff from coming_leaving
        GROUP BY dc
        HAVING diff
        ;
    """
    """
        SELECT date(coming_datetime) as dc,
        sum(strftime('%s' , leaving_datetime) - strftime('%s' , coming_datetime)) as diff from coming_leaving
		where dc BETWEEN "2011-12-22" AND "2011-12-23"
        GROUP BY dc
        HAVING diff
    """

calculate_time()