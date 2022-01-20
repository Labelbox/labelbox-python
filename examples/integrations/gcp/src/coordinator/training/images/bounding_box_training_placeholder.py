from time import sleep
import os
import logging
from job import Job

logger = logging.getLogger(__name__)


class BoundingBoxTraining(Job):

    def run_local(self, training_data_uri):
        sleep(1)
        logger.info("Training complete")

    def run_remote(self, training_data_uri):
        ...
