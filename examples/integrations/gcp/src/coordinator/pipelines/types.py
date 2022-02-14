from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum

import docker
import logging

logger = logging.getLogger("uvicorn")

DOCKER_CLIENT = docker.from_env()


class JobState(Enum):
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'


@dataclass
class JobStatus:
    state: JobState
    result: Dict[str, Any] = field(default_factory=dict)
    errors: Optional[str] = None


class Job(ABC):

    @abstractmethod
    def run_local(self, json_data: Dict[str, Any]):
        ...

    @abstractmethod
    def run_remote(self, *args, **kwargs):
        ...


class Pipeline(Job):

    @abstractmethod
    def parse_args(self, json_data: Dict[str, Any]):
        ...


class CustomJob(Job):
    """
    Base class for coordinator jobs
    """

    def __init__(self, name, local_container_name: str, max_run_time=600):
        self.name = name
        self.local_container_name = local_container_name
        self.max_run_time = max_run_time

    def _run_local(
            self,
            cmd: Optional[List[str]] = None,
            env_vars: Optional[List[str]] = None,
            volumes: Optional[Dict[str, Dict[str, str]]] = None) -> JobStatus:

        logger.info(f"Running container: `{self.local_container_name}`")
        container = DOCKER_CLIENT.containers.run(self.local_container_name,
                                                 cmd or [],
                                                 detach=True,
                                                 stream=True,
                                                 environment=env_vars or [],
                                                 volumes=volumes or {})

        for log in container.logs(stream=True):
            logger.info("[%s]: %s" % (self.name, log.decode('utf-8')))
        res = container.wait()
        logger.info("STATUS: %s", str(res))
        if res['StatusCode'] == 0:
            return JobStatus(state=JobState.SUCCESS)
        else:
            logger.error("[%s]: Job Failed")
            errors = ""
            for log in container.logs(stderr=True, stdout=False, stream=True):
                error = log.decode('utf-8').strip()
                errors += error + "\n"
                logger.error("[%s]: %s" % (self.name, error))
            return JobStatus(state=JobState.FAILED, errors=errors)

    def run_remote(self):
        # Vertex requires a lot of one time config.
        # We might want to create a separate config file and load that in
        raise NotImplementedError("")
