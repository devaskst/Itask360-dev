
import logging
from datetime import date
from enum import Enum

import requests
from requests.adapters import HTTPAdapter, Retry

from config import CeleryConfig
config = CeleryConfig()
API_TOKEN = config.API_TOKEN
API_URL = config.API_URL

class Status(Enum):
    NOTHING = 'nothing'
    STARTED = 'started'
    SUCCESS = 'success'

    BROKEN = 'broken'
    WARNING = 'warning'
    FAILURE = 'failure'
    REVOKED = 'revoked'

class Item:

    def __init__(self, **kwargs) -> None:
        self.value = kwargs['value']
        self.checked = kwargs['checked']
        self.style = kwargs['style']

    def __str__(self) -> str:
        return f'<{self.__class__.__name__}: {self.value}>'

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}: {self.__dict__}>'

    def get_json(self):
        return self.__dict__

class TreeItem(Item):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.expand = kwargs.get("expand", False)
        self.children = ([TreeItem(**kwd) for kwd in kwargs.get("children")] 
                         if isinstance(kwargs.get("children"), list) else [])

    def get_json(self):
        return {
            "value": self.value,
            "checked": self.checked,
            "style": self.style,
            "expand": self.expand,
            "children": [item.get_json() for item in self.children],
        }

class BaseControl:

    def __init__(self, **kwargs) -> None:
        self._guid = kwargs['guid']
        self._name = kwargs['name']
        self._code = kwargs['code']
        self._description = kwargs['description']
        self._describe = kwargs['describe'] if kwargs['describe'] is not None else {}
        self.alert = kwargs['alert']
        self.alert_style = kwargs['alert_style']
        self._order = kwargs['order']
        self._type = kwargs['type']
        self.hide = kwargs['hide']
        self.disabled = kwargs['disabled']
        self.style = kwargs['style']

    @property
    def guid(self):
        return self._guid

    @property
    def name(self):
        return self._name

    @property
    def code(self):
        return self._code

    @property
    def order(self):
        return self._order

    @property
    def description(self):
        return self._description

    def __str__(self) -> str:
        return f'<{self.__class__.__name__}: {self.name}>'

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}: {self.__dict__}>'

    def get_json(self):
        return {
                "guid": self._guid,
                "name": self._name,
                "code": self._code,
                "description": self._description,
                "describe": self._describe,
                "alert": self.alert,
                "alert_style": self.alert_style,
                "order": self._order,
                "hide": self.hide,
                "disabled": self.disabled,
                "type": self._type,
                "style": self.style
            }

class TextBox(BaseControl):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.value = kwargs['value']
        self.default_value = kwargs['default_value']

    def get_json(self):
        upper_json = super().get_json()
        return upper_json | {
            "value": self.value,
            "default_value": self.default_value
        }

# TODO проверка на datetime тип и преобразование в нормализованный вид
# TODO протестить на рабочей
class Calendar(BaseControl):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.value = date.fromisoformat(kwargs['value']) if isinstance(kwargs['value'], str) else None
        self.default_value = kwargs['default_value']

    def get_json(self):
        upper_json = super().get_json()
        return upper_json | {
            "value": self.value.isoformat(),
            "default_value": self.default_value
        }

class CheckBoxList(BaseControl):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.value = kwargs['value']
        self.default_value = kwargs['default_value']
        self.items = [Item(**item) for item in kwargs.get('items', [])]
        self._show_filter = self._describe.get("show_filter", False)

    @property
    def show_filter(self):
        return self._show_filter

    @show_filter.setter
    def show_filter(self, value: bool):
        self._show_filter = value
        self._describe['show_filter'] = value

    def get_json(self):
        upper_json = super().get_json()
        return upper_json | {
            "value": self.value,
            "default_value": self.default_value,
            "items": [item.get_json() for item in self.items]
        }

class DropDownList(BaseControl):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.value = kwargs['value']
        self.default_value = kwargs['default_value']
        self.items = [Item(**item) for item in kwargs.get('items', [])]
        self._show_filter = self._describe.get("show_filter", False)

    @property
    def show_filter(self):
        return self._show_filter

    @show_filter.setter
    def show_filter(self, value: bool):
        self._show_filter = value
        self._describe['show_filter'] = value

    def get_json(self):
        upper_json = super().get_json()
        return upper_json | {
            "value": self.value,
            "default_value": self.default_value,
            "items": [item.get_json() for item in self.items]
        }

class Button(BaseControl):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

class GroupList(BaseControl):
    # TODO переделать структуру контролла и описать стрктуру describe
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.items = [Item(**item) for item in kwargs.get('items', [])]
        self._show_filter = self._describe.get("show_filter", False)

    @property
    def show_filter(self):
        return self._show_filter

    @show_filter.setter
    def show_filter(self, value: bool):
        self._show_filter = value
        self._describe['show_filter'] = value

    def get_json(self):
        upper_json = super().get_json()
        return upper_json | {
            "items": [item.get_json() for item in self.items]
        }

class TreeView(BaseControl):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.items = [TreeItem(**item) for item in kwargs.get('items', [])]

    def get_json(self):
        upper_json = super().get_json()
        return upper_json | {
            "items": [item.get_json() for item in self.items]
        }

