FROM python:3.6

MAINTAINER Vadim Mazaev <vadim.mazaev@gmail.com>

RUN apt-get update
RUN apt-get install -y vim

COPY requirements.txt /
RUN pip install -r requirements.txt

COPY . /src

CMD cd src && python3 main.py
