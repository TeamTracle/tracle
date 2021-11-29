FROM python:3

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /app

RUN apt-get update && apt-get -y -q install ffmpeg memcached

RUN pip install --upgrade pip
COPY requirements.txt .
COPY requirements_dev.txt .
RUN pip install -r requirements.txt -r requirements_dev.txt

COPY . .
