from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum

import docker
import logging

logger = logging.getLogger("uvicorn")


class JobState(Enum):
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'


@dataclass
class JobStatus:
    state: JobState
    result: Dict[str, Any] = field(default_factory=dict)
    errors: Optional[str] = None


class Job(ABC):
    ...

    #def run_local(self, json_data: Dict[str, Any]):
    #    ...

    #def run_remote(self, *args, **kwargs):
    #    ...


class Pipeline(Job):
    ...

    #@abstractmethod
    #def parse_args(self, json_data: Dict[str, Any]):
    #    ...
