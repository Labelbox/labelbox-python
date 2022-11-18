from labelbox_dev import entEnity

from collections import namedtuple

from pydantic import NoneStr
sys.path.append("/Users/olegtrygub/src/labelbox-python")
import labelbox

from labelbox.client import Client
from labelbox.utils import camel_case

from typing import Optional

from time import time

client = labelbox.Client(
                api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJjbDh1dHpxMm8wMDBieHBwMTR0a2o4ZWJzIiwib3JnYW5pemF0aW9uSWQiOiJjbDh1dHpxMXAwMDBheHBwMWNrdHhod3p0IiwiYXBpS2V5SWQiOiJjbDh1dTB4b2YwMDBleHBwMWQwcmMweDhsIiwic2VjcmV0IjoiMmExNDQ4NGZmZmIzMjQyNzk0ZTNlNmIwOTRkMDY3OWYiLCJpYXQiOjE2NjQ5MjYxMjIsImV4cCI6MjI5NjA3ODEyMn0.cqtxIEKVY1GPAQjyqQ8VrbMGkUywx-IwC9BGkCi8ahU",
                endpoint = 'http://localhost:8080/graphql', 
                app_url="localhost:3000"
            )


class BaseObject:
    def create_from_json(self):
        pass


class DataRowInfo(Entity):
    def __init__(self):
        self.data_row_id = None
        self.globalkey = None

class DataRowAssignment(Entity):
    pass

class BaseError(BaseObject):
    def __init__(self, message):
        self.message = message




TASK_ID_KEY = 'jobID'
TASK_STATUS_KEY = 'jobStatus'
TOTAL_PAGES_KEY = 'totalPage'
PAGE_NUMBER_KEY = 'pageNumber'
DATA_KEY = 'data'
DEFAULT_QUERY = ''
DEFAULT_QUERY_NAME = ''


DEFAULT_PAGE_SCHEMA = {}





def get_data_row_ids_for_globaleys(globalkeys):
    pass


def assign_global_keys_to_data_rows(global_key_to_data_row_inputs: List[Dict[str, str]], timeout_seconds=60) -> Dict[str, Union[str, List[Any]]]:
    pass

if __name__ == "__main__":



    PATTERN = "gs://labelbox-datasets/coco_dataset/train2017/00000000{}.jpg-1"
    gks = [PATTERN.format(num ) for num in range(1006, 1300)]
    dr_gk_ids = client.get_data_row_ids_for_global_keys(gks, timeout_seconds=4)
    print(dr_gk_ids.keys())



