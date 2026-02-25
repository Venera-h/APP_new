import json
from kafka import KafkaProducer
from kafka.errors import KafkaError

class KafkaService:
    def __init__(self):
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=['broker:9092'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
        except KafkaError:
            self.producer = None
    
    def publish_event(self, topic: str, event_data: dict):
        if self.producer:
            try:
                self.producer.send(topic, event_data)
                self.producer.flush()
            except Exception as e:
                print(f"Failed to publish event: {e}")

kafka_service = KafkaService()
