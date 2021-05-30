import logging
import os
import time
from datetime import datetime
import webbrowser

from cowin_api.constants import Constants

logger = logging.getLogger(__name__)
logging.basicConfig(format="%(threadName)s:%(message)s")
logger.setLevel(logging.INFO)


def today() -> str:
    return datetime.now().strftime(Constants.DD_MM_YYYY)


def filter_centers_by_age_limit(centers: dict, min_age_limit: int, dose_number: str = '1'):
    original_centers = centers.get('centers')
    filtered_centers = {'centers': []}
    available_capacity_dose = 'available_capacity_dose'+dose_number
    for center in original_centers:
        filtered_sessions = []
        for session in center.get('sessions'):
            if session.get('min_age_limit') == min_age_limit and session.get(available_capacity_dose) > 2:
                filtered_sessions.append(session)
        if len(filtered_sessions) > 0:
            center['sessions'] = filtered_sessions
            filtered_centers['centers'].append(center)

    return filtered_centers


def beep():
    timeout = time.time() + 60*5
    while True:
        duration = 1  # seconds
        freq = 660  # Hz
        os.system('play -nq -t alsa synth {} sine {}'.format(duration, freq))
        time.sleep(1)
        if time.time() > timeout:
            break
    return True


def extract_pin_code(result):
    for center in result:
        pincode = center.get('pincode', '')
        center_name = center.get('name', '')
        logger.info(f"PINCODE: {pincode} and Name: {center_name}")
    webbrowser.open('https://www.cowin.gov.in/home')
    beep()
