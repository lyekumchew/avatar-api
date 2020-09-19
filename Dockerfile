FROM python:3-slim

# set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip3 install Django djangorestframework django-filter django-cors-headers django-queryset-csv markdown xlsxwriter \
    networkx statsmodels numpy sklearn psycopg2-binary

WORKDIR /app

ADD . /app

RUN chmod +x ./entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]