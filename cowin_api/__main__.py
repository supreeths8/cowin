import pyfiglet
import logging
import jmespath

from api import CoWinAPI

logger = logging.getLogger(__name__)
logging.basicConfig(format="%(threadName)s:%(message)s")
logger.setLevel(logging.INFO)


def main():
    logger.info("Hello")
    api = CoWinAPI()
    states_dict = api.get_states()
    kar_state_id = jmespath.search("states[?state_name==`Karnataka`].[state_id] | [0]", states_dict)[0]
    logger.info(f"Karnataka State Id: {kar_state_id}")
    districts = api.get_districts(kar_state_id)
    wanted_districts_map = jmespath.search("districts[?district_name==`Bangalore Urban` || district_name==`BBMP`]", districts)
    api.get_availability_by_base_multi_threaded(
        caller='district', areas=wanted_districts_map, date='1-06-2021', min_age_limt=18, dose_number='1')


if __name__ == "__main__":
    print(pyfiglet.figlet_format("COWIN PLUS 0.1"))
    main()
