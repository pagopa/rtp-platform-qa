import os
import ssl

import certifi
from aiokafka import AIOKafkaProducer
from keyvault import get_eventhub_connection_string

async def setup_producer():
    connection_string = get_eventhub_connection_string()
    namespace = os.environ['EVENTHUB_NAMESPACE']

    ssl_context = ssl.create_default_context(cafile=certifi.where())
    ssl_context.check_hostname = True
    ssl_context.verify_mode = ssl.CERT_REQUIRED

    producer = AIOKafkaProducer(
        bootstrap_servers=f"{namespace}.servicebus.windows.net:9093",
        security_protocol='SASL_SSL',
        sasl_mechanism='PLAIN',
        sasl_plain_username='$ConnectionString',
        sasl_plain_password=connection_string,
        ssl_context=ssl_context,
        client_id='python-producer'
    )
    await producer.start()
    return producer
