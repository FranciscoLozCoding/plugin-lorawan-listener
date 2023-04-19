FROM python:3.8-alpine

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY lorawan_listener.py .
COPY parse.py .
COPY Message.py .

ENTRYPOINT ["python3" , "lorawan_listener.py"]
#ENTRYPOINT ["python3" , "lorawan_listener.py", "--debug", "--dry"] to debug and no messages will be broadcast to Beehive
