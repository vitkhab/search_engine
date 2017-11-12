FROM python:alpine

COPY requirements.txt /
RUN pip install -r requirements.txt

COPY . /search_engine
WORKDIR /search_engine
ENV FLASK_APP=search.py

CMD flask run --host=0.0.0.0 