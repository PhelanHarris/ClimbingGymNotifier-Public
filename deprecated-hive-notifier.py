# $ ssh pi@raspberrypi.local
# $ S*******
# $ screen
# $ python3 hive-notifier.py
# $ CTRL-A, D
# $ screen -ls
# $ screen -r $screen_running

import requests
from twilio.rest import Client
import json
from time import sleep
import datetime

phone_number_database = {"Phelan": 11111111111}

twilio_sid = "REDACTED"
twilio_auth_token = "REDACTED"
twilio_phone_number = 123
alert_phone_numbers = [phone_number_database["Phelan"]]
hive_offering_guid = "484c1a7ca09145419ef258eeb894c38f"
# hive_offering_guid = '6fa9139cc3584fc0a5662a5c36d68958'
hive_url = "https://app.rockgympro.com/b/widget/?a=equery"
request_interval = 60  # seconds


def sendText(message):
    for phone_number in alert_phone_numbers:
        Client(twilio_sid, twilio_auth_token).messages.create(
            to=phone_number, from_=twilio_phone_number, body=message
        )


time_slots_to_check = {}
date_to_check = input("Enter date to see available slots: ")
while date_to_check != "":
    form_data = {
        "offering_guid": hive_offering_guid,
        "fctrl_4": "show_date",
        "show_date": date_to_check,
    }

    result_text = requests.post(hive_url, form_data).text

    raw_slots = result_text.split("'offering-page-schedule-list-time-column'>\\n")[1:]
    time_slots = []
    for raw_slot in raw_slots:
        time_slot = raw_slot.split("\\n<\\/td>")[0].strip()
        is_available = "offering-page-event-is-full" not in raw_slot
        time_slots.append(time_slot)
        print(str(len(time_slots)) + ": " + time_slot)

    times_to_check = []
    time_slot_to_add = input(
        "Select time slot to enable availability notifications (leave blank to move on): "
    )

    while time_slot_to_add.isdigit():
        time_slot_to_add = int(time_slot_to_add)
        if time_slot_to_add < 1 or time_slot_to_add > len(time_slots):
            print(
                "Invalid number. Please pick a number between 1 and "
                + str(len(time_slots))
            )
        elif time_slots[time_slot_to_add - 1] in times_to_check:
            print("Already selected that time slot")
        else:
            times_to_check.append(time_slots[time_slot_to_add - 1])

        time_slot_to_add = input(
            "Select time slot to enable availability notifications (leave blank to move on): "
        )

    if len(times_to_check) > 0:
        time_slots_to_check[date_to_check] = times_to_check

    date_to_check = input(
        "Enter date to see available slots (leave blank to move on): "
    )

print("Notifications enabled for the following time slots:")
print(json.dumps(time_slots_to_check, indent=2))

time_slot_list = []
for date in time_slots_to_check:
    time_slot_list.extend(time_slots_to_check[date])

sendText(
    "Hive climbing availability notifications enabled for the following time slots:\n"
    + "\n".join(time_slot_list)
)


last_health_notification = datetime.date.today()

while len(time_slots_to_check) > 0:
    sleep(60)
    dates_alerted = []

    if (
        datetime.date.today() > last_health_notification
        and datetime.datetime.now().hour > 9
    ):
        last_health_notification = datetime.date.today()

        time_slot_list = []
        for date in time_slots_to_check:
            time_slot_list.extend(time_slots_to_check[date])

        sendText(
            "Hive climbing availability notifications enabled for the following time slots:\n"
            + "\n".join(time_slot_list)
        )

    for date_to_check in time_slots_to_check:
        print(
            str(datetime.datetime.now())
            + ": Checking if slots available on "
            + ", ".join(time_slots_to_check[date_to_check])
        )

        form_data = {
            "offering_guid": hive_offering_guid,
            "fctrl_4": "show_date",
            "show_date": date_to_check,
        }

        result_text = requests.post(hive_url, form_data).text

        raw_slots = result_text.split("'offering-page-schedule-list-time-column'>\\n")[
            1:
        ]
        available_slots = []
        for raw_slot in raw_slots:
            time_slot = raw_slot.split("\\n<\\/td>")[0].strip()
            is_available = "offering-page-event-is-full" not in raw_slot
            num_slots = 0

            if is_available and time_slot in time_slots_to_check[date_to_check]:
                available_slots.append(time_slot)

        if len(available_slots) > 0:
            print("Available slot found! Sending text...")
            sendText(
                "Hive Vancouver climbing slot opened up!\n" + "\n".join(available_slots)
            )

            dates_alerted.append(date_to_check)
        else:
            print("No slots available...")

    for date_alerted in dates_alerted:
        del time_slots_to_check[date_alerted]
