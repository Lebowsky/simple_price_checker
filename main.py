import json
import os.path

from java import jclass

from ru.travelfood.simple_ui import SimpleUtilites as suClass

import ui_models
from ui_utils import HashMap

noClass = jclass("ru.travelfood.simple_ui.NoSQL")
rs_settings = noClass("rs_settings")
prices_ncl = noClass("prices_ncl")
yellow_list_ncl = noClass("yellow_list_ncl")
price_valid_ncl = noClass("price_valid_ncl")
price_invalid_ncl = noClass("price_invalid_ncl")
counter_ncl = noClass("counter_ncl")
detected_ncl = noClass("detected_ncl")

PRICE_MIN_LEN = 2
PRICE_MAX_LEN = 6


@HashMap()
def app_before_on_start(hash_map: HashMap):
    """
    Обработчик при старте приложения запускается перед app_on_start
    нужнен для определения версии конфигурации в последующем
    """

    model = ui_models.MainEvents(hash_map, rs_settings)
    model.app_before_on_start()

@HashMap()
def app_on_start(hash_map: HashMap):
    """ Обработчик при старте приложения """

    model = ui_models.MainEvents(hash_map, rs_settings)
    model.app_on_start()

@HashMap()
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

@HashMap()
def sync_on_input(hash_map: HashMap):
    listener = hash_map.get('listener')
    if listener == 'btn_save_to_device':
        if hash_map.containsKey("prices"):
            prices_str = hash_map.get("_prices")
            ncl = noClass("pricechecker_kit")
            ncl.put("prices", prices_str, True)

            prices_ncl.destroy()
            prices = json.loads(prices_str)
            for item in prices:
                data = {
                    'price': item['price'],
                    'name': item['name'],
                    'barcode': item['barcode']
                }
                prices_ncl.put(
                    item['barcode'], json.dumps(data, ensure_ascii=False), True)

            hash_map.put("toast", "Сохранение завершено")

    elif listener == 'btn_save_to_suip':
        ncl = noClass("pricechecker_kit")
        prices_str = ncl.get("prices")
        hash_map.put("NoProcessSUIP", '')
        hash_map.put("NoPyHandlersSUIP", '')
        detected = hash_map.get("_detected", from_json=True) or []
        confirmed = hash_map.get("_confirmed", from_json=True) or []
        declined = hash_map.get("_declined", from_json=True) or []
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
                    declined.append(price)
        _data = {
            "prices": prices,
            "confirmed": confirmed,
            "declined": declined,
            "detected": declined + confirmed,
        }
        hash_map.put("_data", json.dumps(_data))
        hash_map.toast('Успешно')

    elif listener == 'btn_show_db':
        ncl = noClass("pricechecker_kit")
        prices_str = ncl.get("prices")
        hash_map.put('toast', json.dumps(prices_str))

    elif listener == 'btn_refresh_db':
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


@HashMap()
def scan_settings_on_start(hash_map: HashMap):
    screen = ui_models.SettingsScreen(hash_map, rs_settings)
    screen.on_start()

@HashMap()
def scan_settings_on_input(hash_map: HashMap):
    screen = ui_models.SettingsScreen(hash_map, rs_settings)
    screen.on_input()

@HashMap()
def on_create(hash_map: HashMap):
    hash_map.put('price_checker_info', 'Нет проверенных ценников')
    hash_map.put('CVDetectors', 'barcode')
    price_invalid_ncl.destroy()
    counter_ncl.destroy()
    hash_map.delete('last_error_barcode')
    hash_map.delete('last_error_obj_id')
    hash_map.set_vision_settings(
        min_length=PRICE_MIN_LEN,
        max_length=PRICE_MAX_LEN,
        ReplaceO=True,
        ToUpcase=True,
        OnlyNumbers=True
    )
    hash_map.put('UseVisionSettings', '')

