FROM python:3.9-slim-buster

WORKDIR /consumer

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY ./consumer /consumer

ENV PYTHONPATH=/consumer

CMD ["python", "consumer.py"]