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
detected_ncl = noClass("detected_ncl")
active_cv_ncl = noClass("active_cv_ncl")
dm_mode_ncl = noClass("dm_mode_ncl")
PRICE_MIN_LEN = 2
PRICE_MAX_LEN = 6
finded_objects_temp_counter = {}

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

@HashMap()
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

@HashMap()
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


@HashMap()
def scan_settings_on_start(hash_map: HashMap):
    screen = ui_models.SettingsScreen(hash_map, rs_settings)
    screen.on_start()


@HashMap()
def scan_settings_on_input(hash_map: HashMap):
    screen = ui_models.SettingsScreen(hash_map, rs_settings)
    screen.on_input()


@HashMap()
def price_scan_on_start(hash_map: HashMap):
    hash_map.put('price_checker_info', 'Нет проверенных ценников')
    hash_map.put('CVDetectors', 'barcode')
    title = 'Распознавание ценников'
    if rs_settings.get('flag_cv_single_detector') == 'true':
        hash_map.put('CVSingleDetector')
        title += '   CVSingleDetector'
    if rs_settings.get('flag_cv_skip_nested') == 'true':
        hash_map.put('CVSkipNested')
        title += '   CVSkipNested'
    price_invalid_ncl.destroy()
    price_valid_ncl.destroy()
    dm_mode_ncl.destroy()
    active_cv_ncl.delete('last_barcode')
    active_cv_ncl.delete('last_obj_id')
    hash_map.set_vision_settings(
        # min_length=PRICE_MIN_LEN,
        # max_length=PRICE_MAX_LEN,
        min_length=2,
        max_length=6,
        ReplaceO=False,
        ToUpcase=False,
        OnlyNumbers=True
    )
    hash_map.put('title_cv', title)
    hash_map.put('UseVisionSettings', '')


@HashMap()
def price_scan_on_input(hash_map: HashMap):
    listener = hash_map.get('listener')
    if listener == 'Сброс последнего':
        reset_last_error(hash_map)
    elif listener == 'Сброс подсчёта':
        reset_all(hash_map)


def reset_last_error(hash_map: HashMap) -> None:
    """Сбрасывает ошибку цены у последнего ценника с неверной ценой"""
    global finded_objects_temp_counter
    finded_objects_temp_counter = {}
    barcode = active_cv_ncl.get('last_barcode')
    if not barcode:
        hash_map.toast('Нет результатов подсчета')
        return
    item = json.loads(prices_ncl.get(barcode))
    item.pop('confirmed')
    prices_ncl.put(barcode, json.dumps(item), True)
    active_cv_ncl.delete('last_barcode')
    obj_id = active_cv_ncl.get('last_obj_id')
    active_cv_ncl.delete('last_obj_id')
    dm_mode_ncl.delete(obj_id)
    hash_map.remove_from_cv_list(obj_id, 'yellow_list')
    hash_map.remove_from_cv_list(obj_id, 'red_list')
    hash_map.remove_from_cv_list(obj_id, 'green_list')
    hash_map.remove_from_cv_list(obj_id, 'stop_listener_list')
    hash_map.remove_from_cv_list(
        {'object_id': int(obj_id), 'mode': 'stop'}, 'object_detector_mode', _dict=True)
    yellow_list_ncl.delete(barcode)
    price_invalid_ncl.delete(barcode)
    price_valid_ncl.delete(barcode)
    detected_ncl.delete(barcode)

    hash_map.put('price_checker_info', 'Штрихкод: ' + barcode + '. Подсчет сброшен.')


def reset_all(hash_map: HashMap) -> None:
    """Полностью удаляет все результаты подсчёта"""
    global finded_objects_temp_counter
    finded_objects_temp_counter = {}
    hash_map.put('yellow_list', "[]")
    hash_map.put('red_list', "[]")
    hash_map.put('green_list', "[]")
    hash_map.put('stop_listener_list', "[]")
    hash_map.put('object_detector_mode', "[]")
    hash_map.put('object_caption_list', "[]")
    active_cv_ncl.delete('last_barcode')
    active_cv_ncl.delete('last_obj_id')
    yellow_list_ncl.destroy()
    price_invalid_ncl.destroy()
    price_valid_ncl.destroy()
    dm_mode_ncl.destroy()
    barcode_list = json.loads(detected_ncl.getallkeys())
    for barcode in barcode_list:
        item = json.loads(prices_ncl.get(barcode))
        item.pop('confirmed')
        prices_ncl.put(barcode, json.dumps(item), True)
    detected_ncl.destroy()
    hash_map.put('price_checker_info', "Нет проверенных ценников")
    active_cv_ncl.destroy()


