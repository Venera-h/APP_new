from confluent_kafka import Consumer

c = Consumer({
    'bootstrap.servers': 'broker',
    'group.id': 'log',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': 'false'
})

c.subscribe(['operations'])
session = SessionLocal()


file = open('./log/log.txt', 'w+')


while True:
    msg = c.poll(1.0)

    if msg is None:
        continue
    if msg.error():
        print("Consumer error: {}".format(msg.error()))
        continue
    try:

        object = json.load(msg.value().decode('utf-8'))
        if object.op=='c':
            file.write(f"Note create with id={object.note.id}, title={
            object.note.title}, content={object.note.content}")
            
        elif object.op=='u':
           file.write(f"Note update with id={object.note.id}, title={
            object.note.title}, content={object.note.content}")

        elif object.op=='d':
            file.write(f"Note delete with id={object.note.id}, title={
            object.note.title}, content={object.note.content}")
        else:
            raise RuntimeError("Non correct object op")
        
        c.commit(msg)

    except Exception as e:
        print(e)
        pass
c.close()