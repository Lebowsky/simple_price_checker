import json
from typing import Callable, Union, Literal, List, Dict
from functools import wraps

from java import jclass


noClass = jclass("ru.travelfood.simple_ui.NoSQL")
rs_settings = noClass("rs_settings")


class HashMap:
    def __init__(self, hash_map=None):
        self.hash_map = hash_map

    def finish_process(self):
        self.hash_map.put('FinishProcess', '')

    def toast(self, text):
        self.hash_map.put('toast', str(text))

    def refresh_screen(self):
        self.hash_map.put('RefreshScreen', '')

    def beep(self, tone=''):
        self.hash_map.put('beep', str(tone))

    def playsound(self, event: str, sound_val: str = ''):
        if not sound_val:
            sound = rs_settings.get(f'{event}_signal')
        else:
            sound = sound_val
        self.hash_map.put(f'playsound_{sound}', "")

    def get(self, item, from_json=False):
        if from_json:
            return json.loads(self.hash_map.get(item)) if self.hash_map.get(item) else None
        else:
            return self.hash_map.get(item)

    def put(self, key, value: Union[str, List, Dict, bool] = '', to_json=False):
        if to_json:
            self.hash_map.put(key, json.dumps(value))
        else:
            if isinstance(value, bool):
                value = str(value).lower()
            self.hash_map.put(key, str(value))

    def containsKey(self, key):
        return self.hash_map.containsKey(key)

    def remove(self, key):
        self.hash_map.remove(key)

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

    def set_vision_settings(
            self,
            min_length: int = 2,
            max_length: int = 6,
            ReplaceO: bool = False,
            ToUpcase: bool = False,
            OnlyNumbers: bool = True
    ):
        """min_length - Минимальная длина текста
           max_length - Максимальная длина текста
           ReplaceO - Заменить буквы О на 0 (нули)
           ToUpcase - Преобразование в верхний регистр
           OnlyNumbers - Распознавание чисел
        """
        settings = {
            "min_length": min_length,
            "max_length": max_length,
            "ReplaceO": ReplaceO,
            "ToUpcase": ToUpcase,
            "OnlyNumbers": OnlyNumbers
        }
        self.hash_map.put("SetVisionSettings", json.dumps(settings))


class HashMapDecorator(HashMap):
    """
    Класс-декоратор для удобной работы с hashMap.
    Также можно добавить дополнительную логику.
    """

    def __call__(self, func: Callable[..., None]):
        @wraps(func)
        def wrapper(hashMap, *args, **kwargs):
            self.init(hashMap)
            func(self)
            return hashMap

        return wrapper

    def init(self, hashMap):
        self.hash_map = hashMap