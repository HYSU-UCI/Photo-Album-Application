FROM --platform=amd64 python:3.10-slim-buster

COPY ./requirements.txt /app/

WORKDIR /app

RUN pip install -r requirements.txt

RUN useradd -m web

ARG UPLOADS_PATH

ENV UPLOADS_PATH=$UPLOADS_PATH

COPY . /app

RUN mkdir -p "$UPLOADS_PATH" && \
    chown -R web:web "$UPLOADS_PATH" && \
    chown -R web:web /app

USER web

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