@HashMap()
def on_obj_detected(hash_map: HashMap):
    current_object = hash_map.get("current_object")
    global finded_objects_temp_counter
    if current_object not in finded_objects_temp_counter:
        finded_objects_temp_counter[current_object] = 1
    elif finded_objects_temp_counter[current_object] < rs_settings.get('objects_find_limit'):
        finded_objects_temp_counter[current_object] += 1
    else:
        return
    current_object = json.loads(hash_map.get("current_object"))
    if dm_mode_ncl.get(str(current_object['object_id'])) == 'stop':
        return
    obj_value = current_object['value']
    if len(obj_value) > PRICE_MAX_LEN:
        if obj_value.isdigit():
            barcode_input(hash_map, current_object['object_id'], obj_value)
    else:
        if obj_value.startswith('0'):
            return
        price_input(hash_map, current_object['object_id'], obj_value)


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
        dm_mode_ncl.put(str(current_object_id), 'ocr')
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
                         f"{barcode} Реальная цена: {item['price']} Найдено: {[price]}")
        elif len(valid_prices) + 1 < int(rs_settings.get('scan_settings_valid_price_amount')):
            price_valid_ncl.put(barcode, json.dumps(valid_prices + [price]), True)
            hash_map.put('price_checker_info',
                         f"{barcode} Реальная цена: {item['price']} Найдено: {valid_prices + [price]}")
        else:
            price_valid_ncl.put(barcode, json.dumps(valid_prices + [price]), True)
            hash_map.put('price_checker_info',
                         f"{barcode} Реальная цена: {item['price']} Найдено: {valid_prices + [price]}")
            confirm_object(hash_map, current_object_id, barcode, item)
            item.update(confirmed=True)
            prices_ncl.put(barcode, json.dumps(item), True)
            detected_ncl.put(barcode, json.dumps(item), True)
            hash_map.beep()
            active_cv_ncl.put('last_barcode', barcode, True)
            active_cv_ncl.put('last_obj_id', str(current_object_id), True)
    else:
        errors = price_invalid_ncl.get(barcode)
        errors = json.loads(errors) if errors else []
        if not errors:
            price_invalid_ncl.put(barcode, json.dumps([price]), True)
            hash_map.put('price_checker_info',
                         f"{barcode} Реальная цена: {item['price']} Найдено: {[price]}")
        elif len(errors) + 1 < int(rs_settings.get('scan_settings_invalid_price_amount')):
            price_invalid_ncl.put(barcode,json.dumps(errors + [price]), True)
            hash_map.put('price_checker_info',
                         f"{barcode} Реальная цена: {item['price']} Найдено: {errors + [price]}")
        else:
            price_invalid_ncl.put(barcode,json.dumps(errors + [price]), True)
            hash_map.put('price_checker_info',
                         f"{barcode} Реальная цена: {item['price']} Найдено: {errors + [price]}")
            decline_object(hash_map, current_object_id, barcode, item)
            item.update(confirmed=False)
            prices_ncl.put(barcode, json.dumps(item), True)
            detected_ncl.put(barcode, json.dumps(item), True)
            hash_map.playsound('error')
            active_cv_ncl.put('last_barcode', barcode, True)
            active_cv_ncl.put('last_obj_id', str(current_object_id), True)


def write_caption(hash_map: HashMap, object_id: int, caption: str):
    odm_list = hash_map.get('object_detector_mode')
    odm_list = json.loads(odm_list) if odm_list else []
    item_in_dm = next((item for item in odm_list if item['object_id'] == object_id), None)
    if item_in_dm:
        item_in_dm['mode'] = 'stop'
    else:
        odm_list.append({'object_id': object_id, 'mode': 'stop'})

    hash_map.put('object_detector_mode', json.dumps(odm_list))
    dm_mode_ncl.put(str(object_id), 'stop', True)
    caption_data = {'object': str(object_id), 'caption': caption}
    hash_map.add_to_cv_list(caption_data, 'object_caption_list', _dict=True)
    hash_map.remove_from_cv_list(str(object_id), 'yellow_list')


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
