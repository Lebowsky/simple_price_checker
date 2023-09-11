from ui_utils import HashMap


class MainEvents:
    def __init__(self, hash_map: HashMap, rs_settings):
        self.hash_map = hash_map
        self.rs_settings = rs_settings

    def app_before_on_start(self):
        self.hash_map.put('getJSONConfiguration', '')

    def app_on_start(self):
        # TODO Обработчики обновления!
        release = self.rs_settings.get('Release') or ''
        conf = self.hash_map.get_json('_configuration')
        current_release = None
        toast = 'Готов к работе'

        try:
            current_release = conf['ClientConfiguration']['ConfigurationVersion']
        except Exception as e:
            toast = 'Не удалось определить версию конфигурации'
        finally:
            self.hash_map.remove('_configuration')

        if current_release and release != current_release:
            self.hash_map.put('UpdateConfigurations', '')
            self.rs_settings.put('Release', current_release, True)
            toast = f'Выполнено обновление на версию {current_release}'

        self.hash_map.toast(toast)


