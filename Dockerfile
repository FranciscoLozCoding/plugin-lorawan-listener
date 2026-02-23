FROM python:3.8-alpine

WORKDIR /app

# Install git for codec cloning
RUN apk add --no-cache git

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY ./app .

ENTRYPOINT ["python3" , "main.py"]
