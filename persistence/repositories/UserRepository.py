from persistence.models.User import User
from persistence.repositories.BaseRepository import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self):
        self.model = User

    def find_admin_user(self):
        return self.find_all(where_clause="WHERE is_admin = 1")[0]

    def find_by_phone_number(self, phone_number):
        users = self.find_all("WHERE phone_number = " + str(phone_number))
        if len(users) < 1:
            return None
        return users[0]