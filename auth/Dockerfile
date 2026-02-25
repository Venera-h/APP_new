FROM python:3.13-alpine 

RUN apk add --no-cache curl \
                        librdkafka-dev 

WORKDIR /usr/srs/app

COPY app/requirements.txt ./


RUN pip install --no-cache-dir -r requirements.txt
RUN pip install  --no-cache-dir gunicorn "uvicorn[standard]"
COPY app/*.py ./

EXPOSE 8000

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "1", "main:app"]