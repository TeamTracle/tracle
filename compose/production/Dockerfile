FROM python:3

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /app

RUN apt-get update && apt-get -y -q install ffmpeg memcached curl gnupg
RUN curl -sL https://deb.nodesource.com/setup_16.x | bash -
RUN apt-get -y -q install npm

RUN npm i -g postcss postcss-cli autoprefixer

RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY ./compose/production/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

COPY ./src/ .

ENV DJANGO_SETTINGS_MODULE tracle.settings.production

RUN python manage.py collectstatic -i '*.scss' --no-input -c
RUN python manage.py compress
