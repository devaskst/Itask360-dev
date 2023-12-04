
import os
from celery import shared_task

from appdir.classes import WidgetSession, Response, Status, Item

@shared_task
def init(**kwargs):
    import random
    ws = WidgetSession(guid=kwargs['widget_session_guid'])
    # sale_id = 7
    current_step = ws.get_current_step()
    if current_step.code == 'main-step':
        check_box_list = current_step.get_control(code='order-products')
        items = []
        for i in range(10):
            count = str(random.randint(1, 10))
            price = random.randint(1, 1000)
            items.append(Item(value=f'Товар {i+1}',
                            checked=True,
                            style='primary',
                            description="здесь будет описание",
                            describe={
                                # "a_name": "Кол-во",
                                "count": count,
                                "uom": "шт."
                                }
                            )
                        )
        check_box_list.items = items
    return Response(ws, status=Status.SUCCESS)

@shared_task
def validate(**kwargs):
    ws = WidgetSession(guid=kwargs['widget_session_guid'])
    return Response(ws, status=Status.SUCCESS)

@shared_task
def execute(**kwargs):
    ws = WidgetSession(guid=kwargs['widget_session_guid'])
    return Response(ws, status=Status.SUCCESS)
