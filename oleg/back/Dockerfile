FROM python:3.9-slim-buster

WORKDIR /api

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY ./api /api/api

ENV PYTHONPATH=/api

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]