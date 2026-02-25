from kafka import KafkaConsumer
import json
import os

os.makedirs('./log', exist_ok=True)

consumer = KafkaConsumer(
    'notes-events',
    bootstrap_servers=['broker:9092'],
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='log',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

file = open('./log/log.txt', 'w+')

for message in consumer:
    try:
        data = message.value
        operation = data.get('operation', '')
        
        if operation == 'create':
            file.write(f"Work created: id={data.get('work_id')}, user={data.get('user_id')}\n")
            
        elif operation == 'update':
            file.write(f"Work updated: id={data.get('work_id')}, user={data.get('user_id')}\n")

        elif operation == 'delete':
            file.write(f"Work deleted: id={data.get('work_id')}, user={data.get('user_id')}\n")
        
        file.flush()

    except Exception as e:
        print(e)