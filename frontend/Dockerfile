FROM --platform=amd64 python:3.10-slim-buster

COPY requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app/

CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:3000"]