class DataView(BaseControl):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._columns = self._describe.get("columns", [])
        self._rows = self._describe.get("rows", [])
        # FIXME поменять логику страниц у контролла !!!
        self._pages = []

    @property
    def columns(self):
        return self._columns

    @columns.setter
    def columns(self, value: list):
        self._columns = value
        self._describe['columns'] = value

    @property
    def rows(self):
        return self._rows

    @rows.setter
    def rows(self, value: list):
        self._rows = value
        self._describe['rows'] = value

    @property
    def pages(self):
        return self._pages

    @rows.setter
    def pages(self, value: list):
        self._pages = value
        self._describe['pages'] = value

    def get_json(self):
        # TODO: дописать логику get_json()
        upper_json = super().get_json()
        return upper_json

class FileDownload(BaseControl):
    # TODO: дописать логику
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.file_id = kwargs['url']

_control_types = {
    "text_box": TextBox,
    "calendar": Calendar,
    "check_box_list": CheckBoxList,
    "drop_down_list": DropDownList,
    "button": Button,
    "group_list": GroupList,
    "tree_view": TreeView,
    "data_view": DataView,
    "file_download": FileDownload
}

class StepSession:

    def __init__(self, guid: str, name: str,
                 order: int, description: str,
                 controls=None) -> None:
        self._guid = guid
        self._name = name
        self._order = order
        self._description = description
        self._controls = [_control_types[control['type']](**control)
                          for control in controls] if controls is not None else []

    @property
    def guid(self):
        return self._guid

    @property
    def order(self):
        return self._order

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description

    @property
    def controls(self):
        return self._controls

    def __str__(self) -> str:
        return f'<StepSession: {self.name}>'

    def __repr__(self) -> str:
        return f'<StepSession: {self.name}>'

    # def get_json(self):
    #     return json.dumps(self.__dict__)

    def get_json(self):
        return {
                "guid": self._guid,
                "name": self._name,
                "order": self._order,
                "description": self._description,
                "controls": {control.guid: control.get_json() for control in self.controls}
        }

class WidgetSession:

    def __init__(self, guid: str) -> None:
        self._guid = guid
        self.get_widget_session()

    def get_widget_session(self):
        s = requests.Session()
        retry_strategy = Retry(
            total=5,
            backoff_factor=0.1,
            status_forcelist=[500,502,503,504]
            )
        s.mount(f'{API_URL}', HTTPAdapter(max_retries=retry_strategy))
        request = s.post(
            url=f"{API_URL}/celery/get_widget_session",
            json={"guid": self.guid},
            headers={"Authorization": f"Bearer {API_TOKEN}"},
            timeout=1
        )

        if request.status_code != requests.codes.ok:
            # TODO обсудить логгирование критических ошибок
            logging.critical("API not working!")
            raise SystemError('API not working!')

        data = request.json()

        if data['code'] != 0:
            raise ValueError(data['msg'])

        widget_session_data = data['data']["widget"]
        steps_data = data['data']['steps']

        self.current_step = widget_session_data['current_step']
        self.next_step = widget_session_data['next_step']
        self._count_steps = widget_session_data['count_steps']
        self._code = widget_session_data['code']
        self._name = widget_session_data['name']
        self._status = widget_session_data['status']
        self._description = widget_session_data['description']
        self._async_execute = widget_session_data['async_execute']
        self._steps = [StepSession(
            guid=step['guid'],
            name=step['name'],
            order=step['order'],
            description=step['description'],
            controls=step['controls']
        ) for step in steps_data]

    @property
    def guid(self):
        return self._guid

    @property
    def count_steps(self):
        return self._count_steps

    @property
    def code(self):
        return self._code

    @property
    def name(self):
        return self._name

    @property
    def status(self):
        return self._status

    @property
    def description(self):
        return self._description

    @property
    def async_execute(self):
        return self._async_execute

    @property
    def steps(self):
        return self._steps

    def __str__(self):
        return f'<WidgetSession: {self.code}>'

    def get_dict(self):
        return self.__dict__

    def get_json(self):
        return {
            "widget": {
                "guid": self._guid,
                "current_step": self.current_step,
                "next_step": self.next_step,
                "count_steps": self._count_steps,
                "code": self._code,
                "name": self._name,
                "status": self._status,
                "description": self._description,
                "async_execute": self._async_execute
            },
            "steps": {step.guid: step.get_json() for step in self._steps}
        }

class Response:

    def __init__(self,
                 widget_session: WidgetSession,
                 next_step = 1,
                 status: str = Status.NOTHING) -> None:
        self.widget_session = widget_session
        self.next_step = next_step
        self.status = status

class Webhook:

    def __init__(self, **kwargs) -> None:
        self.guid = kwargs['guid']
        self.requestId = kwargs['requestId']
        self.app_guid = kwargs.get('app_guid', None)
        self.account_guid = kwargs['account_guid']
        self.status = kwargs['status']
        self.status_description = kwargs.get('status_description', None)
        self.data = kwargs['data']

    def __str__(self) -> str:
        return f'<Webhook: {self.requestId}>'

    def __repr__(self) -> str:
        return f'<Webhook: {self.requestId}>'
