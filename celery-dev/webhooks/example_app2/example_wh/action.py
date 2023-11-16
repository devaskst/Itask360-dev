
from celery import shared_task
from appdir.classes import Webhook

@shared_task
def webhook_handler_test(**kwargs):

    webhook_request = Webhook(**kwargs['webhook_request'])
    data = kwargs['webhook_request']
    print("======================")
    print(webhook_request.data)
    return data
