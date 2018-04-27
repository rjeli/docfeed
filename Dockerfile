FROM ubuntu:16.04

RUN apt-get update -y
RUN apt-get install -y python-pip python-dev build-essential

WORKDIR /app
COPY requirements.txt /app
RUN pip install -r requirements.txt

COPY . /app

CMD ["python", "app.py"]
