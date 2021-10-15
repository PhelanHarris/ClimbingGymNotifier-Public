from models.BaseModel import BaseModel


class Facility(BaseModel):
    def __init__(self, id, location, offering_guid):
        self.id = id
        self.location = location
        self.offering_guid = offering_guid

    @staticmethod
    def get_table_name():
        return "facility"

    @staticmethod
    def get_column_names():
        return ["location", "offering_guid"]

    def __str__(self):
        return """Facility - id: {}, location: {}, offering_guid: {}""".format(
            self.id, self.location, self.offering_guid
        )