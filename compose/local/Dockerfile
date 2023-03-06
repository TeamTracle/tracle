FROM python:3

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /app

RUN apt-get update && apt-get -y -q install ffmpeg memcached

RUN pip install --upgrade pip
COPY requirements_dev.txt .
RUN pip install -r requirements_dev.txt

COPY ./compose/local/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

COPY . .
