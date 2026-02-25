from confluent_kafka import Consumer

c = Consumer({
    'bootstrap.servers': 'broker',
    'group.id': 'mygroup',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': 'false'
})

c.subscribe(['operations'])
session = SessionLocal()

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
            database_note = Note(tittle=object.note.title,
                                content=object.note.content,
                        owner_id=object.user_id,
                        id=object.note.id)
            session.add(database_note)

            session.commit()
            pass
        elif object.op=='u':
            note = (session.query(Note)
            .filter(Note.id==object.note.id)
            .first())
            if not note:
                raise RuntimeError("Non correct id")
            note.title = object.note.title
            note.content = object.note.content 
            session.commit()
            pass
        elif object.op=='d':
            note = (session.query(Note)
            .filter(Note.id==object.note.id)
            .first())
            if not note:
                raise RuntimeError("Non correct id")
            session.delete(note)
            session.commit()
            pass
        else:
            raise RuntimeError("Non correct object op")
        
        c.commit(msg)

    except Exception as e:
        print(e)
        pass
c.close()