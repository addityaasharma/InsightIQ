from app import app as flask_app
from utils.celery.celery_app import celery, init_celery

init_celery(flask_app)
import utils.celery.celery_task