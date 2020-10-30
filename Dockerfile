FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

RUN pip install --no-cache-dir -U pip setuptools wheel && \
    pip install --no-cache-dir poetry~=1.1.3

COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.create false
RUN poetry install

COPY . /app



