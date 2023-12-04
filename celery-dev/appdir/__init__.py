
import json
import logging
import importlib
from pathlib import Path

import requests
from celery import Celery

from appdir.classes import *

from config import CeleryConfig
config = CeleryConfig()
app = Celery('celery')
app.config_from_object(config)


application_path = Path('/code/applications')
application_packages = [str(x)[6:].replace('/', '.')
                        for x in application_path.glob('*/*')
                        if x.is_dir() and not str(x.name).startswith("__")]
app.autodiscover_tasks(packages=application_packages, related_name='action', force=True)
application_catalogs = [x for x in application_path.glob('*/models.py') if x.is_file()]

webhooks_path = Path('/code/webhooks')
webhooks_packages = [str(x)[6:].replace('/', '.')
                     for x in webhooks_path.glob('*/*')
                     if x.is_dir() and not str(x.name).startswith("__")]

webhook_catalogs = [x for x in webhooks_path.glob('*/models.py') if x.is_file()]
for model_path in set().union(application_catalogs, webhook_catalogs):
    model_pythonic_path = str(model_path)[6:].replace('/', '.')[:-3]
    module = importlib.import_module(model_pythonic_path)
    # try:
    #     module.create_all_tables()
    # except:

app.autodiscover_tasks(packages=webhooks_packages, related_name='action', force=True)

webhook_tasks = []
application_tasks = []

for code in app.tasks.keys():
    if code.startswith("applications"):
        application_tasks.append(code)
        continue
    elif code.startswith("webhooks"):
        webhook_tasks.append(code)
        continue
register_tasks = requests.post(f"{app.conf.API_URL}/register_tasks",
                               data=json.dumps({"application_task_codes": application_tasks,
                                                "webhook_task_codes": webhook_tasks}),
                               headers=app.conf.api_headers,
                               timeout=120)
if register_tasks.status_code != 200 and register_tasks.json()['code'] != 0:
    raise SystemError('Celery not working!')


# signals
from celery.signals import task_postrun, task_prerun

def change_session_status(widget_session_guid: str,
                          state: str,
                          action_type: str,
                          headers: dict,
                          response: Response):

    data = {
        "widget_session_guid": widget_session_guid,
        "widget_session": response.widget_session.get_json(),
        "state": state,
        "action_type": action_type,
        "retval": {
            "status": response.status.value
            }
        }

    r = requests.post(f"{app.conf.API_URL}/change_session_status",
        data=json.dumps(data),
        headers=headers,
        timeout=5)
    if r.status_code != 200:
        logging.critical("API not working!")
    return None

def update_user_request(user_request_guid: str, state: str, headers: dict):
    data = {
        "user_request_guid": user_request_guid,
        "state": state
        }

    request = requests.post(f"{app.conf.API_URL}/update_user_request",
        data=json.dumps(data),
        headers=headers,
        timeout=5)

    if request.status_code != 200:
        logging.critical("API not working!")

    user_request = request.json()['data']

    return user_request

def update_webhook_request(webhook_request_guid: str, state: str, headers: dict):
    data = {
        "webhook_request_guid": webhook_request_guid,
        "state": state
        }

    request = requests.post(f"{app.conf.API_URL}/update_webhook_request",
        data=json.dumps(data),
        headers=headers,
        timeout=5)

    if request.status_code != 200:
        logging.critical("API not working!")

    webhook_request = request.json()['data']

    return webhook_request

@task_prerun.connect()
def task_prerun_handler(sender=None, task=None, *args, **kwargs):
    task_type = sender.name.split('.')[0]
    if task_type == 'applications':
        user_request = update_user_request(
            user_request_guid=kwargs['kwargs']['user_request_guid'],
            state="started",
            headers=app.conf.api_headers
            )
    elif task_type == 'webhooks':
        webhook_request = update_webhook_request(
            webhook_request_guid=kwargs['kwargs']['webhook_request_guid'],
            state="started",
            headers=app.conf.api_headers
        )

        kwargs['kwargs']['webhook_request'] = webhook_request

@task_postrun.connect()
def task_postrun_handler(sender=None, state=None, **kwargs):
    task_type, action_type = sender.name.split('.')[0], sender.name.split('.')[-1]
    if sender is not None and task_type == 'applications':
        response = kwargs['retval']
        if response is None or not isinstance(response, Response):
            raise TypeError("The return value of the task must be <Response>")

        change_session_status(
            widget_session_guid=kwargs['kwargs']['widget_session_guid'],
            state=state.lower(),
            action_type=action_type,
            response=response,
            headers=app.conf.api_headers
            )
        update_user_request(
            user_request_guid=kwargs['kwargs']['user_request_guid'],
            state=state.lower(),
            headers=app.conf.api_headers
        )
    elif task_type == 'webhooks':
        response = kwargs['retval']
        webhook_request = update_webhook_request(
            webhook_request_guid=kwargs['kwargs']['webhook_request_guid'],
            state="success",
            headers=app.conf.api_headers
        )
