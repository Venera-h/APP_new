from kafka import KafkaConsumer
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@notes_db:5432/notesdb')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

consumer = KafkaConsumer(
    'notes-events',
    bootstrap_servers=['broker:9092'],
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='mygroup',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

session = SessionLocal()

for message in consumer:
    try:
        data = message.value
        operation = data.get('operation', '')
        
        if operation == 'create':
            print(f"Work created: {data}")
            
        elif operation == 'update':
            print(f"Work updated: {data}")

        elif operation == 'delete':
            print(f"Work deleted: {data}")

    except Exception as e:
        print(e)