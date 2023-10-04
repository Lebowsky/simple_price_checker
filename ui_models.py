from abc import ABC
from typing import List

from ui_utils import HashMap


class MainEvents:
    def __init__(self, hash_map: HashMap, rs_settings):
        self.hash_map = hash_map
        self.rs_settings = rs_settings

    def app_before_on_start(self):
        self.hash_map.put('getJSONConfiguration', '')

    def app_on_start(self):
        # # TODO Обработчики обновления!
        # release = self.rs_settings.get('Release') or ''
        # conf = self.hash_map.get_json('_configuration')
        # current_release = None
        # toast = 'Готов к работе'
        #
        # try:
        #     current_release = conf['ClientConfiguration']['ConfigurationVersion']
        # except Exception as e:
        #     toast = 'Не удалось определить версию конфигурации'
        # finally:
        #     self.hash_map.remove('_configuration')
        #
        # if current_release and release != current_release:
        #     self.hash_map.put('UpdateConfigurations', '')
        #     self.rs_settings.put('Release', current_release, True)
        #     toast = f'Выполнено обновление на версию {current_release}'
        # self.hash_map.toast(toast)
        rs_default_settings = {
            'scan_settings_valid_price_amount': '3',
            'scan_settings_invalid_price_amount': '5',
            'flag_cv_single_detector': 'false',
            'flag_cv_skip_nested': 'false'
        }
        for key, value in rs_default_settings.items():
            if self.rs_settings.get(key) is None:
                self.rs_settings.put(key, value, True)


class Screen(ABC):
    screen_name: str
    process_name: str
    screen_values: List[str]

    def __init__(self, hash_map: HashMap, rs_settings):
        self.hash_map: HashMap = hash_map
        self.rs_settings = rs_settings


class SettingsScreen(Screen):
    screen_name = 'ScanSettings'
    process_name = 'Settings'
    screen_values = [
        'scan_settings_valid_price_amount',
        'scan_settings_invalid_price_amount'
    ]

    def __init__(self, hash_map: HashMap, rs_settings):
        super().__init__(hash_map, rs_settings)

    def on_start(self):
        for variable in self.screen_values:
            value = self.hash_map.get(variable)
            if value and value != '0':
                self.hash_map.put(variable, str(int(float(value))))
            else:
                value = self.rs_settings.get(variable)
                self.hash_map.put(variable, value)
        flag_sd = self.hash_map.get('flag_cv_single_detector')
        flag_sd = flag_sd if flag_sd else self.rs_settings.get('flag_cv_single_detector')
        self.hash_map.put('flag_cv_single_detector', flag_sd)
        flag_sn = self.hash_map.get('flag_cv_skip_nested')
        flag_sn = flag_sn if flag_sn else self.rs_settings.get('flag_cv_skip_nested')
        self.hash_map.put('flag_cv_skip_nested', flag_sn)

    def on_input(self):
        listener = self.hash_map.get('listener')
        if listener == 'btn_save_scan_settings':
            for variable in self.screen_values:
                value = self.hash_map.get(variable)
                if value and value != '0':
                    self.hash_map.put(variable, str(int(float(value))))
                    self.rs_settings.put(variable, str(int(float(value))), True)
            self.rs_settings.put('flag_cv_single_detector', self.hash_map.get('flag_cv_single_detector'), True)
            self.rs_settings.put('flag_cv_skip_nested', self.hash_map.get('flag_cv_skip_nested'), True)
            self.hash_map.toast('Настройки сохранены')
        if listener == 'ON_BACK_PRESSED':
            self.hash_map.finish_process()
