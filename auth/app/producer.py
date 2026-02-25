from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers=['broker:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def produce(data):
    producer.send('notes-events', data)
    producer.flush()