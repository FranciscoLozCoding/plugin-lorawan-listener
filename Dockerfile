FROM python:3.8-alpine

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY lorawan_listener.py .
COPY parse.py .
COPY Message.py .
COPY Callbacks.py .
COPY client.py .

ENTRYPOINT ["python3" , "client.py"]
