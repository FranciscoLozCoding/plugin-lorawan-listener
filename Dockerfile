FROM python:3.8-alpine

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY main.py .
COPY parse.py .
COPY client.py .

ENTRYPOINT ["python3" , "main.py"]
