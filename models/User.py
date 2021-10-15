from models.BaseModel import BaseModel


class User(BaseModel):
    def __init__(
        self,
        id,
        name,
        phone_number,
        primary_facility_id,
        most_recent_requested_date,
        most_recent_notification_id,
        is_account_setup,
        is_admin,
    ):
        self.id = id
        self.name = name
        self.phone_number = phone_number
        self.primary_facility_id = primary_facility_id
        self.most_recent_requested_date = most_recent_requested_date
        self.most_recent_notification_id = most_recent_notification_id
        self.is_account_setup = is_account_setup
        self.is_admin = is_admin

    @staticmethod
    def get_table_name():
        return "user"

    @staticmethod
    def get_column_names():
        return [
            "name",
            "phone_number",
            "primary_facility_id",
            "most_recent_requested_date",
            "most_recent_notification_id",
            "is_account_setup",
            "is_admin",
        ]

    def __str__(self):
        return """User - id: {}, name: {}, phone_number: {}, primary_facility_id: {}, most_recent_requested_date: {}, most_recent_notification_id: {}, is_account_setup: {}, is_admin: {}""".format(
            self.id,
            self.name,
            self.phone_number,
            self.primary_facility_id,
            self.most_recent_requested_date,
            self.most_recent_notification_id,
            self.is_account_setup,
            self.is_admin,
        )
