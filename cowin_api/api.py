import concurrent.futures
import logging
import time

from typing import Union, List

from cowin_api.utils import extract_pin_code
from cowin_api.base_api import BaseApi
from cowin_api.constants import Constants
from cowin_api.utils import today, filter_centers_by_age_limit, beep


logger = logging.getLogger(__name__)
logging.basicConfig(format="%(threadName)s:     %(message)s")
logger.setLevel(logging.INFO)


class CoWinAPI(BaseApi):
    def __init__(self):
        self.area_type = None
        self.base_url = None
        self.found = False

    def get_states(self):
        logger.info("Getting states...")
        url = Constants.states_list_url
        return self._call_api(url)

    def get_districts(self, state_id: str):
        url = f"{Constants.districts_list_url}/{state_id}"
        return self._call_api(url)

    def get_availability_by_base(self, caller: str,
                                 areas: Union[str, List[str]],
                                 date: str, min_age_limt: int):
        """this function is called by the get availability function
        this is separated out so that the parent functions have the same
        structure and development becomes easier"""
        area_type, base_url = 'pincode', Constants.availability_by_pin_code_url
        if caller == 'district':
            area_type, base_url = 'district_id', Constants.availability_by_district_url
        # if the areas is a str, convert to list
        if isinstance(areas, str):
            areas = [areas]
        # make a separate call for each of the areas
        results = []
        for area_id in areas:
            url = f"{base_url}?{area_type}={area_id}&date={date}"
            if min_age_limt:
                curr_result = filter_centers_by_age_limit(self._call_api(url),
                                                          min_age_limt)
            else:
                curr_result = self._call_api(url)
            # append
            if curr_result:
                results += curr_result['centers']

        # return the results in the same format as returned by the api
        return {'centers': results}

    def get_availability_by_district(self, district_id: Union[str, List[str]],
                                     date: str = today(),
                                     min_age_limt: int = None):
        return self.get_availability_by_base(caller='district', areas=district_id,
                                             date=date, min_age_limt=min_age_limt)

    def get_availability_by_pincode(self, pin_code: Union[str, List[str]],
                                    date: str = today(),
                                    min_age_limt: int = None):
        return self.get_availability_by_base(caller='pincode', areas=pin_code,
                                             date=date, min_age_limt=min_age_limt)

    def get_availability_by_base_multi_threaded(self, caller: str,
                                                areas: List[str],
                                                date: str, min_age_limt: int, dose_number: str):
        """this function is called by the get availability function
        this is separated out so that the parent functions have the same
        structure and development becomes easier"""
        self.area_type, self.base_url = 'pincode', Constants.availability_by_pin_code_url
        if caller == 'district':
            self.area_type, self.base_url = 'district_id', Constants.availability_by_district_url
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            result = [executor.submit(self.poll_availability_with_age_limit,  area, min_age_limt, date, dose_number)
                      for area in areas]

            for f in concurrent.futures.as_completed(result):
                if f.result() is not None:
                    self.found = True
                    extract_pin_code(f.result())
                    executor.shutdown(wait=False)
        # return the results in the same format as returned by the api
        return {'centers': results}

    def poll_availability_with_age_limit(self, district_map, min_age_limit, date, dose_number):
        district_id = district_map['district_id']
        district_name = district_map['district_name']
        logger.info(f"Area: {district_name}")
        url = f"{self.base_url}?{self.area_type}={district_id}&date={date}"
        while True:
            curr_result = filter_centers_by_age_limit(centers=self._call_api(url),
                                                      min_age_limit=min_age_limit, dose_number=dose_number)
            # curr_result = self._call_api(url)
            if len(curr_result['centers']) > 0:
                break
            time.sleep(3)
            if self.found:
                return None
            logger.info(f"{[time.asctime(time.localtime(time.time()))]}:    "
                        f"Checking for appointments in {district_name}")
        logger.info(f"Available centers: {len(curr_result['centers'])}")
        return curr_result['centers']
