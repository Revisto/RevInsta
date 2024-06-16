import pika
import pika.exceptions
from time import sleep

from logger.log import Logger

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
            },
            'logs': {
                'exchange': 'logs_exchange',
                'queue': 'logs_queue'
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

    def send_message(self, message, exchange, routing_key):
        for i in range(3):
            try:
                self.channel.basic_publish(exchange=exchange, routing_key=routing_key, body=message)
                break
            except pika.exceptions.StreamLostError:
                if i < 2:  # If this was not the last attempt, wait a bit before retrying
                    sleep(5)  # Wait for 5 seconds
                else:  # If this was the last attempt, re-raise the exception
                    Logger("RabbitMQService").log_error("Failed to send message to RabbitMQ")
                    raise pika.exceptions.StreamLostError("Failed to send message to RabbitMQ")

    def send_message_instagram_to_telegram(self, message):
        self.send_message(message, self.exchanges_queues['instagram_to_telegram']['exchange'], 'instagram_to_telegram')

    def send_message_telegram_to_instagram(self, message):
        self.send_message(message, self.exchanges_queues['telegram_to_instagram']['exchange'], 'telegram_to_instagram')

    def send_message_logs(self, message):
        self.send_message(message, self.exchanges_queues['logs']['exchange'], 'logs')

    def stop_consuming(self):
        self.channel.stop_consuming()

    def close_connection(self):
        self.connection.close()