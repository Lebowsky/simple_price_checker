import json
import os.path

from java import jclass

from ru.travelfood.simple_ui import SimpleUtilites as suClass

import ui_models
from ui_utils import HashMap, HashMapDecorator
from price_checker import PriceChecker
noClass = jclass("ru.travelfood.simple_ui.NoSQL")
rs_settings = noClass("rs_settings")
prices_ncl = noClass("prices_ncl")
detected_ncl = noClass("detected_ncl")
finded_objects_temp_counter = {}


@HashMapDecorator()
def app_before_on_start(hash_map: HashMap):
    """
    Обработчик при старте приложения запускается перед app_on_start
    нужнен для определения версии конфигурации в последующем
    """
    model = ui_models.MainEvents(hash_map, rs_settings)
    model.app_before_on_start()


@HashMapDecorator()
def app_on_start(hash_map: HashMap):
    """ Обработчик при старте приложения """

    model = ui_models.MainEvents(hash_map, rs_settings)
    model.app_on_start()


@HashMapDecorator()
def sync_on_start(hash_map: HashMap): # Экран: Синхронизация  Обр ПриЗапуске
    if hash_map.containsKey("prices"):
        prices = json.loads(hash_map.get("prices"))
        hash_map.put("_prices", hash_map.get("prices"))
        hash_map.put("count_goods_file", str(len(prices)))
    else:
        hash_map.put("count_goods_file", "suip-файл не открыт")

    if hash_map.containsKey("_prices"):
        prices = json.loads(hash_map.get("_prices"))
        hash_map.put("count_goods_device", str(len(prices)))
    else:
        hash_map.put("count_goods_device", "нет товаров")

    confirmed = json.loads(prices_ncl.findJSON("confirmed", True))
    hash_map.put("count_detected", str(len(confirmed)))
    declined = json.loads(prices_ncl.findJSON("confirmed", False))
    hash_map.put("count_declined", str(len(declined)))
    count_all_nosql = len(json.loads(prices_ncl.getallkeys()))
    hash_map.put("count_all_nosql", str(count_all_nosql))


@HashMapDecorator()
def save_to_device(hash_map: HashMap):
    if hash_map.containsKey("prices"):
        prices_str = hash_map.get("_prices")
        ncl = noClass("pricechecker_kit")
        ncl.put("prices", prices_str, True)

        prices_ncl.destroy()
        prices = json.loads(prices_str)
        for item in prices:
            prices_ncl.put(
                item['barcode'],
                json.dumps({
                    'price': item['price'],
                    'name': item['name'],
                    'barcode': item['barcode']}, ensure_ascii=False)
                , True
            )

        hash_map.put("toast", "Сохранение завершено")


@HashMapDecorator()
def save_to_suip(hash_map: HashMap):
    ncl = noClass("pricechecker_kit")
    prices_str = ncl.get("prices")
    hash_map.put("NoProcessSUIP", '')
    hash_map.put("NoPyHandlersSUIP", '')
    detected = hash_map.get("_detected", from_json=True) or []
    confirmed = hash_map.get("_confirmed", from_json=True) or []
    prices = json.loads(prices_str)

    conf = json.loads(prices_ncl.findJSON("confirmed", True))

    for elem in conf:
        for price in prices:
            if price['barcode'] == elem['key']:
                confirmed.append(price)
    decl = json.loads(prices_ncl.findJSON("confirmed", True))
    for elem in decl:
        for price in prices:
            if price['barcode'] == elem['key']:
                detected.append(price)
    _data = {
        "prices" : prices,
        "confirmed": confirmed,
        "detected": detected + confirmed
    }
    hash_map.put("_data", json.dumps(_data))
    hash_map.toast('Успешно')


@HashMapDecorator()
def sync_on_input(hash_map: HashMap):
    listener = hash_map.get('listener')
    if listener == 'btn_refresh_db':
        ncl = noClass("pricechecker_kit")
        prices_ncl.destroy()
        detected_ncl.destroy()
        prices = ncl.get('prices')
        if not prices:
            hash_map.toast('Список товаров prices пуст.')
            return
        for item in json.loads(prices):
            data = {
                'price': item['price'],
                'name': item['name'],
                'barcode': item['barcode']
            }
            prices_ncl.put(item['barcode'], json.dumps(data, ensure_ascii=False), True)
        hash_map.toast('Данные обновлены')

    elif listener == 'btn_save_to_json':
        directory = suClass.get_temp_dir()
        path = os.path.join(directory, 'saved_json.json')
        prices = []
        confirmed = []
        declined = []
        detected = []
        with open(path, 'w') as f:
            for key in json.loads(prices_ncl.getallkeys()):
                item = json.loads(prices_ncl.get(key))
                prices.append(item)
                if 'confirmed' in item:
                    detected.append(item)
                    if item['confirmed'] is True:
                        confirmed.append(item)
                    else:
                        declined.append(item)

            _data = {
                "prices": prices,
                "confirmed": confirmed,
                "declined": declined,
                "detected": detected,
            }
            json.dump(_data, f, indent=4, ensure_ascii=False)
        file_data = {'path': path, "default": 'saved_json.json'}
        hash_map.put('SaveExternalFile', json.dumps(file_data))

    elif listener == 'FileSave':
        hash_map.toast('Файл сохранен в Загрузки')


@HashMapDecorator()
def scan_settings_on_start(hash_map: HashMap):
    screen = ui_models.SettingsScreen(hash_map, rs_settings)
    screen.on_start()


@HashMapDecorator()
def scan_settings_on_input(hash_map: HashMap):
    screen = ui_models.SettingsScreen(hash_map, rs_settings)
    screen.on_input()


@HashMapDecorator()
def price_scan_on_start(hash_map: HashMap):
    PriceChecker(hash_map).price_scan_on_start()


@HashMapDecorator()
def price_scan_on_input(hash_map: HashMap):
    PriceChecker(hash_map).price_scan_on_input()


def on_obj_detected(hashMap, _files=None, _data=None):
    global finded_objects_temp_counter
    current_object = hashMap.get("current_object")
    if current_object not in finded_objects_temp_counter:
        finded_objects_temp_counter[current_object] = 1
    elif finded_objects_temp_counter[current_object] < rs_settings.get('objects_find_limit'):
        finded_objects_temp_counter[current_object] += 1
    else:
        return
    PriceChecker(hashmap=HashMap(hashMap)).handle_value()
    return hashMap
