FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /code

# system deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# install python deps
COPY requirements.txt /code/
RUN pip install --upgrade pip && pip install -r requirements.txt

# copy project
COPY . /code/

# entrypoint
COPY docker-entrypoint.sh /code/docker-entrypoint.sh
RUN chmod +x /code/docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/code/docker-entrypoint.sh"]