FROM python:3.8-slim

WORKDIR /app

COPY backend/requirements.txt /app

RUN python -m pip install --upgrade pip

RUN pip3 install -r /app/requirements.txt --no-cache-dir

COPY ./ .

CMD ["gunicorn", "--bind", "0:8000", "foodgram.wsgi:application"]