def write_caption(hash_map: HashMap, object_id: int, caption: str):
    odm_list = hash_map.get('object_detector_mode')
    odm_list = json.loads(odm_list) if odm_list else []
    item_in_dm = next((item for item in odm_list if item['object_id'] == object_id), None)
    if item_in_dm:
        item_in_dm['mode'] = 'stop'
    else:
        odm_list.append({'object_id': object_id, 'mode': 'stop'})

    hash_map.put('object_detector_mode', json.dumps(odm_list))
    caption_data = {'object': str(object_id), 'caption': caption}
    hash_map.add_to_cv_list(caption_data, 'object_caption_list', _dict=True)
    hash_map.remove_from_cv_list(str(object_id), 'yellow_list')
    hash_map.add_to_cv_list(str(object_id), 'stop_listener_list')


def confirm_object(hash_map: HashMap, object_id: int, barcode: str, item: dict):
    hash_map.add_to_cv_list(str(object_id), 'green_list')
    caption = item['name'] + ", <b> Цена: " + str(
        item['price']) + "</b>. Цена совпадает!"
    write_caption(hash_map, object_id, caption)
    yellow_list_ncl.delete(barcode)


def decline_object(hash_map: HashMap, object_id: int, barcode: str, item: dict):
    hash_map.add_to_cv_list(str(object_id), 'red_list')
    caption = item['name'] + ", <b> Цена: " + str(
        item['price']) + "</b>. Цена не совпадает!"
    write_caption(hash_map, object_id, caption)
    yellow_list_ncl.delete(barcode)


def barcode_input(hash_map: HashMap, current_object_id: int, barcode: str):
    item = prices_ncl.get(barcode)
    if not item:
        return
    in_processing = yellow_list_ncl.get(barcode)
    if in_processing and current_object_id in json.loads(in_processing):
        return
    item = json.loads(item)
    confirmed = item.get('confirmed')
    if confirmed is None:
        hash_map.add_to_cv_list(str(current_object_id), 'yellow_list')
        ids_list = yellow_list_ncl.get(barcode)
        ids_list = json.loads(ids_list) if ids_list else []
        ids_list.append(current_object_id)
        yellow_list_ncl.put(barcode, json.dumps(ids_list), True)
        hash_map.add_to_cv_list(
            {'object_id': current_object_id, 'mode': 'ocr'},
            'object_detector_mode', _dict=True)
    elif confirmed is True:
        confirm_object(hash_map, current_object_id, barcode, item)
    elif confirmed is False:
        decline_object(hash_map, current_object_id, barcode, item)


def price_input(hash_map: HashMap, current_object_id: int, price: str):
    barcode = None
    for key in json.loads(yellow_list_ncl.getallkeys()):
        if current_object_id in json.loads(yellow_list_ncl.get(key)):
            barcode = key
            break
    if not barcode:
        return
    item = json.loads(prices_ncl.get(barcode))
    if price == str(item['price']):
        valid_prices = price_valid_ncl.get(barcode)
        valid_prices = json.loads(valid_prices) if valid_prices else []
        if not valid_prices:
            price_valid_ncl.put(barcode, json.dumps([price]), True)
            hash_map.put('price_checker_info',
                         f"{barcode} Реальная цена: {item['price']} Найдено: {price}")
        elif len(valid_prices) < int(rs_settings.get('scan_settings_valid_price_amount')):
            price_valid_ncl.put(barcode, json.dumps(valid_prices + [price]), True)
            hash_map.put('price_checker_info',
                         f"{barcode} Реальная цена: {item['price']} Найдено: {valid_prices + [price]}")
        else:
            confirm_object(hash_map, current_object_id, barcode, item)
            item.update(confirmed=True)
            prices_ncl.put(barcode, json.dumps(item), True)
            detected_ncl.put(barcode, json.dumps(item), True)
            hash_map.beep()
            hash_map.put('last_barcode', barcode)
            hash_map.put('last_obj_id', str(current_object_id))
    else:
        errors = price_invalid_ncl.get(barcode)
        errors = json.loads(errors) if errors else []
        if not errors:
            price_invalid_ncl.put(barcode, json.dumps([price]), True)
            hash_map.put('price_checker_info',
                         f"{barcode} Реальная цена: {item['price']} Найдено: {price}")
        elif len(errors) < int(rs_settings.get('scan_settings_invalid_price_amount')):
            price_invalid_ncl.put(barcode,json.dumps(errors + [price]), True)
            hash_map.put('price_checker_info',
                         f"{barcode} Реальная цена: {item['price']} Найдено: {errors + [price]}")
        else:
            decline_object(hash_map, current_object_id, barcode, item)
            item.update(confirmed=False)
            prices_ncl.put(barcode, json.dumps(item), True)
            detected_ncl.put(barcode, json.dumps(item), True)
            hash_map.playsound('error')
            hash_map.put('last_barcode', barcode)
            hash_map.put('last_obj_id', str(current_object_id))


