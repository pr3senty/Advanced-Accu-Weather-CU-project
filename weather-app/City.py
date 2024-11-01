

class City:

    def __init__(self, city_uuid, city_name, city_info):
        self.uuid = city_uuid
        self.name = city_name
        self.info = city_info

    def __eq__(self, other):
        if type(other) is City:
            return self.uuid == other.uuid

    def __str(self):
        return self.name