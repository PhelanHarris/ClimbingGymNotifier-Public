import requests
from constants import HIVE_URL


def get_time_slot_availability(date_to_check, offering_guid):
    form_data = {
        "offering_guid": offering_guid,
        "fctrl_4": "show_date",
        "show_date": date_to_check,
    }

    result_text = requests.post(HIVE_URL, form_data).text

    raw_slots = result_text.split("'offering-page-schedule-list-time-column'>\\n")[1:]
    time_slot_availability = {}
    index = 0
    for raw_slot in raw_slots:
        index += 1
        time_slot = raw_slot.split("\\n<\\/td>")[0].strip().replace("  ", " ")
        is_available = "book-now-button" in raw_slot
        time_slot_availability[time_slot] = {
            "index": index,
            "is_available": is_available,
            "day_of_week": time_slot.split(",")[0].strip(),
            "start_time": time_slot.split(",")[2].split("to")[0].strip(),
            "end_time": time_slot.split(",")[2].split("to")[1].strip(),
        }

    return time_slot_availability