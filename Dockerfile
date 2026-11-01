FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY alembic.ini /app/alembic.ini
COPY server /app/server

EXPOSE 8000

CMD ["sh", "-c", "alembic -c /app/alembic.ini upgrade head && python -m uvicorn server.main:app --host 0.0.0.0 --port 8000"]
