FROM pytorch/pytorch:latest

WORKDIR /consumer

COPY requirements.txt .

RUN pip --default-timeout=1000 install -r requirements.txt

COPY ./consumer /consumer

ENV PYTHONPATH=/consumer

CMD ["python", "consumer.py"]