FROM python:3.9-slim-buster

WORKDIR /crawler

COPY ./requirements.txt /crawler/requirements.txt 

RUN pip install --no-cache-dir --upgrade -r /crawler/requirements.txt

COPY ./app /crawler/app

ENV PYTHONPATH=/producer

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8020"]