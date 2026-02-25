FROM python:3.13-alpine 

WORKDIR /usr/src/app

RUN apk add --no-cache curl

COPY app/requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt


COPY app/*.py ./

CMD ["python", "main.py"]