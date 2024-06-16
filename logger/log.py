import sys
from loguru import logger

from utils.singleton import Singleton
from message_broker.rabbitmq_service import RabbitMQService
from config.config import Config

class Logger(metaclass=Singleton):
    def __init__(self, service):
        self.service = service
        # Configure the logger
        logger.add(sys.stderr, format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {extra[service]} - {message}", level="INFO")
        logger.add("log.txt", format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {extra[service]} - {message}", level="INFO")
        self.logger = logger.bind(service=service)

    def log_and_send(self, level, message):
        # Log the message
        getattr(self.logger, level)(message)

        # Send the log message to RabbitMQ
        self.rabbitmq_service = RabbitMQService(Config)
        self.rabbitmq_service.send_message_logs(f"{self.service} - {level.upper()} - {message}")
        self.rabbitmq_service.close_connection()

    def log_debug(self, message):
        self.log_and_send('debug', message)

    def log_info(self, message):
        self.log_and_send('info', message)

    def log_warning(self, message):
        self.log_and_send('warning', message)

    def log_error(self, message):
        self.log_and_send('error', message)

    def log_critical(self, message):
        self.log_and_send('critical', message)