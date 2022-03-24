from persistence.models.BaseModel import BaseModel


class Notification(BaseModel):
    def __init__(self, id, facility_id, user_id, notification_date, time_slot, enabled):
        self.id = id
        self.facility_id = facility_id
        self.user_id = user_id
        self.notification_date = notification_date
        self.time_slot = time_slot
        self.enabled = enabled

    @staticmethod
    def get_table_name():
        return "notification"

    @staticmethod
    def get_column_names():
        return ["facility_id", "user_id", "notification_date", "time_slot", "enabled"]

    def __str__(self):
        return """Notification - id: {}, facility_id: {}, user_id: {}, notification_date: {}, time_slot: {}, enabled: {}""".format(
            self.id,
            self.facility_id,
            self.user_id,
            self.notification_date,
            self.time_slot,
            self.enabled,
        )