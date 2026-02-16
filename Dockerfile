FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код бота
COPY video_downloader_bot.py .

# Создаем директорию для загрузок
RUN mkdir -p downloads

# Переменная окружения для токена (будет передана Railway)
ENV TOKEN=${TOKEN}

# Запускаем бота
CMD ["python", "-u", "video_downloader_bot.py"]
