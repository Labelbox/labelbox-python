import json
import os
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generic,
    Iterator,
    Optional,
    Tuple,
    TypeVar,
    Union,
)
import warnings

import requests
from pydantic import BaseModel

from labelbox.schema.task import Task
from labelbox.utils import _CamelCaseMixin

if TYPE_CHECKING:
    from labelbox import Client

OutputT = TypeVar("OutputT")


class StreamType(Enum):
    """The type of the stream."""

    RESULT = "RESULT"
    ERRORS = "ERRORS"


class Range(_CamelCaseMixin, BaseModel):  # pylint: disable=too-few-public-methods
    """Represents a range."""

    start: int
    end: int


class _MetadataHeader(_CamelCaseMixin, BaseModel):  # pylint: disable=too-few-public-methods
    total_size: int
    total_lines: int


class _MetadataFileInfo(_CamelCaseMixin, BaseModel):  # pylint: disable=too-few-public-methods
    offsets: Range
    lines: Range
    file: str


@dataclass
class _TaskContext:
    client: "Client"
    task_id: str
    stream_type: StreamType
    metadata_header: _MetadataHeader


class Converter(ABC, Generic[OutputT]):
    """Abstract class for transforming data."""

    @dataclass
    class ConverterInputArgs:
        """Input for the converter."""

        ctx: _TaskContext
        file_info: _MetadataFileInfo
        raw_data: str

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    @abstractmethod
    def convert(self, input_args: ConverterInputArgs) -> Iterator[OutputT]:
        """Converts the data.
        Returns an iterator that yields the converted data.

        Args:
            current_offset: The global offset indicating the position of the data within the
                            exported files. It represents a cumulative offset in characters
                            across multiple files.
            raw_data: The raw data to convert.

        Yields:
            Iterator[OutputT]: The converted data.
        """


class FileRetrieverStrategy(ABC):  # pylint: disable=too-few-public-methods
    """Abstract class for retrieving files."""

    def __init__(self, ctx: _TaskContext) -> None:
        super().__init__()
        self._ctx = ctx

    @abstractmethod
    def get_next_chunk(self) -> Optional[Tuple[_MetadataFileInfo, str]]:
        """Retrieves the file."""

    def _get_file_content(
        self, query: str, variables: dict, result_field_name: str
    ) -> Tuple[_MetadataFileInfo, str]:
        """Runs the query."""
        res = self._ctx.client.execute(query, variables, error_log_key="errors")
        res = res["task"][result_field_name]
        file_info = _MetadataFileInfo(**res) if res else None
        if not file_info:
            raise ValueError(
                f"Task {self._ctx.task_id} does not have a metadata file for the "
                f"{self._ctx.stream_type.value} stream"
            )
        response = requests.get(file_info.file, timeout=30)
        response.raise_for_status()
        response.encoding = "utf-8"
        assert (
            len(response.content)
            == file_info.offsets.end - file_info.offsets.start + 1
        ), (
            f"expected {file_info.offsets.end - file_info.offsets.start + 1} bytes, "
            f"got {len(response.content)} bytes"
        )
        return file_info, response.text


class _Reader(ABC):  # pylint: disable=too-few-public-methods
    """Abstract class for reading data from a source."""

    @abstractmethod
    def set_retrieval_strategy(self, strategy: FileRetrieverStrategy) -> None:
        """Sets the retrieval strategy."""

    @abstractmethod
    def read(self) -> Iterator[Tuple[_MetadataFileInfo, str]]:
        """Reads data from the source."""


