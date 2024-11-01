from City import City

class CityManager:
    cities_by_name = {}
    cities_by_uuid = {}
    initialized = False

    @staticmethod
    def init(cities: list[City]):
        for city in cities:


            CityManager.cities_by_name[city.name] = city
            CityManager.cities_by_uuid[city.uuid] = city.info["translated_city_names"]

        CityManager.initialized = True

    @staticmethod
    def find_by_name(name) -> City:
        if not CityManager.initialized:
            raise "Значения не заинициализированы"

        return CityManager.cities_by_name[name]

    @staticmethod
    def find_by_uuid(uuid, lang="ru") -> City:
        if not CityManager.initialized:
            raise "Значения не заинициализированы"

        return CityManager.cities_by_uuid[uuid][lang]
