# Задание 1: consumer для записи событий в БД
from kafka import KafkaConsumer
import json
from sqlalchemy import create_engine, Column, String, Integer, Text
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@notes_db:5432/notesdb')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Таблица для хранения всех событий из Kafka
class EventLog(Base):
    __tablename__ = 'event_log'
    id = Column(Integer, primary_key=True, autoincrement=True)
    op = Column(String)       # тип операции: c / u / d
    note_id = Column(String)
    payload = Column(Text)    # полное событие в JSON

Base.metadata.create_all(engine)

# Подписываемся на топик 'operations'
consumer = KafkaConsumer(
    'operations',
    bootstrap_servers=['broker:9092'],
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='db-writer-group',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

session = SessionLocal()

for message in consumer:
    try:
        event = message.value
        op = event.get('op', '')
        note = event.get('note', {})
        note_id = note.get('id')

        # Записываем событие в БД
        session.add(EventLog(
            op=op,
            note_id=note_id,
            payload=json.dumps(event)
        ))
        session.commit()
        print(f"[DB] Saved event op={op}, note_id={note_id}")
    except Exception as e:
        session.rollback()
        print(e)
