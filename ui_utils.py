import json
from typing import Callable, Union, Literal, List, Dict
from functools import wraps

from java import jclass


noClass = jclass("ru.travelfood.simple_ui.NoSQL")
rs_settings = noClass("rs_settings")


# Класс-декоратор для удобной работы с hashMap. Также можно добавить дополнительную логику.
class HashMap:
    """
        Класс-декоратор для удобной работы с hashMap. Также можно добавить дополнительную логику.
    """

    def __init__(self, hash_map=None, debug: bool = False):
        self.hash_map = hash_map
        self.debug_mode = debug

    def __call__(self, func: Callable[..., None]):
        @wraps(func)
        def wrapper(hashMap, *args, **kwargs):
            self.init(hashMap)
            func(self)
            return hashMap

        return wrapper

    def init(self, hashMap):
        self.hash_map = hashMap

    def finish_process(self):
        self.hash_map.put('FinishProcess', '')

    def finish_process_result(self):
        self.hash_map.put('FinishProcessResult', '')

    def show_process_result(self, process, screen):
        if process and screen:
            self.hash_map.put('ShowProcessResult', f'{process}|{screen}')

    def set_result_listener(self, listener):
        if listener and isinstance(listener, str):
            self.hash_map.put('SetResultListener', listener)

    def toast(self, text, add_to_log=False):
        self.hash_map.put('toast', str(text))
        if add_to_log:
            self.error_log(text)

    def notification(self, text, title=None, add_to_log=False):
        notification_id = rs_settings.get("notification_id") + 1 if rs_settings.get("notification_id") else 1
        if title is None:
            title = self.get_current_screen()

        self.hash_map.put(
            "basic_notification",
            json.dumps([{'number': notification_id, 'title': str(title), 'message': text}])
        )

        rs_settings.put("notification_id", notification_id, True)
        if add_to_log:
            self.error_log(text)

    def debug(self, text):
        if self.debug_mode:
            self.toast(text, add_to_log=True)

    def refresh_screen(self):
        self.hash_map.put('RefreshScreen', '')

    def run_event(self, method_name):
        self['RunEvent'] = json.dumps(self._get_event(method_name))

    def run_event_async(self, method_name, post_execute_method=None):
        run_event = self._get_event(method_name, 'runasync')
        if post_execute_method:
            run_event[0]['postExecute'] = json.dumps(self._get_event(post_execute_method))
        self['RunEvent'] = json.dumps(run_event)

    def run_event_progress(self, method_name):
        self['RunEvent'] = json.dumps(self._get_event(method_name, 'runprogress'))

    def beep(self, tone=''):
        self.hash_map.put('beep', str(tone))

    def playsound(self, event: str, sound_val: str = ''):
        if not sound_val:
            sound = rs_settings.get(f'{event}_signal')
        else:
            sound = sound_val
        self.hash_map.put(f'playsound_{sound}', "")

    def _get_event(self, method_name, action=None):
        """
        :param method_name: handlers name
        :param action: run|runasync|runprogress

        :return: event dict
        """

        evt = [{
            'action': action if action else 'run',
            'type': 'python',
            'method': method_name,
        }]

        return evt

    def error_log(self, err_data):
        try:
            err_data = json.dumps(err_data, ensure_ascii=False, indent=2)
        except:
            err_data = str(err_data)

        rs_settings.put('error_log', err_data, True)

    def __getitem__(self, item):
        return self.get(item, False)

    def __setitem__(self, key, value):
        self.put(key, value, False)

    def get(self, item, from_json=False):
        if from_json:
            return json.loads(self.hash_map.get(item)) if self.hash_map.get(item) else None
        else:
            return self.hash_map.get(item)

    def get_json(self, item):
        return json.loads(self.hash_map.get(item)) if self.hash_map.get(item) else None

    def get_bool(self, item):
        value = str(self.hash_map.get(item)).lower() not in ('0', 'false', 'none')
        return value

    def put(self, key, value: Union[str, List, Dict, bool] = '', to_json=False):
        if to_json:
            self.hash_map.put(key, json.dumps(value))
        else:
            if isinstance(value, bool):
                value = str(value).lower()
            self.hash_map.put(key, str(value))

    def put_data(self, data: dict):
        for key, value in data.items():
            self[key] = value

    def containsKey(self, key):
        return self.hash_map.containsKey(key)

    def remove(self, key):
        self.hash_map.remove(key)

    def delete(self, key):
        self.hash_map.remove(key)

    def export(self) -> list:
        return self.hash_map.export()

    def to_json(self):
        return json.dumps(self.export(), indent=4, ensure_ascii=False).encode('utf8').decode()

    def add_to_cv_list(
            self,
            element: Union[str, dict],
            cv_list: Literal['green_list', 'yellow_list', 'red_list', 'gray_list',
                             'blue_list', 'hidden_list', 'object_info_list',
                             'stop_listener_list', 'object_caption_list',
                             'object_detector_mode'],
            _dict: bool = False
    ) -> None:
        """ Добавляет в cv-список элемент, или создает новый список с этим элементом.
            object_info_list - Информация об объекте (снизу). [{'object': object_id: str, 'info': value}]
            object_detector_mode - Режим детектора. [{'object_id': object_id: int, 'mode': barcode|ocr|stop}]
            object_caption_list - Информация об объекте (сверху). [{'object': object_id: str, 'caption': value}]
            stop_listener_list - Блокирует выполние обработчиков для объектов в списке
        """

        if _dict:
            lst = self.get(cv_list, from_json=True) or []
            if element not in lst:
                lst.append(element)
                self.put(cv_list, json.dumps(lst, ensure_ascii=False))

        else:
            lst = self.get(cv_list)
            lst = lst.split(';') if lst else []
            if element not in lst:
                lst.append(element)
                self.put(cv_list, ';'.join(lst))

    def remove_from_cv_list(
        self,
        element: Union[str, dict],
        cv_list: Literal['green_list', 'yellow_list', 'red_list', 'gray_list',
                         'blue_list', 'hidden_list', 'object_info_list',
                         'stop_listener_list', 'object_caption_list',
                         'object_detector_mode'],
        _dict: bool = False
    ):
        """Удаляет из cv-списка"""
        if _dict:
            lst = self.get(cv_list, from_json=True) or []
            try:
                lst.remove(element)
                self.put(cv_list, json.dumps(lst, ensure_ascii=False))
            except ValueError:
                pass
        else:
            lst = self.get(cv_list)
            lst = lst.split(';') if lst else []
            if element in lst:
                lst.remove(element)
                self.put(cv_list, ';'.join(lst))

    def show_screen(self, name, data=None):
        self.put('ShowScreen', name)
        if data:
            self.put_data(data)

    def show_dialog(self, listener, title='', buttons=None):
        self.put("ShowDialog", listener)

        if title or buttons:
            dialog_style = {
                'title': title or listener,
                'yes': 'Ок',
                'no': 'Отмена'
            }
            if buttons and len(buttons) > 1:
                dialog_style['yes'] = buttons[0]
                dialog_style['no'] = buttons[1]

            self.put('ShowDialogStyle', dialog_style)

    def get_current_screen(self):

        return self['current_screen_name'] if self.containsKey('current_screen_name') else ''

    def get_current_process(self):
        return self['current_process_name']

    def set_title(self, title):
        self['SetTitle'] = title

    def run_py_thread_progress(self, handlers_name: str):
        """
        Запускает асинхронное фоновое выполнение скрипта c блокирующим прогресс-баром, который блокирует UI-поток.
        В качестве аргумента - имя функции-хендлера.
        """

        self['RunPyThreadProgressDef'] = handlers_name

    def sql_exec(self, query, params=''):
        self._put_sql('SQLExec', query, params)

    def sql_exec_many(self, query, params=None):
        params = params or []
        self._put_sql('SQLExecMany', query, params)

    def sql_query(self, query, params=''):
        self._put_sql('SQLQuery', query, params)

    def _put_sql(self, sql_type, query, params):
        self.put(
            sql_type,
            {"query": query, 'params': params},
            to_json=True
        )