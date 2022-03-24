import logging
from flask import Flask, request, redirect
from twilio.twiml.messaging_response import MessagingResponse
from persistence.models.User import User
from persistence.models.Facility import Facility
from persistence.models.Notification import Notification
from persistence.repositories.UserRepository import UserRepository
from persistence.repositories.FacilityRepository import FacilityRepository
from persistence.repositories.NotificationRepository import NotificationRepository
from datetime import date, timedelta, datetime
from lib import get_time_slot_availability
from logging.handlers import RotatingFileHandler
import traceback
import os


logger = logging.getLogger("Rotating App Log")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler("logs/app.log", maxBytes=100000, backupCount=5)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

app = Flask(__name__)

user_repository = UserRepository()
facility_repository = FacilityRepository()
notification_repository = NotificationRepository()


def get_response_message(message="Invalid message."):
    resp = MessagingResponse()
    resp.message(message)
    return str(resp)


def next_weekday(d, weekday):
    days_ahead = (7 + weekday - d.weekday()) % 7
    return d + timedelta(days_ahead)


@app.route("/sms", methods=["GET", "POST"])
def sms_reply():
    try:
        message_body = str(request.values.get("Body", "")).lower().strip()
        sender = int(request.values.get("From", 0))

        if message_body == "":
            return get_response_message()

        user = user_repository.find_by_phone_number()
        if user == None:
            logger.info(
                "Message recieved from unknown sender ({}): {}".format(
                    str(sender), message_body
                )
            )
            user = User(0, "", sender, 0, "", 0, 0, 0)
            user_repository.save(user)
            return get_response_message(
                "Hi there! I don't recognize your number. Please reply with your name to create an account."
            )
        logger.info(
            "Message recieved from {} ({}): {}".format(
                user.name, str(sender), message_body
            )
        )

        if message_body.startswith("ac") and user.is_admin == 1:
            os.system(
                'python3 /home/pi/ACController/handle_command.py "{}"'.format(
                    message_body
                )
            )
            return str(MessagingResponse())

        facilities = facility_repository.find_all()
        facilities_string = ", ".join(
            map(lambda f: "'{}'".format(f.location), facilities)
        )
        facilities_dict = {facility.id: facility for facility in facilities}

        if user.name == "":
            user.name = str(request.values.get("Body", "")).strip()
            user_repository.save(user)
            if user.is_account_setup == 0:
                return get_response_message(
                    "Hi {}! Please reply with the location of your primary gym to finish creating your account. Available gyms: {}".format(
                        user.name, facilities_string
                    )
                )
            else:
                return get_response_message(
                    "Hi {}! Your name has been successfully changed.".format(user.name)
                )

        if user.primary_facility_id == 0:
            for facility_id in facilities_dict:
                if message_body == facilities_dict[facility_id].location.lower():
                    user.primary_facility_id = facility_id
                    user.most_recent_requested_date = ""
                    user_repository.save(user)
                    if user.is_account_setup == 0:
                        user.is_account_setup = 1
                        user_repository.save(user)
                        return get_response_message(
                            "Set current gym to {}. Congratulations, your account is set up and ready to go! Reply 'commands' to see how to manage your notifications.".format(
                                facilities_dict[facility_id].location
                            )
                        )
                    else:
                        return get_response_message(
                            "Changed current gym to {}.".format(
                                facilities_dict[facility_id].location
                            )
                        )
            return get_response_message(
                "Please reply with the location of your gym. Available gyms: {}".format(
                    facilities_string
                )
            )

        facility = facilities_dict[user.primary_facility_id]

        if message_body == "commands":
            return get_response_message(
                "Climbing Gym Notifier commands:\n\nTo create a notification for yourself, reply with the day of the week that you would like to book, and then follow subsequent instructions to pick your time slots. Add 'next' before the day to specify that day next week.\n\nTo change your current gym, reply 'change gym'.\n\nTo change your name, reply 'change name'.\n\nTo see all your current notifications, reply 'notifications'.\n\nTo remove all your notifications, reply 'remove all'.".format(
                    facility.location, facilities_string
                )
            )

        if message_body == "change gym":
            user.primary_facility_id = 0
            user_repository.save(user)
            return get_response_message(
                "Please reply with the location of your gym. Available gyms: {}".format(
                    facilities_string
                )
            )

        if message_body == "change name":
            user.name = ""
            user_repository.save(user)
            return get_response_message("Please reply with your name.")

        if message_body == "enable":
            if user.most_recent_notification_id == 0:
                return get_response_message("Error: No notification to enable.")

            notification = notification_repository.find_by_id(
                user.most_recent_notification_id
            )
            notification.enabled = 1
            notification_repository.save(notification)
            user.most_recent_notification_id = 0
            user_repository.save(user)
            return get_response_message(
                "Re-enabled notification for {}".format(notification.time_slot)
            )

        if message_body == "remove":
            if user.most_recent_notification_id == 0:
                return get_response_message("Error: No notifications to remove.")

            notification_repository.delete_all_for_user_on_same_day_as(
                user.id, user.most_recent_notification_id
            )
            user.most_recent_notification_id = 0
            user_repository.save(user)

            return get_response_message(
                "Cancelled all notifications for {}.".format(
                    notification.notification_date
                )
            )

        if message_body == "remove all":
            notification_repository.delete_all_for_user(user.id)
            user.most_recent_notification_id = 0
            user_repository.save(user)
            return get_response_message(
                "Successfully cancelled all your notifications."
            )

        if message_body == "notifications":
            notifications = notification_repository.find_all_enabled_by_user_id(user.id)
            if len(notifications) == 0:
                return get_response_message(
                    "You do not currently have any notifications set up."
                )

            notifications_string = "Current notifications:\n"
            for notification in notifications:
                notifications_string += "{}: {}\n".format(
                    facilities_dict[notification.facility_id].location,
                    notification.time_slot,
                )

            return get_response_message(notifications_string)

        if message_body[0].isdigit():
            if user.most_recent_requested_date != "":
                date_to_check = datetime.strptime(
                    user.most_recent_requested_date, "%Y-%m-%d"
                ).date()
                if date_to_check < date.today():
                    return get_response_message()

            time_slot_availability = get_time_slot_availability(
                user.most_recent_requested_date, facility.offering_guid
            )
            indexes = message_body.split(",")
            time_slots_to_add = []
            for index in indexes:
                index = int(index.strip())
                time_slot = list(time_slot_availability.keys())[index - 1]
                time_slots_to_add.append(time_slot)

            for time_slot in time_slots_to_add:
                notification = Notification(
                    0,
                    facility.id,
                    user.id,
                    user.most_recent_requested_date,
                    time_slot,
                    1,
                )
                notification_repository.save(notification)

            return get_response_message(
                "Hive {} notifications enabled for:\n{}".format(
                    facility.location, "\n".join(time_slots_to_add)
                )
            )

        date_to_check = date.today()
        input_is_valid = False
        if message_body.startswith("next"):
            message_body = message_body.split(" ", 1)[1]
            date_to_check = date_to_check + timedelta(7)

        if message_body == "today":
            date_to_check = date.today()
            input_is_valid = True
        elif message_body == "m" or message_body == "mon" or message_body == "monday":
            input_is_valid = True
            date_to_check = next_weekday(date_to_check, 0)
        elif message_body == "t" or message_body == "tue" or message_body == "tuesday":
            input_is_valid = True
            date_to_check = next_weekday(date_to_check, 1)
        elif (
            message_body == "w" or message_body == "wed" or message_body == "wednesday"
        ):
            input_is_valid = True
            date_to_check = next_weekday(date_to_check, 2)
        elif (
            message_body == "th" or message_body == "thu" or message_body == "thursday"
        ):
            input_is_valid = True
            date_to_check = next_weekday(date_to_check, 3)
        elif message_body == "f" or message_body == "fri" or message_body == "friday":
            input_is_valid = True
            date_to_check = next_weekday(date_to_check, 4)
        elif message_body == "s" or message_body == "sat" or message_body == "saturday":
            input_is_valid = True
            date_to_check = next_weekday(date_to_check, 5)
        elif message_body == "su" or message_body == "sun" or message_body == "sunday":
            input_is_valid = True
            date_to_check = next_weekday(date_to_check, 6)

        if input_is_valid is False:
            return get_response_message(
                "Sorry, I am not able to handle this input. Try replying with 'commands' to see a list of available commands."
            )

        time_slot_availability = get_time_slot_availability(
            date_to_check, facility.offering_guid
        )

        formatted_time_slots = ""
        for time_slot in time_slot_availability:
            time_slot_obj = time_slot_availability[time_slot]
            formatted_time_slots += "{}: {} to {}\n".format(
                str(time_slot_obj["index"]),
                time_slot_obj["start_time"],
                time_slot_obj["end_time"],
            )

        user.most_recent_requested_date = str(date_to_check)
        user_repository.save(user)

        return get_response_message(
            "Hive {} time slots for {}:\n{}Please reply with comma separated numbers of the time slots you would like.".format(
                facility.location,
                date_to_check.strftime("%a, %B %d"),
                formatted_time_slots,
            )
        )
    except Exception as e:
        logger.error(str(e))
        logger.error(traceback.format_exc())
        return get_response_message("An unexpected error occurred.")


if __name__ == "__main__":
    app.run(debug=True, port=80, host="0.0.0.0")
