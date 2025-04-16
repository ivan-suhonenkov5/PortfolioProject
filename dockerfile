FROM python:3.10-slim

# Установка системных библиотек, включая wkhtmltopdf
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    wkhtmltopdf \
    && rm -rf /var/lib/apt/lists/*

# Установка переменной окружения для предотвращения запуска интерактивного режима
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Установка рабочей директории
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Установка Python-зависимостей
RUN pip install --upgrade pip && pip install -r requirements.txt

# Копируем остальную часть проекта
COPY . .

# Указываем путь к wkhtmltopdf в Linux
ENV WKHTMLTOPDF_PATH=/usr/bin/wkhtmltopdf

# Переменная для Flask
ENV FLASK_APP=run.py

RUN wkhtmltopdf --version

# Запуск
CMD ["python", "run.py"]
