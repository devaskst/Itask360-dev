import logging
import sys
from os import getenv, path
from dotenv import load_dotenv
from kombu import Queue

dotenv_path = path.join('.env')
if path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    logging.error("Файл .env не найден.")
    sys.exit()

class CeleryConfig:
    REDIS_PASSWORD = getenv("REDIS_PASSWORD_DEV", default='secret')
    REDIS_HOST = getenv("REDIS_HOST_DEV", default='')
    REDIS_USER = getenv("REDIS_USER_DEV", default='')
    REDIS_PORT = getenv("REDIS_PORT_DEV", default='')

    API_TOKEN = getenv("CELERY_API_TOKEN", default='super-secret')
    API_URL = getenv("API_URL", default='http://127.0.0.1/api')
    APPLICATION_GUID = getenv("APPLICATION_GUID", default='')

    result_expires=3600
    broker_connection_retry_on_startup = True
    task_ignore_result = True
    task_store_errors_even_if_ignored = True

    task_queues = (
        Queue('default',    routing_key='default'),
        Queue(f"webhook/{APPLICATION_GUID}"),
        Queue(f"application/{APPLICATION_GUID}")
    )

    task_default_queue = 'default'
    task_default_exchange = task_default_queue
    task_default_exchange_type = 'direct'
    task_default_routing_key = task_default_queue

    @property
    def broker_url(self):
        return f'redis://{self.REDIS_USER}:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0'

    @property
    def result_backend(self):
        return f'redis://{self.REDIS_USER}:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/1'

    @property
    def api_headers(self):
        return {
            "Authorization": f"Bearer {self.API_TOKEN}",
            "Content-Type": "application/json"
        }

ENABLE_EXAMPLE_DATA = True
