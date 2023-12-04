
import os
from celery import shared_task

from appdir.classes import WidgetSession, Response, Status

@shared_task
def init(**kwargs):
    ws = WidgetSession(guid=kwargs['widget_session_guid'])
    return Response(ws, next_step=2, status=Status.SUCCESS)

@shared_task
def validate(**kwargs):
    ws = WidgetSession(guid=kwargs['widget_session_guid'])
    next_step = ws.current_step + 1
    return Response(ws, next_step=next_step, status=Status.SUCCESS)

@shared_task
def execute(**kwargs):
    ws = WidgetSession(guid=kwargs['widget_session_guid'])
    return Response(ws, next_step=1, status=Status.SUCCESS)