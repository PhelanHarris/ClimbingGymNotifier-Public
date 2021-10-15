# $ ssh pi@raspberrypi.local
# $ S*******
# $ screen
# $ python3 hive-notifier.py
# $ CTRL-A, D
# $ screen -ls
# $ screen -r $screen_running

from repositories.Repository import Repository
from models.Facility import Facility
from models.User import User
from models.Notification import Notification
from twilio.rest import Client
from time import sleep
from logging.handlers import RotatingFileHandler
from lib import get_time_slot_availability
from datetime import datetime, timedelta
import requests
import traceback
import logging
import os

if not os.path.exists("logs"):
    os.makedirs("logs")

logger = logging.getLogger("Rotating Main Log")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler("logs/hive-notifier.log", maxBytes=100000, backupCount=5)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.info("Hive Notifier main app starting up...")

TWILIO_SID = "REDACTED"
TWILIO_AUTH_TOKEN = "REDACTED"
TWILIO_PHONE_NUMBER = 1111111111  # REDACTED
REQUEST_INTERVAL = 20  # seconds

facility_repository = Repository(Facility)
user_repository = Repository(User)
notification_repository = Repository(Notification)
last_error_notification_date = datetime.now() - timedelta(1)


def send_text(message, user):
    try:
        logger.info("Sending text to {}: {}".format(user.name, message))
        Client(TWILIO_SID, TWILIO_AUTH_TOKEN).messages.create(
            to=user.phone_number, from_=TWILIO_PHONE_NUMBER, body=message
        )
        return True
    except Exception as e:
        logger.error(str(e))
        return False


try:
    while True:
        # Get and prepare DB data
        facilities_dict = {
            facility.id: facility for facility in facility_repository.find_all()
        }
        users = user_repository.find_all()
        users_dict = {user.id: user for user in users}
        priority_users = list(filter(lambda user: user.is_admin == 1, users))
        priority_user_ids = list(map(lambda user: user.id, priority_users))
        notifications = notification_repository.find_all("WHERE enabled = 1")

        for facility_id in facilities_dict:
            facilities_dict[facility_id].notifications_dict = {}

        for notification in notifications:
            facility = facilities_dict[notification.facility_id]
            if notification.notification_date not in facility.notifications_dict:
                facility.notifications_dict[notification.notification_date] = []

            facility.notifications_dict[notification.notification_date].append(
                notification
            )

        # Check for available slots
        checked_slot = False
        for facility_id in facilities_dict:
            facility = facilities_dict[facility_id]
            for notification_date in facility.notifications_dict:
                checked_slot = True
                logger.info(
                    "Checking Hive {} for slots on {}".format(
                        facility.location, notification_date
                    )
                )
                time_slot_availability = None
                try:
                    time_slot_availability = get_time_slot_availability(
                        notification_date, facility.offering_guid
                    )
                except Exception as e:
                    if datetime.now() > (
                        last_error_notification_date + timedelta(hours=1)
                    ):
                        logger.error(str(e))
                        admin_user = user_repository.find_all(
                            where_clause="WHERE is_admin = 1"
                        )[0]
                        if send_text(
                            "Hive Notifier app: Error connecting to server!", admin_user
                        ):
                            last_error_notification_date = datetime.now()

                if time_slot_availability is not None:
                    notifications_to_check = []
                    for notification in facility.notifications_dict[notification_date]:
                        if (
                            notification.user_id in priority_user_ids
                            or len(
                                list(
                                    filter(
                                        lambda n: n.time_slot == notification.time_slot
                                        and n.user_id in priority_user_ids,
                                        facility.notifications_dict[notification_date],
                                    )
                                )
                            )
                            == 0
                        ):
                            notifications_to_check.append(notification)

                    for notification in notifications_to_check:
                        if notification.time_slot not in time_slot_availability:
                            year = int(notification.notification_date.split("-")[0])
                            month = int(notification.notification_date.split("-")[1])
                            day = int(notification.notification_date.split("-")[2])
                            time_string = (
                                notification.time_slot.split(",")[2]
                                .split("to")[0]
                                .strip()
                            )
                            hour = int(time_string.split(" ")[0].split(":")[0])
                            if "PM" in time_string:
                                hour += 12
                            minute = (
                                int(time_string.split(" ")[0].split(":")[1])
                                if ":" in time_string
                                else 0
                            )
                            notification_datetime = datetime(
                                year, month, day, hour, minute
                            )

                            if notification_datetime < (
                                datetime.now() + timedelta(minutes=3)
                            ):
                                message_content = "Hive {} time slot {} has started, no free slot was found.".format(
                                    facility.location, notification.time_slot
                                )
                                user = users_dict[notification.user_id]
                                if send_text(message_content, user):
                                    notification_repository.delete(notification)
                            else:
                                raise Exception(
                                    "Time slot {} not found!".format(
                                        notification.time_slot
                                    )
                                )

                        elif time_slot_availability[notification.time_slot][
                            "is_available"
                        ]:
                            message_content = "Hive {} slot opened up for {} at {}\n\nTip: Reply 'enable' if you missed the slot. Reply 'remove' to cancel other notifications on that date".format(
                                facility.location,
                                datetime.strptime(
                                    notification.notification_date, "%Y-%m-%d"
                                ).strftime("%a %b %d"),
                                time_slot_availability[notification.time_slot][
                                    "start_time"
                                ],
                            )
                            user = users_dict[notification.user_id]
                            if send_text(message_content, user):
                                notification.enabled = 0
                                notification_repository.save(notification)
                                if user.most_recent_notification_id != 0:
                                    notification_to_delete = (
                                        notification_repository.find_by_id(
                                            user.most_recent_notification_id
                                        )
                                    )
                                    if notification_to_delete is not None:
                                        notification_repository.delete(
                                            notification_to_delete
                                        )

                                user.most_recent_notification_id = notification.id
                                user_repository.save(user)

                else:
                    logger.info(
                        "Failed to get time slot availability for {}".format(
                            notification_date
                        )
                    )

        if checked_slot is False:
            logger.info(
                "No notifications are set up, did not check for available slots."
            )

        sleep(REQUEST_INTERVAL)

except Exception as e:
    logger.error(str(e))
    logger.error(traceback.format_exc())
    admin_user = user_repository.find_all(where_clause="WHERE is_admin = 1")[0]
    send_text(
        "Hive Notifier app: Fatal error has occurred, check the log file!", admin_user
    )
