FROM python:3.9-slim-buster

WORKDIR /bot

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY ./bot /bot/bot

ENV PYTHONPATH=/bot

CMD ["python3", "bot/main.py"]