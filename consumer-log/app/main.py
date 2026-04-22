# Задание 1: простой consumer, который логирует все события из Kafka в файл
from kafka import KafkaConsumer
import json
import os

os.makedirs('./log', exist_ok=True)

# Подписываемся на топик 'operations', где публикуются все события сущности
consumer = KafkaConsumer(
    'operations',
    bootstrap_servers=['broker:9092'],
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='log-group',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

file = open('./log/log.txt', 'a')

for message in consumer:
    try:
        event = message.value
        op = event.get('op', '')
        note = event.get('note', {})

        # Логируем каждое событие в файл
        if op == 'c':
            file.write(f"[CREATE] id={note.get('id')}, title={note.get('title')}\n")
        elif op == 'u':
            file.write(f"[UPDATE] id={note.get('id')}\n")
        elif op == 'd':
            file.write(f"[DELETE] id={note.get('id')}\n")
        else:
            file.write(f"[UNKNOWN] {event}\n")

        file.flush()
    except Exception as e:
        print(e)
