# Event Sourcing - паттерн хранения изменений состояния как последовательности событий
# Вместо хранения текущего состояния в БД, сохраняем все события изменений в Kafka

from confluent_kafka import Consumer, Producer
import json
import sys

# Consumer читает события из Kafka для восстановления состояния (replay)
class NoteEventConsumer:
    @classmethod
    def load_events(cls, id):
        # Загружаем все события для конкретной сущности по ID
        events = []
        __c__ = Consumer({
            'bootstrap.servers': 'broker:9092',
            'group.id': 'mygroup',
            'auto.offset.reset': 'earliest',  # Читаем с начала топика
            'enable.auto.commit': False
        })
        __c__.subscribe(['operations'])
        while True:
            msg = __c__.poll(timeout=1.0)
            if msg is None:
                break
            if msg.error():
                print("Consumer error: {}".format(msg.error()), file=sys.stderr)
                break
            try:
                event = json.loads(msg.value().decode('utf-8'))
                print(f"Object: {repr(event)}", file=sys.stderr)
                # Фильтруем события по ID сущности
                if event['op'] == 'c':  # create
                    if event['note']['id'] == id:
                        events.append(event)
                elif event['op'] == 'u':  # update
                    if event['note']['id'] == id:
                        events.append(event)
                elif event['op'] == 'd':  # delete
                    if event['id'] == id:
                        events.append(event)
                else:
                    raise RuntimeError("Non correct object op")
                __c__.commit(msg)
            except Exception as e:
                print(str(e), file=sys.stderr)
        __c__.close()
        return events

# Producer публикует события в Kafka при любых изменениях
class NoteEventProducer:
    __p__ = Producer({
        'bootstrap.servers': 'broker:9092'
    })
    
    @classmethod
    def produce_event(cls, operation, object):
        # Публикуем событие: 'c' (create), 'u' (update), 'd' (delete)
        cls.__p__.produce('operations', json.dumps({
            'op': operation,
            'note': object
        }).encode('utf-8'))
        cls.__p__.flush()

# Event Sourcing класс - восстанавливает состояние из событий
class NoteEventSourcing:
    def __init__(self, id, title=None, content=None):
        self.__id__ = id
        self.__title__ = title
        self.__content__ = content
        self.__version__ = 0  # Версия для оптимистичной блокировки
        self.__deleted__ = False

    def load(self):
        # Replay: восстанавливаем текущее состояние из всех событий
        events = NoteEventConsumer.load_events(self.__id__)
        for event in events:
            if event['op'] == 'c':
                self.__title__ = event['note']['title']
                self.__content__ = event['note']['content']
                self.__version__ = 0
            elif event['op'] == 'u':
                self.__title__ = event['note']['title']
                self.__content__ = event['note']['content']
                self.__version__ = self.__version__ + 1
            elif event['op'] == 'd':
                self.__deleted__ = True

    def update(self, old_version, title, content):
        # Оптимистичная блокировка: обновляем только если версия совпадает
        if self.__version__ == old_version:
            self.__title__ = title
            self.__content__ = content
            self.__version__ += 1
