import json
from java import jclass

from ru.travelfood.simple_ui import SimpleUtilites as suClass

import ui_models
from ui_utils import HashMap

noClass = jclass("ru.travelfood.simple_ui.NoSQL")
rs_settings = noClass("rs_settings")
prices_ncl = noClass("price_ncl")
yellow_list_ncl = noClass("yellow_list_ncl")
price_valid_ncl = noClass("price_valid_ncl")
counter_ncl = noClass("counter_ncl")

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

    price_ncl = noClass("price_ncl")
    res = json.loads(price_ncl.findJSON("confirmed", True))
    hash_map.put("count_detected", str(len(res)))


@HashMap()
def save_to_device(hash_map: HashMap):  # Соб:onInput listener: btn_read Действ: run Тип обраб: python
    # Метод: save_to_device
    if hash_map.containsKey("prices"):
        prices_str = hash_map.get("_prices")
        ncl = noClass("pricechecker_kit")
        ncl.put("prices", prices_str, True)

        price_ncl = noClass("price_ncl")
        price_ncl.destroy()
        prices = json.loads(prices_str)
        for item in prices:
            price_ncl.put(item['barcode'],
                          json.dumps({'price': item['price'], 'name': item['name']}), True)

        hash_map.put("toast", "Сохранение завершено")

@HashMap()
def del_from_device(hash_map: HashMap):
    ncl = noClass("pricechecker_kit")
    ncl.delete("prices")
    hash_map.put("toast", "Удаление завершено")


@HashMap()
def show_db(hash_map: HashMap):
    ncl = noClass("pricechecker_kit")
    prices_str = ncl.get("prices")
    hash_map.put('toast', json.dumps(prices_str))


@HashMap()
def refresh_db(hash_map: HashMap):
    ncl = noClass("pricechecker_kit")
    price_ncl = noClass("price_ncl")
    price_ncl.destroy()
    prices = ncl.get('prices')
    if not prices:
        hash_map.toast('Список товаров prices пуст.')
        return
    for item in json.loads(prices):
        price_ncl.put(item['barcode'],
                      json.dumps({'price': item['price'], 'name': item['name']}), True)
    hash_map.toast('Данные обновлены')

@HashMap()
def save_to_suip(hash_map: HashMap):  # Соб:onInput listener: btn_save Действ: run Тип обраб: python Метод: save_to_suip
    ncl = noClass("pricechecker_kit")
    prices_str = ncl.get("prices")
    hash_map.put("NoProcessSUIP", '')
    hash_map.put("NoPyHandlersSUIP", '')
    detected = hash_map.get("_detected", from_json=True) or []
    confirmed = hash_map.get("_confirmed", from_json=True) or []
    prices = json.loads(prices_str)

    price_ncl = noClass("price_ncl")
    conf = json.loads(price_ncl.findJSON("confirmed", True))

    for elem in conf:
        for price in prices:
            if price['barcode'] == elem['key']:
                confirmed.append(price)
    decl = json.loads(price_ncl.findJSON("confirmed", True))
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
def on_create(hash_map: HashMap):
    hash_map.delete('price_checker_info')
    hash_map.put('CVDetectors', 'barcode')
    price_valid_ncl.destroy()
    counter_ncl.destroy()
    hash_map.delete('last_error_barcode')
    hash_map.delete('last_error_obj_id')

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
    caption = item['name'] + ", <b> Цена: " + str(item['price']) + "</b>"
    write_caption(hash_map, object_id, caption)
    yellow_list_ncl.delete(barcode)


def decline_object(hash_map: HashMap, object_id: int, barcode: str, item: dict):
    hash_map.add_to_cv_list(str(object_id), 'red_list')
    caption = item['name'] + ", <b> Цена: " + str(
        item['price']) + "</b>. Цена не совпадает!"
    write_caption(hash_map, object_id, caption)
    yellow_list_ncl.delete(barcode)


def barcode_input(hash_map: HashMap, current_object_id: int, barcode: str):
    in_processing = yellow_list_ncl.get(barcode)
    if in_processing and current_object_id in json.loads(in_processing):
        return
    item = prices_ncl.get(barcode)
    if not item:
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
    price = price.replace(' ', '').replace('o', '0').replace('O', '0')
    price = ''.join([letter for letter in price if letter.isdigit()])
    if not price:
        return
    if price == str(item['price']):
        confirm_object(hash_map, current_object_id, barcode, item)
        hash_map.put('price_checker_info', f"{barcode} Реальная цена: {item['price']} Найдено: {price}")
        item.update(confirmed=True)
        prices_ncl.put(barcode, json.dumps(item), True)
        hash_map.beep()
    else:
        errors = price_valid_ncl.get(barcode)
        errors = json.loads(errors) if errors else []
        if not errors:
            price_valid_ncl.put(barcode, json.dumps([price]), True)
            hash_map.put('price_checker_info', f"{barcode} Реальная цена: {item['price']} Найдено: {errors}")
        elif len(errors) < 5:
            price_valid_ncl.put(barcode,json.dumps(errors + [price]), True)
            hash_map.put('price_checker_info', f"{barcode} Реальная цена: {item['price']} Найдено: {errors + [price]}")
        else:
            decline_object(hash_map, current_object_id, barcode, item)
            item.update(confirmed=False)
            prices_ncl.put(barcode, json.dumps(item), True)
            hash_map.playsound('error')
            hash_map.put('last_error_barcode', barcode)
            hash_map.put('last_error_obj_id', str(current_object_id))


def is_dm_stop(hash_map: HashMap, object_id: int):
    odm_list = hash_map.get('object_detector_mode')
    odm_list = json.loads(odm_list) if odm_list else []
    return next((item for item in odm_list
                if item['object_id'] == object_id and item['mode'] == 'stop'), None)


def is_valid_barcode(barcode: str):
    if len(barcode) > 9 and barcode.isdigit():
        return True


@HashMap()
def ob_detected(hash_map: HashMap):
    current_object = json.loads(hash_map.get("current_object"))
    if is_dm_stop(hash_map, current_object['object_id']):
        return
    obj_value = current_object['value']
    if not obj_value or len(current_object['value']) > 19:
        return
    if is_valid_barcode(obj_value):
        barcode_input(hash_map, current_object['object_id'], obj_value)
    else:
        if not 1 < len(obj_value) < 7:
            return
        price_input(hash_map, current_object['object_id'], obj_value)

@HashMap()
def reset_last_error(hash_map: HashMap):
    """Сбрасывает ошибку цены у последнего ценника с неверной ценой"""
    barcode = hash_map.get('last_error_barcode')
    if not barcode:
        hash_map.toast('Нет ошибок')
        return
    item = json.loads(prices_ncl.get(barcode))
    item['confirmed'] = None
    prices_ncl.put(barcode, json.dumps(item), True)
    hash_map.delete('last_error_barcode')
    obj_id = hash_map.get('last_error_obj_id')
    hash_map.remove_from_cv_list(obj_id, 'yellow_list')
    yellow_list_ncl.delete(barcode)
    hash_map.remove_from_cv_list(obj_id, 'red_list')
    hash_map.remove_from_cv_list(obj_id, 'green_list')
    hash_map.remove_from_cv_list(obj_id, 'stop_listener_list')

    hash_map.remove_from_cv_list({'object_id': int(obj_id), 'mode': 'stop'}, 'object_detector_mode', _dict=True)
    hash_map.put('price_checker_info', "")
    hash_map.delete('last_error_obj_id')
    price_valid_ncl.destroy()
    counter_ncl.destroy()
