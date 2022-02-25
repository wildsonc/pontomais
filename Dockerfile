FROM python:3.8-slim-buster

WORKDIR /code

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip

COPY requirements.txt /code/

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . /code

CMD ["/code/start-server.sh"]