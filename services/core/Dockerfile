FROM python:3.13-slim

WORKDIR /app
COPY app/ /app/

RUN pip install paho-mqtt

CMD ["python", "main.py"]
