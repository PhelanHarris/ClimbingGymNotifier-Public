from persistence.models.Notification import Notification
from persistence.repositories.BaseRepository import BaseRepository


class NotificationRepository(BaseRepository):
    def __init__(self):
        self.model = Notification

    def find_all_enabled(self):
        return self.find_all("WHERE enabled = 1")

    def delete_all_for_user_on_same_day_as(self, user_id, notification_id):
        notification = self.find_by_id(notification_id)
        notifications = self.find_all(
            "WHERE user_id = {} and notification_date = '{}'".format(
                user_id, notification.notification_date
            )
        )
        for notification in notifications:
            self.delete(notification)

    def delete_all_for_user(self, user_id):
        notifications = self.find_all("WHERE user_id = {}".format(str(user_id)))
        for notification in notifications:
            self.delete(notification)

    def find_all_enabled_by_user_id(self, user_id):
        return self.find_all("WHERE user_id = {} AND enabled = 1".format(str(user_id)))
