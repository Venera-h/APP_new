from confluent_kafka import Producer

p = Producer({'bootstrap.servers': 'broker'})

#ack - - когда нужно выходить из продюса. Ждем подтверждение, что операция завершена полностью 
def produce(data):
    p.produce('operations', json.dumps(data).encode('utf-8'),
              data.id.encode('utf-8'))


for data in some_data_source:
    # Trigger any available delivery report callbacks from previous produce() calls
    p.poll(0)

    # Asynchronously produce a message. The delivery report callback will
    # be triggered from the call to poll() above, or flush() below, when the
    # message has been successfully delivered or failed permanently.
    p.produce('mytopic', data.encode('utf-8'), callback=delivery_report)

# Wait for any outstanding messages to be delivered and delivery report
# callbacks to be triggered.
p.flush()