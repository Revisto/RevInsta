import sys
from loguru import logger

from utils.singleton import Singleton

class Logger(metaclass=Singleton):
    def __init__(self, service):
        # Configure the logger
        logger.add(sys.stderr, format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {extra[service]} - {message}", level="INFO")
        logger.add("log.txt", format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {extra[service]} - {message}", level="INFO")
        self.logger = logger.bind(service=service)

    def log_debug(self, message):
        self.logger.debug(message)

    def log_info(self, message):
        self.logger.info(message)

    def log_warning(self, message):
        self.logger.warning(message)

    def log_error(self, message):
        self.logger.error(message)

    def log_critical(self, message):
        self.logger.critical(message)