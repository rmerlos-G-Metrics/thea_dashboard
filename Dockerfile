FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY .env .env

EXPOSE 8005

CMD ["gunicorn", "-b", "0.0.0.0:8050", "app:server"]