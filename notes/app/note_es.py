# Event Sourcing - паттерн хранения изменений состояния как последовательности событий.
# Единственный источник правды - Kafka topic с событиями.
# Текущее состояние получается через replay всех событий с начала топика.

from confluent_kafka import Consumer, Producer
import json
import sys

# Consumer читает все события из Kafka и фильтрует по id сущности
class NoteEventConsumer:
    @classmethod
    def load_events(cls, id):
        # Читаем ВСЕ события из топика с самого начала (earliest)
        # и фильтруем только те, что относятся к нужной сущности по id
        events = []
        c = Consumer({
            'bootstrap.servers': 'broker:9092',
            'group.id': f'replay-{id}',  # уникальная группа для каждого replay
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False
        })
        c.subscribe(['operations'])
        while True:
            msg = c.poll(timeout=1.0)
            if msg is None:
                break
            if msg.error():
                print(f"Consumer error: {msg.error()}", file=sys.stderr)
                break
            try:
                event = json.loads(msg.value().decode('utf-8'))
                op = event.get('op')
                # Фильтрация по id сущности в зависимости от типа события
                if op in ('c', 'u') and event.get('note', {}).get('id') == id:
                    events.append(event)
                elif op == 'd' and event.get('note', {}).get('id') == id:
                    events.append(event)
            except Exception as e:
                print(str(e), file=sys.stderr)
        c.close()
        return events


# Producer публикует события изменений в Kafka
class NoteEventProducer:
    __p__ = Producer({'bootstrap.servers': 'broker:9092'})

    @classmethod
    def produce_event(cls, operation, note):
        # Публикуем событие в Kafka: op = 'c' (create) | 'u' (update) | 'd' (delete)
        cls.__p__.produce('operations', json.dumps({
            'op': operation,
            'note': note
        }).encode('utf-8'))
        cls.__p__.flush()


class NoteEventSourcing:
    """
    Чистый Event Sourcing без оптимизации чтения.
    Состояние сущности восстанавливается каждый раз через replay всех событий из Kafka.
    """

    def __init__(self, id):
        self.id = id
        self.title = None
        self.content = None
        self.owner_id = None
        self.work_name = None
        self.student = None
        self.variant_number = None
        self.level_number = None
        self.submission_date = None
        self.grade = None
        self.version = 0       # версия для отслеживания количества обновлений
        self.deleted = False
        self.exists = False    # True если событие 'c' было найдено

    def replay(self):
        # Replay: применяем все события по порядку, чтобы получить текущее состояние
        events = NoteEventConsumer.load_events(self.id)
        for event in events:
            op = event['op']
            note = event.get('note', {})
            if op == 'c':
                # Применяем событие создания - инициализируем все поля
                self.title = note.get('title')
                self.content = note.get('content')
                self.owner_id = note.get('owner_id')
                self.work_name = note.get('work_name')
                self.student = note.get('student')
                self.variant_number = note.get('variant_number')
                self.level_number = note.get('level_number')
                self.submission_date = note.get('submission_date')
                self.grade = note.get('grade')
                self.version = 0
                self.deleted = False
                self.exists = True
            elif op == 'u':
                # Применяем событие обновления - меняем только переданные поля
                for field in ('title', 'content', 'work_name', 'student',
                              'variant_number', 'level_number', 'submission_date', 'grade'):
                    if field in note:
                        setattr(self, field, note[field])
                self.version += 1
            elif op == 'd':
                # Применяем событие удаления
                self.deleted = True
        return self
