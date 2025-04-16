FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    wkhtmltopdf \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip && pip install -r requirements.txt

ENV WKHTMLTOPDF_PATH=/usr/bin/wkhtmltopdf

COPY . .

ENV FLASK_APP=run.py

CMD ["python", "run.py"]