def is_dm_stop(hash_map: HashMap, object_id: int) -> bool:
    odm_list = hash_map.get('object_detector_mode')
    odm_list = json.loads(odm_list) if odm_list else []
    return bool(next((item for item in odm_list
                      if item['object_id'] == object_id
                      and item['mode'] == 'stop'), None))


@HashMap()
def on_input(hash_map: HashMap):
    listener = hash_map.get('listener')
    if listener == 'Сброс последнего':
        reset_last_error(hash_map)
    elif listener == 'Сброс подсчёта':
        reset_all(hash_map)


@HashMap()
def on_obj_detected(hash_map: HashMap):
    current_object = json.loads(hash_map.get("current_object"))
    if is_dm_stop(hash_map, current_object['object_id']):
        return
    obj_value = current_object['value']
    if not obj_value or len(current_object['value']) > 19:
        return
    if len(obj_value) > PRICE_MAX_LEN:
        if obj_value.isdigit():
            barcode_input(hash_map, current_object['object_id'], obj_value)
    else:
        price_input(hash_map, current_object['object_id'], obj_value)


def reset_last_error(hash_map: HashMap) -> None:
    """Сбрасывает ошибку цены у последнего ценника с неверной ценой"""
    barcode = hash_map.get('last_barcode')
    if not barcode:
        hash_map.toast('Нет результатов подсчета')
        return
    item = json.loads(prices_ncl.get(barcode))
    item.pop('confirmed')
    prices_ncl.put(barcode, json.dumps(item), True)
    hash_map.delete('last_barcode')
    obj_id = hash_map.get('last_obj_id')
    hash_map.remove_from_cv_list(obj_id, 'yellow_list')
    yellow_list_ncl.delete(barcode)
    hash_map.remove_from_cv_list(obj_id, 'red_list')
    hash_map.remove_from_cv_list(obj_id, 'green_list')
    hash_map.remove_from_cv_list(obj_id, 'stop_listener_list')
    hash_map.remove_from_cv_list({'object_id': int(obj_id), 'mode': 'stop'}, 'object_detector_mode', _dict=True)
    hash_map.put('price_checker_info', "")
    hash_map.delete('last_obj_id')
    price_invalid_ncl.destroy()
    price_valid_ncl.destroy()
    counter_ncl.destroy()
    detected_ncl.delete(barcode)
    hash_map.toast('Штрихкод: ' + barcode + '. Подсчет сброшен.')

def reset_all(hash_map: HashMap) -> None:
    """Полностью удаляет все результаты подсчёта"""
    hash_map.put('price_checker_info', "Нет проверенных ценников")
    hash_map.put('yellow_list', "[]")
    hash_map.put('red_list', "[]")
    hash_map.put('green_list', "[]")
    hash_map.put('stop_listener_list', "[]")
    hash_map.put('object_detector_mode', "[]")
    hash_map.put('object_caption_list', "[]")
    hash_map.delete('last_barcode')
    hash_map.delete('last_obj_id')
    yellow_list_ncl.destroy()
    price_invalid_ncl.destroy()
    price_valid_ncl.destroy()
    counter_ncl.destroy()
    barcode_list = json.loads(detected_ncl.getallkeys())
    for barcode in barcode_list:
        detected_ncl.delete(barcode)
        item = json.loads(prices_ncl.get(barcode))
        item.pop('confirmed')
        prices_ncl.put(barcode, json.dumps(item), True)
    hash_map.toast('Подсчет сброшен')