class _BufferedFileRetrieverByOffset(FileRetrieverStrategy):  # pylint: disable=too-few-public-methods
    """Retrieves files by offset."""

    def __init__(
        self,
        ctx: _TaskContext,
        offset: int,
    ) -> None:
        super().__init__(ctx)
        self._current_offset = offset
        self._current_line = 0
        if self._current_offset >= self._ctx.metadata_header.total_size:
            raise ValueError(
                f"offset is out of range, max offset is {self._ctx.metadata_header.total_size - 1}"
            )

    def get_next_chunk(self) -> Optional[Tuple[_MetadataFileInfo, str]]:
        if self._current_offset >= self._ctx.metadata_header.total_size:
            return None
        query = (
            f"query GetExportFileFromOffsetPyApi"
            f"($where: WhereUniqueIdInput, $streamType: TaskStreamType!, $offset: UInt64!)"
            f"{{task(where: $where)"
            f"{{{'exportFileFromOffset'}(streamType: $streamType, offset: $offset)"
            f"{{offsets {{start end}} lines {{start end}} file}}"
            f"}}}}"
        )
        variables = {
            "where": {"id": self._ctx.task_id},
            "streamType": self._ctx.stream_type.value,
            "offset": str(self._current_offset),
        }
        file_info, file_content = self._get_file_content(
            query, variables, "exportFileFromOffset"
        )
        file_info.offsets.start = self._current_offset
        file_info.lines.start = self._current_line
        self._current_offset = file_info.offsets.end + 1
        self._current_line = file_info.lines.end + 1
        return file_info, file_content


class BufferedStream(Generic[OutputT]):
    """Streams data from a Reader."""

    def __init__(
        self,
        ctx: _TaskContext,
    ):
        self._ctx = ctx
        self._reader = _BufferedGCSFileReader()
        self._converter = _BufferedJsonConverter()
        self._reader.set_retrieval_strategy(
            _BufferedFileRetrieverByOffset(self._ctx, 0)
        )

    def __iter__(self):
        yield from self._fetch()

    def _fetch(
        self,
    ) -> Iterator[OutputT]:
        """Fetches the result data.
        Returns an iterator that yields the offset and the data.
        """
        if self._ctx.metadata_header.total_size is None:
            return

        stream = self._reader.read()
        with self._converter as converter:
            for file_info, raw_data in stream:
                for output in converter.convert(
                    Converter.ConverterInputArgs(self._ctx, file_info, raw_data)
                ):
                    yield output

    def start(
        self, stream_handler: Optional[Callable[[OutputT], None]] = None
    ) -> None:
        """Starts streaming the result data.
        Calls the stream_handler for each result.
        """
        # this calls the __iter__ method, which in turn calls the _fetch method
        for output in self:
            if stream_handler:
                stream_handler(output)


@dataclass
class BufferedJsonConverterOutput:
    """Output with the JSON object"""

    json: Any


class _BufferedJsonConverter(Converter[BufferedJsonConverterOutput]):
    """Converts JSON data in a buffered manner"""

    def convert(
        self, input_args: Converter.ConverterInputArgs
    ) -> Iterator[BufferedJsonConverterOutput]:
        yield BufferedJsonConverterOutput(json=json.loads(input_args.raw_data))


class _BufferedGCSFileReader(_Reader):
    """Reads data from multiple GCS files and buffer them to disk"""

    def __init__(self):
        super().__init__()
        self._retrieval_strategy = None

    def set_retrieval_strategy(self, strategy: FileRetrieverStrategy) -> None:
        """Sets the retrieval strategy."""
        self._retrieval_strategy = strategy

    def read(self) -> Iterator[Tuple[_MetadataFileInfo, str]]:
        if not self._retrieval_strategy:
            raise ValueError("retrieval strategy not set")
        # create a buffer
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
            result = self._retrieval_strategy.get_next_chunk()
            while result:
                _, raw_data = result
                # there is something wrong with the way the offsets are being calculated
                # so just write all of the chunks as is too the file, with pointer initially
                # pointed to the start of the file (like what is in GCS) and do not
                # rely on offsets for file location
                # temp_file.seek(file_info.offsets.start)
                temp_file.write(raw_data)
                result = self._retrieval_strategy.get_next_chunk()
        # read buffer
        with open(temp_file.name, "r") as temp_file_reopened:
            for idx, line in enumerate(temp_file_reopened):
                yield (
                    _MetadataFileInfo(
                        offsets=Range(start=0, end=len(line) - 1),
                        lines=Range(start=idx, end=idx + 1),
                        file=temp_file.name,
                    ),
                    line,
                )
        # manually delete buffer
        os.unlink(temp_file.name)


