from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv(override=True)

REDIS_URL = "redis://default:yEzs5PcNSpiYOV7qBmyp4xAfatL8mvZ8@redis-17174.c89.us-east-1-3.ec2.cloud.redislabs.com:17174"

celery = Celery(
    __name__,
    broker=REDIS_URL,
    backend=None,
)

celery.conf.update(
    task_ignore_result=True,
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=5,
    broker_pool_limit=None,
)

def init_celery(app):
    # ← removed celery.conf.update(app.config)

    class ContextTask(celery.Task):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return super().__call__(*args, **kwargs)

    celery.Task = ContextTask
    return celery