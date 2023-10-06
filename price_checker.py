import json
from java import jclass

noClass = jclass("ru.travelfood.simple_ui.NoSQL")
rs_settings = noClass("rs_settings")
prices_ncl = noClass("prices_ncl")
yellow_list_ncl = noClass("yellow_list_ncl")
price_valid_ncl = noClass("price_valid_ncl")
price_invalid_ncl = noClass("price_invalid_ncl")
detected_ncl = noClass("detected_ncl")
active_cv_ncl = noClass("active_cv_ncl")
dm_mode_ncl = noClass("dm_mode_ncl")


class PriceChecker:
    def __init__(self, hashmap):
        self.hash_map = hashmap

    def handle_value(self):
        current_object = json.loads(self.hash_map.get("current_object"))
        if dm_mode_ncl.get(str(current_object['object_id'])) == 'stop':
            return
        obj_value = current_object['value']
        if len(obj_value) > rs_settings.get('price_max_length'):
            self.handle_barcode(current_object['object_id'], obj_value)
        else:
            if obj_value.startswith('0'):
                return
            self.handle_price(current_object['object_id'], obj_value)
        return self.hash_map.hash_map

    def handle_barcode(self, current_object_id: int, barcode: str):
        item = prices_ncl.get(barcode)
        if not item:
            return
        in_processing = yellow_list_ncl.get(barcode)
        if in_processing and current_object_id in json.loads(in_processing):
            return
        item = json.loads(item)
        confirmed = item.get('confirmed')
        if confirmed is None:
            self.hash_map.add_to_cv_list(str(current_object_id), 'yellow_list')
            ids_list = yellow_list_ncl.get(barcode)
            ids_list = json.loads(ids_list) if ids_list else []
            ids_list.append(current_object_id)
            yellow_list_ncl.put(barcode, json.dumps(ids_list), True)
            self.hash_map.add_to_cv_list(
                {'object_id': current_object_id, 'mode': 'ocr'},
                'object_detector_mode', _dict=True)
            dm_mode_ncl.put(str(current_object_id), 'ocr')
        elif confirmed is True:
            self._confirm_object(current_object_id, barcode, item)
        elif confirmed is False:
            self._decline_object(current_object_id, barcode, item)

    def handle_price(self, current_object_id: int, price: str):
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
                self.hash_map.put('price_checker_info',
                             f"{barcode} Реальная цена: {item['price']} Найдено: {[price]}")
            elif len(valid_prices) + 1 < int(
                    rs_settings.get('scan_settings_valid_price_amount')):
                price_valid_ncl.put(barcode, json.dumps(valid_prices + [price]), True)
                self.hash_map.put('price_checker_info',
                             f"{barcode} Реальная цена: {item['price']} Найдено: {valid_prices + [price]}")
            else:
                price_valid_ncl.put(barcode, json.dumps(valid_prices + [price]), True)
                self.hash_map.put('price_checker_info',
                             f"{barcode} Реальная цена: {item['price']} Найдено: {valid_prices + [price]}")
                self._confirm_object(current_object_id, barcode, item)
                item.update(confirmed=True)
                prices_ncl.put(barcode, json.dumps(item), True)
                detected_ncl.put(barcode, json.dumps(item), True)
                self.hash_map.beep()
                active_cv_ncl.put('last_barcode', barcode, True)
                active_cv_ncl.put('last_obj_id', str(current_object_id), True)
        else:
            errors = price_invalid_ncl.get(barcode)
            errors = json.loads(errors) if errors else []
            if not errors:
                price_invalid_ncl.put(barcode, json.dumps([price]), True)
                self.hash_map.put('price_checker_info',
                             f"{barcode} Реальная цена: {item['price']} Найдено: {[price]}")
            elif len(errors) + 1 < int(
                    rs_settings.get('scan_settings_invalid_price_amount')):
                price_invalid_ncl.put(barcode, json.dumps(errors + [price]), True)
                self.hash_map.put('price_checker_info',
                             f"{barcode} Реальная цена: {item['price']} Найдено: {errors + [price]}")
            else:
                price_invalid_ncl.put(barcode, json.dumps(errors + [price]), True)
                self.hash_map.put('price_checker_info',
                             f"{barcode} Реальная цена: {item['price']} Найдено: {errors + [price]}")
                self._decline_object(current_object_id, barcode, item)
                item.update(confirmed=False)
                prices_ncl.put(barcode, json.dumps(item), True)
                detected_ncl.put(barcode, json.dumps(item), True)
                self.hash_map.playsound('error')
                active_cv_ncl.put('last_barcode', barcode, True)
                active_cv_ncl.put('last_obj_id', str(current_object_id), True)

    def reset_last_error(self) -> None:
        """Сбрасывает ошибку цены у последнего ценника с неверной ценой"""
        global finded_objects_temp_counter
        finded_objects_temp_counter = {}
        barcode = active_cv_ncl.get('last_barcode')
        if not barcode:
            self.hash_map.toast('Нет результатов подсчета')
            return
        item = json.loads(prices_ncl.get(barcode))
        item.pop('confirmed')
        prices_ncl.put(barcode, json.dumps(item), True)
        active_cv_ncl.delete('last_barcode')
        obj_id = active_cv_ncl.get('last_obj_id')
        active_cv_ncl.delete('last_obj_id')
        dm_mode_ncl.delete(obj_id)
        self.hash_map.remove_from_cv_list(obj_id, 'yellow_list')
        self.hash_map.remove_from_cv_list(obj_id, 'red_list')
        self.hash_map.remove_from_cv_list(obj_id, 'green_list')
        self.hash_map.remove_from_cv_list(obj_id, 'stop_listener_list')
        self.hash_map.remove_from_cv_list(
            {'object_id': int(obj_id), 'mode': 'stop'}, 'object_detector_mode',
            _dict=True)
        yellow_list_ncl.delete(barcode)
        price_invalid_ncl.delete(barcode)
        price_valid_ncl.delete(barcode)
        detected_ncl.delete(barcode)

        self.hash_map.put('price_checker_info',
                     'Штрихкод: ' + barcode + '. Подсчет сброшен.')

    def reset_all(self) -> None:
        """Полностью удаляет все результаты подсчёта"""
        global finded_objects_temp_counter
        finded_objects_temp_counter = {}
        self.hash_map.put('yellow_list', "[]")
        self.hash_map.put('red_list', "[]")
        self.hash_map.put('green_list', "[]")
        self.hash_map.put('stop_listener_list', "[]")
        self.hash_map.put('object_detector_mode', "[]")
        self.hash_map.put('object_caption_list', "[]")
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
        self.hash_map.put('price_checker_info', "Нет проверенных ценников")
        active_cv_ncl.destroy()

    def price_scan_on_start(self):
        self.hash_map.put('price_checker_info', 'Нет проверенных ценников')
        self.hash_map.put('CVDetectors', 'barcode')
        title = 'Распознавание ценников'
        if rs_settings.get('flag_cv_single_detector') == 'true':
            self.hash_map.put('CVSingleDetector')
            title += '   CVSingleDetector'
        if rs_settings.get('flag_cv_skip_nested') == 'true':
            self.hash_map.put('CVSkipNested')
            title += '   CVSkipNested'
        price_invalid_ncl.destroy()
        price_valid_ncl.destroy()
        dm_mode_ncl.destroy()
        active_cv_ncl.delete('last_barcode')
        active_cv_ncl.delete('last_obj_id')
        self.hash_map.set_vision_settings(
            min_length=rs_settings.get('price_min_length'),
            max_length=rs_settings.get('price_max_length'),
            ReplaceO=False,
            ToUpcase=False,
            OnlyNumbers=True
        )
        self.hash_map.put('title_cv', title)
        self.hash_map.put('UseVisionSettings', '')

    def price_scan_on_input(self):
        listener = self.hash_map.get('listener')
        if listener == 'Сброс последнего':
            self.reset_last_error()
        elif listener == 'Сброс подсчёта':
            self.reset_all()

    def _write_caption(self, object_id: int, caption: str):
        odm_list = self.hash_map.get('object_detector_mode')
        odm_list = json.loads(odm_list) if odm_list else []
        item_in_dm = next((item for item in odm_list if item['object_id'] == object_id), None)
        if item_in_dm:
            item_in_dm['mode'] = 'stop'
        else:
            odm_list.append({'object_id': object_id, 'mode': 'stop'})
    
        self.hash_map.put('object_detector_mode', json.dumps(odm_list))
        dm_mode_ncl.put(str(object_id), 'stop', True)
        caption_data = {'object': str(object_id), 'caption': caption}
        self.hash_map.add_to_cv_list(caption_data, 'object_caption_list', _dict=True)
        self.hash_map.remove_from_cv_list(str(object_id), 'yellow_list')
    
    def _confirm_object(self, object_id: int, barcode: str, item: dict):
        self.hash_map.add_to_cv_list(str(object_id), 'green_list')
        caption = item['name'] + ", <b> Цена: " + str(
            item['price']) + "</b>. Цена совпадает!"
        self._write_caption(object_id, caption)
        yellow_list_ncl.delete(barcode)
    
    def _decline_object(self, object_id: int, barcode: str, item: dict):
        self.hash_map.add_to_cv_list(str(object_id), 'red_list')
        caption = item['name'] + ", <b> Цена: " + str(
            item['price']) + "</b>. Цена не совпадает!"
        self._write_caption(object_id, caption)
        yellow_list_ncl.delete(barcode)


