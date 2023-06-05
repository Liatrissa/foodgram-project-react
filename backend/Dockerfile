FROM python:3.8-slim

RUN apt-get update && apt-get install -y \
    && pip install --upgrade pip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip3 install -r requirements.txt --no-cache-dir

COPY . .
CMD ["gunicorn", "--bind", "0:8000", "foodgram.wsgi:application"]