class ExportTask:
    """
    An adapter class for working with task objects, providing extended functionality
    and convenient access to task-related information.

    This class wraps a `Task` object, allowing you to interact with tasks of this type.
    It offers methods to retrieve task results, errors, and metadata, as well as properties
    for accessing task details such as UID, status, and creation time.
    """

    class ExportTaskException(Exception):
        """Raised when the task is not ready yet."""

    def __init__(self, task: Task, is_export_v2: bool = False) -> None:
        self._is_export_v2 = is_export_v2
        self._task = task

    def __repr__(self):
        return (
            f"<ExportTask ID: {self.uid}>"
            if getattr(self, "uid", None)
            else "<ExportTask>"
        )

    def __str__(self):
        properties_to_include = [
            "completion_percentage",
            "created_at",
            "metadata",
            "name",
            "result",
            "result_url",
            "errors",
            "errors_url",
            "status",
            "type",
            "uid",
            "updated_at",
        ]
        props = {prop: getattr(self, prop) for prop in properties_to_include}
        return f"<ExportTask {json.dumps(props, indent=4, default=str)}>"

    def __eq__(self, other):
        return self._task.__eq__(other)

    def __hash__(self):
        return self._task.__hash__()

    @property
    def uid(self):
        """Returns the uid of the task."""
        return self._task.uid

    @property
    def deleted(self):
        """Returns whether the task is deleted."""
        return self._task.deleted

    @property
    def updated_at(self):
        """Returns the last time the task was updated."""
        return self._task.updated_at

    @property
    def created_at(self):
        """Returns the time the task was created."""
        return self._task.created_at

    @property
    def name(self):
        """Returns the name of the task."""
        return self._task.name

    @property
    def status(self):
        """Returns the status of the task."""
        return self._task.status

    @property
    def metadata(self):
        """Returns the metadata of the task."""
        return self._task.metadata

    @property
    def result_url(self):
        """Returns the result URL of the task."""
        if not self._is_export_v2:
            raise ExportTask.ExportTaskException(
                "This property is only available for export_v2 tasks due to compatibility reasons, please use streamable errors instead"
            )
        base_url = self._task.client.rest_endpoint
        return (
            base_url
            + "/export-results/"
            + self._task.uid
            + "/"
            + self._task.client.get_organization().uid
        )

    @property
    def errors_url(self):
        """Returns the errors URL of the task."""
        if not self._is_export_v2:
            raise ExportTask.ExportTaskException(
                "This property is only available for export_v2 tasks due to compatibility reasons, please use streamable errors instead"
            )
        if not self.has_errors():
            return None
        base_url = self._task.client.rest_endpoint
        return (
            base_url
            + "/export-errors/"
            + self._task.uid
            + "/"
            + self._task.client.get_organization().uid
        )

    @property
    def errors(self):
        """Returns the errors of the task."""
        if not self._is_export_v2:
            raise ExportTask.ExportTaskException(
                "This property is only available for export_v2 tasks due to compatibility reasons, please use streamable errors instead"
            )
        if self.status == "FAILED":
            raise ExportTask.ExportTaskException("Task failed")
        if self.status != "COMPLETE":
            raise ExportTask.ExportTaskException("Task is not ready yet")

        if not self.has_errors():
            return None

        data = []

        metadata_header = ExportTask._get_metadata_header(
            self._task.client, self._task.uid, StreamType.ERRORS
        )
        if metadata_header is None:
            return None
        BufferedStream(
            _TaskContext(
                self._task.client,
                self._task.uid,
                StreamType.ERRORS,
                metadata_header,
            ),
        ).start(stream_handler=lambda output: data.append(output.json))
        return data

    @property
    def result(self):
        """Returns the result of the task."""
        if self._is_export_v2:
            if self.status == "FAILED":
                raise ExportTask.ExportTaskException("Task failed")
            if self.status != "COMPLETE":
                raise ExportTask.ExportTaskException("Task is not ready yet")
            data = []

            metadata_header = ExportTask._get_metadata_header(
                self._task.client, self._task.uid, StreamType.RESULT
            )
            if metadata_header is None:
                return []
            BufferedStream(
                _TaskContext(
                    self._task.client,
                    self._task.uid,
                    StreamType.RESULT,
                    metadata_header,
                ),
            ).start(stream_handler=lambda output: data.append(output.json))
            return data
        return self._task.result_url

    @property
    def completion_percentage(self):
        """Returns the completion percentage of the task."""
        return self._task.completion_percentage

    @property
    def type(self):
        """Returns the type of the task."""
        return self._task.type

    @property
    def created_by(self):
        """Returns the user who created the task."""
        return self._task.created_by

    @property
    def organization(self):
        """Returns the organization of the task."""
        return self._task.organization

    def wait_until_done(self, timeout_seconds: int = 7200) -> None:
        warnings.warn(
            "The method wait_until_done for ExportTask is deprecated and will be removed in the next major release. Use the wait_till_done method instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.wait_till_done(timeout_seconds)

    def wait_till_done(self, timeout_seconds: int = 7200) -> None:
        """Waits until the task is done."""
        return self._task.wait_till_done(timeout_seconds)

    @staticmethod
    @lru_cache(maxsize=5)
    def _get_metadata_header(
        client, task_id: str, stream_type: StreamType
    ) -> Union[_MetadataHeader, None]:
        """Returns the total file size for a specific task."""
        query = (
            f"query GetExportMetadataHeaderPyApi"
            f"($where: WhereUniqueIdInput, $streamType: TaskStreamType!)"
            f"{{task(where: $where)"
            f"{{{'exportMetadataHeader'}(streamType: $streamType)"
            f"{{totalSize totalLines}}"
            f"}}}}"
        )
        variables = {"where": {"id": task_id}, "streamType": stream_type.value}
        res = client.execute(query, variables, error_log_key="errors")
        res = res["task"]["exportMetadataHeader"]
        return _MetadataHeader(**res) if res else None

    def get_total_file_size(self, stream_type: StreamType) -> Union[int, None]:
        """Returns the total file size for a specific task."""
        if self._task.status == "FAILED":
            raise ExportTask.ExportTaskException("Task failed")
        if self._task.status != "COMPLETE":
            raise ExportTask.ExportTaskException("Task is not ready yet")
        header = ExportTask._get_metadata_header(
            self._task.client, self._task.uid, stream_type
        )
        return header.total_size if header else None

    def get_total_lines(self, stream_type: StreamType) -> Union[int, None]:
        """Returns the total file size for a specific task."""
        if self._task.status == "FAILED":
            raise ExportTask.ExportTaskException("Task failed")
        if self._task.status != "COMPLETE":
            raise ExportTask.ExportTaskException("Task is not ready yet")
        header = ExportTask._get_metadata_header(
            self._task.client, self._task.uid, stream_type
        )
        return header.total_lines if header else None

    def has_result(self) -> bool:
        """Returns whether the task has a result."""
        total_size = self.get_total_file_size(StreamType.RESULT)
        return total_size is not None and total_size > 0

    def has_errors(self) -> bool:
        """Returns whether the task has errors."""
        total_size = self.get_total_file_size(StreamType.ERRORS)
        return total_size is not None and total_size > 0

    def get_buffered_stream(
        self,
        stream_type: StreamType = StreamType.RESULT,
    ) -> BufferedStream:
        """
        Returns the result of the task.

        Args:
            stream_type (StreamType, optional): The type of stream to retrieve. Defaults to StreamType.RESULT.

        Returns:
            Stream: The buffered stream object.

        Raises:
            ExportTask.ExportTaskException: If the task has failed or is not ready yet.
            ValueError: If the task does not have the specified stream type.
        """
        if self._task.status == "FAILED":
            raise ExportTask.ExportTaskException("Task failed")
        if self._task.status != "COMPLETE":
            raise ExportTask.ExportTaskException("Task is not ready yet")

        metadata_header = self._get_metadata_header(
            self._task.client, self._task.uid, stream_type
        )
        if metadata_header is None:
            raise ValueError(
                f"Task {self._task.uid} does not have a {stream_type.value} stream"
            )
        return BufferedStream(
            _TaskContext(
                self._task.client, self._task.uid, stream_type, metadata_header
            ),
        )

    @staticmethod
    def get_task(client, task_id):
        """Returns the task with the given id."""
        return ExportTask(Task.get_task(client, task_id))
