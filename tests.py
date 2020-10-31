import datetime
import os
import json

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app, get_db
from models import Report, Base
from config import DATETIME_FORMAT

NAME_TEST_DB = 'test.sqlite3'
TEST_DB = f'sqlite:///{NAME_TEST_DB}'
WORK_DIRECTORY = os.getcwd()

try:
    os.remove(f'{WORK_DIRECTORY}/{NAME_TEST_DB}')
except FileNotFoundError:
    pass

engine = create_engine(
    TEST_DB, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_main():
    session = TestingSessionLocal()
    q = session.query(Report)

    response = client.get('/')
    assert response.status_code == 200
    assert session.query(q.exists()).scalar() is False
    test_files = ['new_small.xml', 'new.xml']
    # test adding file
    for file_name in test_files:
        response = client.post('/', files={
            'file': (file_name, open(f'{os.getcwd()}/test_data/{file_name}', 'rb'), 'text/plain')
        })
        assert response.status_code == 200
        payload = response.context['report']
        assert payload.report_name == file_name
        assert session.query(q.exists()).scalar() is True
        last_report = q.order_by(Report.report_id.desc()).first()
        assert payload.report_id == last_report.report_id

    # test listing reports
    response = client.get('/results')
    assert response.status_code == 200
    reports = response.context['reports']
    assert len(reports) == len(test_files)

    checked_data = {
        'new_small.xml':
            {'work_hours':
                 {'21.12.2011': 17.12, '22.12.2011': 8.32, '23.12.2011': 14.33, '24.12.2011': 10.99},
             'persons': ['a.snova', 'a.snovkaa', 'a.stepanova', 'i.ivanov']},
        'new.xml':
            {'work_hours': {'21.12.2011': 171222.22, '22.12.2011': 83180.56, '23.12.2011': 13180.56},
             'persons': ['a.snova', 'a.snovkaa', 'a.stepanova', 'i.ivanov']}}

    # test show working_time
    for report in reports:
        response = client.get(f'/results/{report.report_id}')
        assert response.status_code == 200
        payload = response.context
        assert payload['report'] == report.report_id
        assert payload['work_hours'] == checked_data[report.report_name]['work_hours']
        for person in payload['persons']:
            assert person.full_name in checked_data[report.report_name]['persons']
        assert payload['who_worked'] is None

    # test working_time with params
    with open(f'{WORK_DIRECTORY}/test_data/test_data.json', 'r') as f:
        checked_data = json.loads(f.read())

    for report in reports:

        for data in checked_data[report.report_name]:
            params = {
                'from_date': '',
                'to_date': '',
                'person': ''
            }
            params.update(data['param'])
            response = client.get(f'/results/{report.report_id}', params=params)
            assert response.status_code == 200
            payload = response.context
            assert payload['work_hours'] == data['result']
