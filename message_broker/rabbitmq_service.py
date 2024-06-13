import pika

class RabbitMQService:
    def __init__(self, config):
        self.rabbitmq_username = config.RABBITMQ_USERNAME
        self.rabbitmq_password = config.RABBITMQ_PASSWORD
        self.rabbitmq_host = config.RABBITMQ_HOST
        self.rabbitmq_port = config.RABBITMQ_PORT

        # Connect to RabbitMQ
        credentials = pika.PlainCredentials(self.rabbitmq_username, self.rabbitmq_password)
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.rabbitmq_host, port=self.rabbitmq_port, credentials=credentials))
        self.channel = self.connection.channel()

        # Declare the exchanges and queues
        self.exchanges_queues = {
            'instagram_to_telegram': {
                'exchange': 'instagram_to_telegram_exchange',
                'queue': 'instagram_to_telegram_queue'
            },
            'telegram_to_instagram': {
                'exchange': 'telegram_to_instagram_exchange',
                'queue': 'telegram_to_instagram_queue'
            }
        }

        for key, value in self.exchanges_queues.items():
            self.channel.exchange_declare(exchange=value['exchange'], exchange_type='direct')
            self.channel.queue_declare(queue=value['queue'])
            self.channel.queue_bind(exchange=value['exchange'], queue=value['queue'], routing_key=key)

    def start_consuming(self, callbacks):
        for key, value in self.exchanges_queues.items():
            if key in callbacks:
                self.channel.basic_consume(queue=value['queue'], on_message_callback=callbacks[key], auto_ack=True)
        self.channel.start_consuming()

    def send_message_instagram_to_telegram(self, message):
        self.channel.basic_publish(exchange=self.exchanges_queues['instagram_to_telegram']['exchange'], routing_key='instagram_to_telegram', body=message)

    def send_message_telegram_to_instagram(self, message):
        self.channel.basic_publish(exchange=self.exchanges_queues['telegram_to_instagram']['exchange'], routing_key='telegram_to_instagram', body=message)

    def stop_consuming(self):
        self.channel.stop_consuming()

    def close_connection(self):
        self.connection.close()