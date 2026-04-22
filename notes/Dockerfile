FROM python:3.13-slim

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y --no-install-recommends curl librdkafka-dev && rm -rf /var/lib/apt/lists/*

COPY app/requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn "uvicorn[standard]"

COPY app/*.py ./

EXPOSE 8000

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "1", "main:app"]