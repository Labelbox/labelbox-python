from typing import List, Optional, Dict
from abc import ABC, abstractmethod

import docker
import logging
from enum import Enum

logger = logging.getLogger("uvicorn")


class JobStatus(Enum):
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'


class Job(ABC):

    @abstractmethod
    def run_local(self, *args, **kwargs):
        ...

    @abstractmethod
    def run_remote(self, *args, **kwargs):
        ...


class CustomJob(Job):
    """
    Base class for coordinator jobs

    """

    def __init__(self, name, container_name, max_run_time=600):
        self.name = name
        self.container_name = container_name
        self.max_run_time = max_run_time

    def run_local(
            self,
            docker_client: docker.DockerClient,
            cmd: Optional[List[str]] = None,
            env_vars: Optional[List[str]] = None,
            volumes: Optional[Dict[str, Dict[str, str]]] = None) -> JobStatus:

        logger.info("Starting gcp_bounding_box_etl container locally")
        container = docker_client.containers.run(self.container_name,
                                                 cmd or [],
                                                 detach=True,
                                                 stream=True,
                                                 environment=env_vars or [],
                                                 volumes=volumes or {})

        for log in container.logs(stream=True):
            logger.info("[%s]: %s" % (self.name, log.decode('utf-8')))
        res = container.wait()
        # TODO: Maybe we just raise an exception if the job failed?
        logger.info("STATUS: %s", str(res))
        if res['StatusCode'] == 0:
            return JobStatus.SUCCESS
        else:
            logger.error("[%s]: Job Failed")
            for log in container.logs(stderr=True, stdout=False, stream=True):
                logger.error("[%s]: %s" %
                             (self.name, log.decode('utf-8').strip()))

            # We might want to return the errors
            return JobStatus.FAILED

    def run_remote(self):
        # Vertex requires a lot of one time config.
        # We might want to create a separate config file and load that in
        raise NotImplementedError("")
