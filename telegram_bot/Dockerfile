FROM python:3.13-slim

WORKDIR /telegram_bot

COPY telegram_bot/requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY telegram_bot/ .
COPY common ./common

CMD ["python", "telegram_bot.py"]