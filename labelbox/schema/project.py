import json
import logging
import time
import warnings
from collections import namedtuple
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Union
from urllib.parse import urlparse

import requests

from labelbox import parser
from labelbox import utils
from labelbox.exceptions import (InvalidQueryError, LabelboxError,
                                 ProcessingWaitTimeout, ResourceConflict,
                                 ResourceNotFoundError)
from labelbox.orm import query
from labelbox.orm.db_object import DbObject, Deletable, Updateable
from labelbox.orm.model import Entity, Field, Relationship
from labelbox.pagination import PaginatedCollection
from labelbox.schema.consensus_settings import ConsensusSettings
from labelbox.schema.create_batches_task import CreateBatchesTask
from labelbox.schema.data_row import DataRow
from labelbox.schema.export_filters import ProjectExportFilters, validate_datetime, build_filters
from labelbox.schema.export_params import ProjectExportParams
from labelbox.schema.media_type import MediaType
from labelbox.schema.queue_mode import QueueMode
from labelbox.schema.resource_tag import ResourceTag
from labelbox.schema.task import Task
from labelbox.schema.task_queue import TaskQueue
from labelbox.schema.user import User

if TYPE_CHECKING:
    from labelbox import BulkImportRequest

try:
    datetime.fromisoformat  # type: ignore[attr-defined]
except AttributeError:
    from backports.datetime_fromisoformat import MonkeyPatch

    MonkeyPatch.patch_fromisoformat()

try:
    from labelbox.data.serialization import LBV1Converter
except ImportError:
    pass

logger = logging.getLogger(__name__)


class Project(DbObject, Updateable, Deletable):
    """ A Project is a container that includes a labeling frontend, an ontology,
    datasets and labels.

    Attributes:
        name (str)
        description (str)
        updated_at (datetime)
        created_at (datetime)
        setup_complete (datetime)
        last_activity_time (datetime)
        queue_mode (string)
        auto_audit_number_of_labels (int)
        auto_audit_percentage (float)

        datasets (Relationship): `ToMany` relationship to Dataset
        created_by (Relationship): `ToOne` relationship to User
        organization (Relationship): `ToOne` relationship to Organization
        labeling_frontend (Relationship): `ToOne` relationship to LabelingFrontend
        labeling_frontend_options (Relationship): `ToMany` relationship to LabelingFrontendOptions
        labeling_parameter_overrides (Relationship): `ToMany` relationship to LabelingParameterOverride
        webhooks (Relationship): `ToMany` relationship to Webhook
        benchmarks (Relationship): `ToMany` relationship to Benchmark
        ontology (Relationship): `ToOne` relationship to Ontology
        task_queues (Relationship): `ToMany` relationship to TaskQueue
    """

    name = Field.String("name")
    description = Field.String("description")
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    setup_complete = Field.DateTime("setup_complete")
    last_activity_time = Field.DateTime("last_activity_time")
    queue_mode = Field.Enum(QueueMode, "queue_mode")
    auto_audit_number_of_labels = Field.Int("auto_audit_number_of_labels")
    auto_audit_percentage = Field.Float("auto_audit_percentage")
    # Bind data_type and allowedMediaTYpe using the GraphQL type MediaType
    media_type = Field.Enum(MediaType, "media_type", "allowedMediaType")

    # Relationships
    datasets = Relationship.ToMany(
        "Dataset",
        True,
        deprecation_warning=
        "This method does not return any data for batch-based projects and it will be deprecated on or around November 1, 2023."
    )
    created_by = Relationship.ToOne("User", False, "created_by")
    organization = Relationship.ToOne("Organization", False)
    labeling_frontend = Relationship.ToOne("LabelingFrontend")
    labeling_frontend_options = Relationship.ToMany(
        "LabelingFrontendOptions", False, "labeling_frontend_options")
    labeling_parameter_overrides = Relationship.ToMany(
        "LabelingParameterOverride", False, "labeling_parameter_overrides")
    webhooks = Relationship.ToMany("Webhook", False)
    benchmarks = Relationship.ToMany("Benchmark", False)
    ontology = Relationship.ToOne("Ontology", True)

    #
    _wait_processing_max_seconds = 3600

    def update(self, **kwargs):
        """ Updates this project with the specified attributes

        Args:
            kwargs: a dictionary containing attributes to be upserted

        Note that the queue_mode cannot be changed after a project has been created.

        Additionally, the quality setting cannot be changed after a project has been created. The quality mode
        for a project is inferred through the following attributes:

        Benchmark:
            auto_audit_number_of_labels = 1 and auto_audit_percentage = 1.0

        Consensus:
            auto_audit_number_of_labels > 1 or auto_audit_percentage <= 1.0

        Attempting to switch between benchmark and consensus modes is an invalid operation and will result
        in an error.
        """

        media_type = kwargs.get("media_type")
        if media_type:
            if MediaType.is_supported(media_type):
                kwargs["media_type"] = media_type.value
            else:
                raise TypeError(f"{media_type} is not a valid media type. Use"
                                f" any of {MediaType.get_supported_members()}"
                                " from MediaType. Example: MediaType.Image.")

        return super().update(**kwargs)

    def members(self) -> PaginatedCollection:
        """ Fetch all current members for this project

        Returns:
            A `PaginatedCollection` of `ProjectMember`s

        """
        id_param = "projectId"
        query_str = """query ProjectMemberOverviewPyApi($%s: ID!) {
             project(where: {id : $%s}) { id members(skip: %%d first: %%d){ id user { %s } role { id name } accessFrom }
           }
        }""" % (id_param, id_param, query.results_query_part(Entity.User))
        return PaginatedCollection(self.client, query_str,
                                   {id_param: str(self.uid)},
                                   ["project", "members"], ProjectMember)

    def update_project_resource_tags(
            self, resource_tag_ids: List[str]) -> List[ResourceTag]:
        """ Creates project resource tags

        Args:
            resource_tag_ids
        Returns:
            a list of ResourceTag ids that was created.
        """
        project_id_param = "projectId"
        tag_ids_param = "resourceTagIds"

        query_str = """mutation UpdateProjectResourceTagsPyApi($%s:ID!,$%s:[String!]) {
            project(where:{id:$%s}){updateProjectResourceTags(input:{%s:$%s}){%s}}}""" % (
            project_id_param, tag_ids_param, project_id_param, tag_ids_param,
            tag_ids_param, query.results_query_part(ResourceTag))

        res = self.client.execute(query_str, {
            project_id_param: self.uid,
            tag_ids_param: resource_tag_ids
        })

        return [
            ResourceTag(self.client, tag)
            for tag in res["project"]["updateProjectResourceTags"]
        ]

    def labels(self, datasets=None, order_by=None) -> PaginatedCollection:
        """ Custom relationship expansion method to support limited filtering.

        Args:
            datasets (iterable of Dataset): Optional collection of Datasets
                whose Labels are sought. If not provided, all Labels in
                this Project are returned.
            order_by (None or (Field, Field.Order)): Ordering clause.
        """
        Label = Entity.Label

        if datasets is not None:
            where = " where:{dataRow: {dataset: {id_in: [%s]}}}" % ", ".join(
                '"%s"' % dataset.uid for dataset in datasets)
        else:
            where = ""

        if order_by is not None:
            query.check_order_by_clause(Label, order_by)
            order_by_str = "orderBy: %s_%s" % (order_by[0].graphql_name,
                                               order_by[1].name.upper())
        else:
            order_by_str = ""

        id_param = "projectId"
        query_str = """query GetProjectLabelsPyApi($%s: ID!)
            {project (where: {id: $%s})
                {labels (skip: %%d first: %%d %s %s) {%s}}}""" % (
            id_param, id_param, where, order_by_str,
            query.results_query_part(Label))

        return PaginatedCollection(self.client, query_str, {id_param: self.uid},
                                   ["project", "labels"], Label)

    def export_queued_data_rows(
            self,
            timeout_seconds=120,
            include_metadata: bool = False) -> List[Dict[str, str]]:
        """ Returns all data rows that are currently enqueued for this project.

        Args:
            timeout_seconds (float): Max waiting time, in seconds.
            include_metadata (bool): True to return related DataRow metadata
        Returns:
            Data row fields for all data rows in the queue as json
        Raises:
            LabelboxError: if the export fails or is unable to download within the specified time.
        """
        warnings.warn(
            "You are currently utilizing exports v1 for this action, which will be deprecated after December 31st, 2023. We recommend transitioning to exports v2. To view export v2 details, visit our docs: https://docs.labelbox.com/reference/label-export",
            DeprecationWarning)
        id_param = "projectId"
        metadata_param = "includeMetadataInput"
        query_str = """mutation GetQueuedDataRowsExportUrlPyApi($%s: ID!, $%s: Boolean!)
            {exportQueuedDataRows(data:{projectId: $%s , includeMetadataInput: $%s}) {downloadUrl createdAt status} }
        """ % (id_param, metadata_param, id_param, metadata_param)
        sleep_time = 2
        start_time = time.time()
        while True:
            res = self.client.execute(query_str, {
                id_param: self.uid,
                metadata_param: include_metadata
            })
            res = res["exportQueuedDataRows"]
            if res["status"] == "COMPLETE":
                download_url = res["downloadUrl"]
                response = requests.get(download_url)
                response.raise_for_status()
                return parser.loads(response.text)
            elif res["status"] == "FAILED":
                raise LabelboxError("Data row export failed.")

            current_time = time.time()
            if current_time - start_time > timeout_seconds:
                raise LabelboxError(
                    f"Unable to export data rows within {timeout_seconds} seconds."
                )

            logger.debug(
                "Project '%s' queued data row export, waiting for server...",
                self.uid)
            time.sleep(sleep_time)

    def label_generator(self, timeout_seconds=600, **kwargs):
        """
        Download text and image annotations, or video annotations.

        For a mixture of text/image and video, use project.export_labels()

        Returns:
            LabelGenerator for accessing labels
        """
        _check_converter_import()
        json_data = self.export_labels(download=True,
                                       timeout_seconds=timeout_seconds,
                                       **kwargs)

        # assert that the instance this would fail is only if timeout runs out
        assert isinstance(
            json_data,
            List), "Unable to successfully get labels. Please try again"

        if json_data is None:
            raise TimeoutError(
                f"Unable to download labels in {timeout_seconds} seconds."
                "Please try again or contact support if the issue persists.")

        is_video = [
            "frames" in row["Label"]
            for row in json_data
            if row["Label"] and not row["Skipped"]
        ]

        if len(is_video) and not all(is_video) and any(is_video):
            raise ValueError(
                "Found mixed data types of video and text/image. "
                "Use project.export_labels() to export projects with mixed data types. "
            )
        if len(is_video) and all(is_video):
            # Filter skipped labels to avoid inference errors
            json_data = [
                label for label in self.export_labels(download=True)
                if not label["Skipped"]
            ]

            return LBV1Converter.deserialize_video(json_data, self.client)

        return LBV1Converter.deserialize(json_data)

    def export_labels(self,
                      download=False,
                      timeout_seconds=1800,
                      **kwargs) -> Optional[Union[str, List[Dict[Any, Any]]]]:
        """ Calls the server-side Label exporting that generates a JSON
        payload, and returns the URL to that payload.

        Will only generate a new URL at a max frequency of 30 min.

        Args:
            download (bool): Returns the url if False
            timeout_seconds (float): Max waiting time, in seconds.
            start (str): Earliest date for labels, formatted "YYYY-MM-DD" or "YYYY-MM-DD hh:mm:ss"
            end (str): Latest date for labels, formatted "YYYY-MM-DD" or "YYYY-MM-DD hh:mm:ss"
            last_activity_start (str): Will include all labels that have had any updates to
              data rows, issues, comments, metadata, or reviews since this timestamp.
              formatted "YYYY-MM-DD" or "YYYY-MM-DD hh:mm:ss"
            last_activity_end (str): Will include all labels that do not have any updates to
              data rows, issues, comments, metadata, or reviews after this timestamp.
              formatted "YYYY-MM-DD" or "YYYY-MM-DD hh:mm:ss"

        Returns:
            URL of the data file with this Project's labels. If the server didn't
            generate during the `timeout_seconds` period, None is returned.
        """
        warnings.warn(
            "You are currently utilizing exports v1 for this action, which will be deprecated after December 31st, 2023. We recommend transitioning to exports v2. To view export v2 details, visit our docs: https://docs.labelbox.com/reference/label-export",
            DeprecationWarning)

        def _string_from_dict(dictionary: dict, value_with_quotes=False) -> str:
            """Returns a concatenated string of the dictionary's keys and values

            The string will be formatted as {key}: 'value' for each key. Value will be inclusive of
            quotations while key will not. This can be toggled with `value_with_quotes`"""

            quote = "\"" if value_with_quotes else ""
            return ",".join([
                f"""{c}: {quote}{dictionary.get(c)}{quote}"""
                for c in dictionary
                if dictionary.get(c)
            ])

        sleep_time = 2
        id_param = "projectId"
        filter_param = ""
        filter_param_dict = {}

        if "start" in kwargs or "end" in kwargs:
            created_at_dict = {
                "start": kwargs.get("start", ""),
                "end": kwargs.get("end", "")
            }
            [validate_datetime(date) for date in created_at_dict.values()]
            filter_param_dict["labelCreatedAt"] = "{%s}" % _string_from_dict(
                created_at_dict, value_with_quotes=True)

        if "last_activity_start" in kwargs or "last_activity_end" in kwargs:
            last_activity_start = kwargs.get('last_activity_start')
            last_activity_end = kwargs.get('last_activity_end')

            if last_activity_start:
                validate_datetime(str(last_activity_start))
            if last_activity_end:
                validate_datetime(str(last_activity_end))

            filter_param_dict["lastActivityAt"] = "{%s}" % _string_from_dict(
                {
                    "start": last_activity_start,
                    "end": last_activity_end
                },
                value_with_quotes=True)

        if filter_param_dict:
            filter_param = """, filters: {%s }""" % (_string_from_dict(
                filter_param_dict, value_with_quotes=False))

        query_str = """mutation GetLabelExportUrlPyApi($%s: ID!)
            {exportLabels(data:{projectId: $%s%s}) {downloadUrl createdAt shouldPoll} }
        """ % (id_param, id_param, filter_param)

        start_time = time.time()

        while True:
            res = self.client.execute(query_str, {id_param: self.uid})
            res = res["exportLabels"]
            if not res["shouldPoll"] and res["downloadUrl"] is not None:
                url = res['downloadUrl']
                if not download:
                    return url
                else:
                    response = requests.get(url)
                    response.raise_for_status()
                    return response.json()

            current_time = time.time()
            if current_time - start_time > timeout_seconds:
                return None

            logger.debug("Project '%s' label export, waiting for server...",
                         self.uid)
            time.sleep(sleep_time)

    def export_v2(self,
                  task_name: Optional[str] = None,
                  filters: Optional[ProjectExportFilters] = None,
                  params: Optional[ProjectExportParams] = None) -> Task:
        """
        Creates a project export task with the given params and returns the task.

        For more information visit: https://docs.labelbox.com/docs/exports-v2#export-from-a-project-python-sdk
        
        >>>     task = project.export_v2(
        >>>         filters={
        >>>             "last_activity_at": ["2000-01-01 00:00:00", "2050-01-01 00:00:00"],
        >>>             "label_created_at": ["2000-01-01 00:00:00", "2050-01-01 00:00:00"],
        >>>             "data_row_ids": [DATA_ROW_ID_1, DATA_ROW_ID_2, ...] # or global_keys: [DATA_ROW_GLOBAL_KEY_1, DATA_ROW_GLOBAL_KEY_2, ...]   
        >>>             "batch_ids": [BATCH_ID_1, BATCH_ID_2, ...]
        >>>         },
        >>>         params={
        >>>             "performance_details": False,
        >>>             "label_details": True
        >>>         })
        >>>     task.wait_till_done()
        >>>     task.result
        """

        _params = params or ProjectExportParams({
            "attachments": False,
            "metadata_fields": False,
            "data_row_details": False,
            "project_details": False,
            "performance_details": False,
            "label_details": False,
            "media_type_override": None,
            "interpolated_frames": False,
        })

        _filters = filters or ProjectExportFilters({
            "last_activity_at": None,
            "label_created_at": None,
            "data_row_ids": None,
            "global_keys": None,
            "batch_ids": None,
            "workflow_status": None
        })

        mutation_name = "exportDataRowsInProject"
        create_task_query_str = """mutation exportDataRowsInProjectPyApi($input: ExportDataRowsInProjectInput!){
          %s(input: $input) {taskId} }
          """ % (mutation_name)

        media_type_override = _params.get('media_type_override', None)
        query_params: Dict[str, Any] = {
            "input": {
                "taskName": task_name,
                "filters": {
                    "projectId": self.uid,
                    "searchQuery": {
                        "scope": None,
                        "query": [],
                    }
                },
                "params": {
                    "mediaTypeOverride":
                        media_type_override.value
                        if media_type_override is not None else None,
                    "includeAttachments":
                        _params.get('attachments', False),
                    "includeMetadata":
                        _params.get('metadata_fields', False),
                    "includeDataRowDetails":
                        _params.get('data_row_details', False),
                    "includeProjectDetails":
                        _params.get('project_details', False),
                    "includePerformanceDetails":
                        _params.get('performance_details', False),
                    "includeLabelDetails":
                        _params.get('label_details', False),
                    "includeInterpolatedFrames":
                        _params.get('interpolated_frames', False),
                },
            }
        }

        search_query = build_filters(self.client, _filters)
        query_params["input"]["filters"]["searchQuery"]["query"] = search_query

        res = self.client.execute(create_task_query_str,
                                  query_params,
                                  error_log_key="errors")
        res = res[mutation_name]
        task_id = res["taskId"]
        user: User = self.client.get_user()
        tasks: List[Task] = list(
            user.created_tasks(where=Entity.Task.uid == task_id))
        # Cache user in a private variable as the relationship can't be
        # resolved due to server-side limitations (see Task.created_by)
        # for more info.
        if len(tasks) != 1:
            raise ResourceNotFoundError(Entity.Task, task_id)
        task: Task = tasks[0]
        task._user = user
        return task

    def export_issues(self, status=None) -> str:
        """ Calls the server-side Issues exporting that
        returns the URL to that payload.

        Args:
            status (string): valid values: Open, Resolved
        Returns:
            URL of the data file with this Project's issues.
        """
        id_param = "projectId"
        status_param = "status"
        query_str = """query GetProjectIssuesExportPyApi($%s: ID!, $%s: IssueStatus) {
            project(where: { id: $%s }) {
                issueExportUrl(where: { status: $%s })
            }
        }""" % (id_param, status_param, id_param, status_param)

        valid_statuses = {None, "Open", "Resolved"}

        if status not in valid_statuses:
            raise ValueError("status must be in {}. Found {}".format(
                valid_statuses, status))

        res = self.client.execute(query_str, {
            id_param: self.uid,
            status_param: status
        })

        res = res['project']

        logger.debug("Project '%s' issues export, link generated", self.uid)

        return res.get('issueExportUrl')

    def upsert_instructions(self, instructions_file: str) -> None:
        """
        * Uploads instructions to the UI. Running more than once will replace the instructions

        Args:
            instructions_file (str): Path to a local file.
                * Must be a pdf or html file

        Raises:
            ValueError:
                * project must be setup
                * instructions file must have a ".pdf" or ".html" extension
        """

        if self.setup_complete is None:
            raise ValueError(
                "Cannot attach instructions to a project that has not been set up."
            )

        frontend = self.labeling_frontend()

        if frontend.name != "Editor":
            logger.warning(
                f"This function has only been tested to work with the Editor front end. Found %s",
                frontend.name)

        supported_instruction_formats = (".pdf", ".html")
        if not instructions_file.endswith(supported_instruction_formats):
            raise ValueError(
                f"instructions_file must be a pdf or html file. Found {instructions_file}"
            )

        instructions_url = self.client.upload_file(instructions_file)

        query_str = """mutation setprojectinsructionsPyApi($projectId: ID!, $instructions_url: String!) {
                setProjectInstructions(
                    where: {id: $projectId},
                    data: {instructionsUrl: $instructions_url}
                ) {
                    id
                    ontology {
                    id
                    options
                    }
                }
            }"""

        self.client.execute(query_str, {
            'projectId': self.uid,
            'instructions_url': instructions_url
        })

    def labeler_performance(self) -> PaginatedCollection:
        """ Returns the labeler performances for this Project.

        Returns:
            A PaginatedCollection of LabelerPerformance objects.
        """
        id_param = "projectId"
        query_str = """query LabelerPerformancePyApi($%s: ID!) {
            project(where: {id: $%s}) {
                labelerPerformance(skip: %%d first: %%d) {
                    count user {%s} secondsPerLabel totalTimeLabeling consensus
                    averageBenchmarkAgreement lastActivityTime}
            }}""" % (id_param, id_param, query.results_query_part(Entity.User))

        def create_labeler_performance(client, result):
            result["user"] = Entity.User(client, result["user"])
            # python isoformat doesn't accept Z as utc timezone
            result["lastActivityTime"] = datetime.fromisoformat(
                result["lastActivityTime"].replace('Z', '+00:00'))
            return LabelerPerformance(**{
                utils.snake_case(key): value for key, value in result.items()
            })

        return PaginatedCollection(self.client, query_str, {id_param: self.uid},
                                   ["project", "labelerPerformance"],
                                   create_labeler_performance)

    def review_metrics(self, net_score) -> int:
        """ Returns this Project's review metrics.

        Args:
            net_score (None or Review.NetScore): Indicates desired metric.
        Returns:
            int, aggregation count of reviews for given `net_score`.
        """
        if net_score not in (None,) + tuple(Entity.Review.NetScore):
            raise InvalidQueryError(
                "Review metrics net score must be either None "
                "or one of Review.NetScore values")
        id_param = "projectId"
        net_score_literal = "None" if net_score is None else net_score.name
        query_str = """query ProjectReviewMetricsPyApi($%s: ID!){
            project(where: {id:$%s})
            {reviewMetrics {labelAggregate(netScore: %s) {count}}}
        }""" % (id_param, id_param, net_score_literal)
        res = self.client.execute(query_str, {id_param: self.uid})
        return res["project"]["reviewMetrics"]["labelAggregate"]["count"]

    def setup_editor(self, ontology) -> None:
        """
        Sets up the project using the Pictor editor.

        Args:
            ontology (Ontology): The ontology to attach to the project
        """
        if self.labeling_frontend() is not None:
            raise ResourceConflict("Editor is already set up.")

        labeling_frontend = next(
            self.client.get_labeling_frontends(
                where=Entity.LabelingFrontend.name == "Editor"))
        self.labeling_frontend.connect(labeling_frontend)

        LFO = Entity.LabelingFrontendOptions
        self.client._create(
            LFO, {
                LFO.project:
                    self,
                LFO.labeling_frontend:
                    labeling_frontend,
                LFO.customization_options:
                    json.dumps({
                        "tools": [],
                        "classifications": []
                    })
            })

        query_str = """mutation ConnectOntologyPyApi($projectId: ID!, $ontologyId: ID!){
            project(where: {id: $projectId}) {connectOntology(ontologyId: $ontologyId) {id}}}"""
        self.client.execute(query_str, {
            'ontologyId': ontology.uid,
            'projectId': self.uid
        })
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.update(setup_complete=timestamp)

    def setup(self, labeling_frontend, labeling_frontend_options) -> None:
        """ Finalizes the Project setup.

        Args:
            labeling_frontend (LabelingFrontend): Which UI to use to label the
                data.
            labeling_frontend_options (dict or str): Labeling frontend options,
                a.k.a. project ontology. If given a `dict` it will be converted
                to `str` using `json.dumps`.
        """

        if self.labeling_frontend() is not None:
            raise ResourceConflict("Editor is already set up.")

        if not isinstance(labeling_frontend_options, str):
            labeling_frontend_options = json.dumps(labeling_frontend_options)

        self.labeling_frontend.connect(labeling_frontend)

        LFO = Entity.LabelingFrontendOptions
        self.client._create(
            LFO, {
                LFO.project: self,
                LFO.labeling_frontend: labeling_frontend,
                LFO.customization_options: labeling_frontend_options
            })

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.update(setup_complete=timestamp)

    def create_batch(
        self,
        name: str,
        data_rows: Optional[List[Union[str, DataRow]]] = None,
        priority: int = 5,
        consensus_settings: Optional[Dict[str, float]] = None,
        global_keys: Optional[List[str]] = None,
    ):
        """
        Creates a new batch for a project. One of `global_keys` or `data_rows` must be provided, but not both. A
            maximum of 100,000 data rows can be added to a batch.

        Args:
            name: a name for the batch, must be unique within a project
            data_rows: Either a list of `DataRows` or Data Row ids. 
            global_keys: global keys for data rows to add to the batch. 
            priority: An optional priority for the Data Rows in the Batch. 1 highest -> 5 lowest
            consensus_settings: An optional dictionary with consensus settings: {'number_of_labels': 3,
                'coverage_percentage': 0.1}

        Returns: the created batch
        """

        # @TODO: make this automatic?
        if self.queue_mode != QueueMode.Batch:
            raise ValueError("Project must be in batch mode")

        dr_ids = []
        if data_rows is not None:
            for dr in data_rows:
                if isinstance(dr, Entity.DataRow):
                    dr_ids.append(dr.uid)
                elif isinstance(dr, str):
                    dr_ids.append(dr)
                else:
                    raise ValueError(
                        "`data_rows` must be DataRow ids or DataRow objects")

        if data_rows is not None:
            row_count = len(dr_ids)
        elif global_keys is not None:
            row_count = len(global_keys)
        else:
            row_count = 0

        if row_count > 100_000:
            raise ValueError(
                f"Batch exceeds max size, break into smaller batches")
        if not row_count:
            raise ValueError("You need at least one data row in a batch")

        self._wait_until_data_rows_are_processed(
            dr_ids, global_keys, self._wait_processing_max_seconds)

        if consensus_settings:
            consensus_settings = ConsensusSettings(**consensus_settings).dict(
                by_alias=True)

        if row_count >= 1_000:
            return self._create_batch_async(name, dr_ids, global_keys, priority,
                                            consensus_settings)
        else:
            return self._create_batch_sync(name, dr_ids, global_keys, priority,
                                           consensus_settings)

    def create_batches(
        self,
        name_prefix: str,
        data_rows: Optional[List[Union[str, DataRow]]] = None,
        global_keys: Optional[List[str]] = None,
        priority: int = 5,
        consensus_settings: Optional[Dict[str, float]] = None,
    ) -> CreateBatchesTask:
        """
        Creates batches for a project from a list of data rows. One of `global_keys` or `data_rows` must be provided,
        but not both. When more than 100k data rows are specified and thus multiple batches are needed, the specific
        batch that each data row will be placed in is undefined.

        Batches will be created with the specified name prefix and a unique suffix. The suffix will be a 4-digit
        number starting at 0000. For example, if the name prefix is "batch" and 3 batches are created, the names
        will be "batch0000", "batch0001", and "batch0002". This method will throw an error if a batch with the same
        name already exists.

        Args:
            name_prefix: a prefix for the batch names, must be unique within a project
            data_rows: Either a list of `DataRows` or Data Row ids.
            global_keys: global keys for data rows to add to the batch.
            priority: An optional priority for the Data Rows in the Batch. 1 highest -> 5 lowest
            consensus_settings: An optional dictionary with consensus settings: {'number_of_labels': 3,
                'coverage_percentage': 0.1}

        Returns: a task for the created batches
        """

        if self.queue_mode != QueueMode.Batch:
            raise ValueError("Project must be in batch mode")

        dr_ids = []
        if data_rows is not None:
            for dr in data_rows:
                if isinstance(dr, Entity.DataRow):
                    dr_ids.append(dr.uid)
                elif isinstance(dr, str):
                    dr_ids.append(dr)
                else:
                    raise ValueError(
                        "`data_rows` must be DataRow ids or DataRow objects")

        self._wait_until_data_rows_are_processed(
            dr_ids, global_keys, self._wait_processing_max_seconds)

        if consensus_settings:
            consensus_settings = ConsensusSettings(**consensus_settings).dict(
                by_alias=True)

        method = 'createBatches'
        mutation_str = """mutation %sPyApi($projectId: ID!, $input: CreateBatchesInput!) {
                                      project(where: {id: $projectId}) {
                                        %s(input: $input) {
                                          tasks {
                                            batchUuid
                                            taskId
                                          }
                                        }
                                      }
                                    }
                                """ % (method, method)

        params = {
            "projectId": self.uid,
            "input": {
                "batchNamePrefix": name_prefix,
                "dataRowIds": dr_ids,
                "globalKeys": global_keys,
                "priority": priority,
                "consensusSettings": consensus_settings
            }
        }

        tasks = self.client.execute(
            mutation_str, params, experimental=True)["project"][method]["tasks"]
        batch_ids = [task["batchUuid"] for task in tasks]
        task_ids = [task["taskId"] for task in tasks]

        return CreateBatchesTask(self.client, self.uid, batch_ids, task_ids)

    def create_batches_from_dataset(
        self,
        name_prefix: str,
        dataset_id: str,
        priority: int = 5,
        consensus_settings: Optional[Dict[str,
                                          float]] = None) -> CreateBatchesTask:
        """
        Creates batches for a project from a dataset, selecting only the data rows that are not already added to the
        project. When the dataset contains more than 100k data rows and multiple batches are needed, the specific batch
        that each data row will be placed in is undefined. Note that data rows may not be immediately available for a
        project after being added to a dataset; use the `_wait_until_data_rows_are_processed` method to ensure that
        data rows are available before creating batches.

        Batches will be created with the specified name prefix and a unique suffix. The suffix will be a 4-digit
        number starting at 0000. For example, if the name prefix is "batch" and 3 batches are created, the names
        will be "batch0000", "batch0001", and "batch0002". This method will throw an error if a batch with the same
        name already exists.

        Args:
            name_prefix: a prefix for the batch names, must be unique within a project
            dataset_id: the id of the dataset to create batches from
            priority: An optional priority for the Data Rows in the Batch. 1 highest -> 5 lowest
            consensus_settings: An optional dictionary with consensus settings: {'number_of_labels': 3,
                'coverage_percentage': 0.1}

        Returns: a task for the created batches
        """

        if self.queue_mode != QueueMode.Batch:
            raise ValueError("Project must be in batch mode")

        if consensus_settings:
            consensus_settings = ConsensusSettings(**consensus_settings).dict(
                by_alias=True)

        print("Creating batches from dataset %s", dataset_id)

        method = 'createBatchesFromDataset'
        mutation_str = """mutation %sPyApi($projectId: ID!, $input: CreateBatchesFromDatasetInput!) {
                                        project(where: {id: $projectId}) {
                                            %s(input: $input) {
                                              tasks {
                                                batchUuid
                                                taskId
                                              }
                                            }
                                        }
                                    }
                                """ % (method, method)

        params = {
            "projectId": self.uid,
            "input": {
                "batchNamePrefix": name_prefix,
                "datasetId": dataset_id,
                "priority": priority,
                "consensusSettings": consensus_settings
            }
        }

        tasks = self.client.execute(
            mutation_str, params, experimental=True)["project"][method]["tasks"]

        batch_ids = [task["batchUuid"] for task in tasks]
        task_ids = [task["taskId"] for task in tasks]

        return CreateBatchesTask(self.client, self.uid, batch_ids, task_ids)

    def _create_batch_sync(self, name, dr_ids, global_keys, priority,
                           consensus_settings):
        method = 'createBatchV2'
        query_str = """mutation %sPyApi($projectId: ID!, $batchInput: CreateBatchInput!) {
                  project(where: {id: $projectId}) {
                    %s(input: $batchInput) {
                        batch {
                            %s
                        }
                        failedDataRowIds
                    }
                  }
                }
            """ % (method, method, query.results_query_part(Entity.Batch))
        params = {
            "projectId": self.uid,
            "batchInput": {
                "name": name,
                "dataRowIds": dr_ids,
                "globalKeys": global_keys,
                "priority": priority,
                "consensusSettings": consensus_settings
            }
        }
        res = self.client.execute(query_str,
                                  params,
                                  timeout=180.0,
                                  experimental=True)["project"][method]
        batch = res['batch']
        batch['size'] = res['batch']['size']
        return Entity.Batch(self.client,
                            self.uid,
                            batch,
                            failed_data_row_ids=res['failedDataRowIds'])

    def _create_batch_async(self,
                            name: str,
                            dr_ids: Optional[List[str]] = None,
                            global_keys: Optional[List[str]] = None,
                            priority: int = 5,
                            consensus_settings: Optional[Dict[str,
                                                              float]] = None):
        method = 'createEmptyBatch'
        create_empty_batch_mutation_str = """mutation %sPyApi($projectId: ID!, $input: CreateEmptyBatchInput!) {
                                      project(where: {id: $projectId}) {
                                        %s(input: $input) {
                                            id
                                        }
                                      }
                                    }
                                """ % (method, method)

        params = {
            "projectId": self.uid,
            "input": {
                "name": name,
                "consensusSettings": consensus_settings
            }
        }

        res = self.client.execute(create_empty_batch_mutation_str,
                                  params,
                                  timeout=180.0,
                                  experimental=True)["project"][method]
        batch_id = res['id']

        method = 'addDataRowsToBatchAsync'
        add_data_rows_mutation_str = """mutation %sPyApi($projectId: ID!, $input: AddDataRowsToBatchInput!) {
                                      project(where: {id: $projectId}) {
                                        %s(input: $input) {
                                          taskId
                                        }
                                      }
                                    }
                                """ % (method, method)

        params = {
            "projectId": self.uid,
            "input": {
                "batchId": batch_id,
                "dataRowIds": dr_ids,
                "globalKeys": global_keys,
                "priority": priority,
            }
        }

        res = self.client.execute(add_data_rows_mutation_str,
                                  params,
                                  timeout=180.0,
                                  experimental=True)["project"][method]

        task_id = res['taskId']

        task = self._wait_for_task(task_id)
        if task.status != "COMPLETE":
            raise LabelboxError(f"Batch was not created successfully: " +
                                json.dumps(task.errors))

        return self.client.get_batch(self.uid, batch_id)

    def _update_queue_mode(self, mode: "QueueMode") -> "QueueMode":
        """
        Updates the queueing mode of this project.

        Deprecation notice: This method is deprecated. Going forward, projects must
        go through a migration to have the queue mode changed. Users should specify the
        queue mode for a project during creation if a non-default mode is desired.

        For more information, visit https://docs.labelbox.com/reference/migrating-to-workflows#upcoming-changes

        Args:
            mode: the specified queue mode

        Returns: the updated queueing mode of this project

        """

        logger.warning(
            "Updating the queue_mode for a project will soon no longer be supported."
        )

        if self.queue_mode == mode:
            return mode

        if mode == QueueMode.Batch:
            status = "ENABLED"
        elif mode == QueueMode.Dataset:
            status = "DISABLED"
        else:
            raise ValueError(
                "Must provide either `BATCH` or `DATASET` as a mode")

        query_str = """mutation %s($projectId: ID!, $status: TagSetStatusInput!) {
              project(where: {id: $projectId}) {
                 setTagSetStatus(input: {tagSetStatus: $status}) {
                    tagSetStatus
                }
            }
        }
        """ % "setTagSetStatusPyApi"

        self.client.execute(query_str, {
            'projectId': self.uid,
            'status': status
        })

        return mode

    def get_queue_mode(self) -> "QueueMode":
        """
        Provides the queue mode used for this project.

        Deprecation notice: This method is deprecated and will be removed in
        a future version. To obtain the queue mode of a project, simply refer
        to the queue_mode attribute of a Project.

        For more information, visit https://docs.labelbox.com/reference/migrating-to-workflows#upcoming-changes

        Returns: the QueueMode for this project

        """

        logger.warning(
            "Obtaining the queue_mode for a project through this method will soon"
            " no longer be supported.")

        query_str = """query %s($projectId: ID!) {
              project(where: {id: $projectId}) {
                 tagSetStatus
            }
        }
        """ % "GetTagSetStatusPyApi"

        status = self.client.execute(
            query_str, {'projectId': self.uid})["project"]["tagSetStatus"]

        if status == "ENABLED":
            return QueueMode.Batch
        elif status == "DISABLED":
            return QueueMode.Dataset
        else:
            raise ValueError("Status not known")

    def validate_labeling_parameter_overrides(self, data) -> None:
        for idx, row in enumerate(data):
            if len(row) < 2:
                raise TypeError(
                    f"Data must be a list of tuples containing a DataRow and priority (int). Found {len(row)} items. Index: {idx}"
                )
            data_row = row[0]
            priority = row[1]
            if not isinstance(data_row, Entity.DataRow):
                raise TypeError(
                    f"data_row should be be of type DataRow. Found {type(data_row)}. Index: {idx}"
                )

            if not isinstance(priority, int):
                raise TypeError(
                    f"Priority must be an int. Found {type(priority)} for data_row {data_row}. Index: {idx}"
                )

    def set_labeling_parameter_overrides(self, data) -> bool:
        """ Adds labeling parameter overrides to this project.

        See information on priority here:
            https://docs.labelbox.com/en/configure-editor/queue-system#reservation-system

            >>> project.set_labeling_parameter_overrides([
            >>>     (data_row_1, 2), (data_row_2, 1)])

        Args:
            data (iterable): An iterable of tuples. Each tuple must contain
                (DataRow, priority<int>) for the new override.

                Priority:
                    * Data will be labeled in priority order.
                        - A lower number priority is labeled first.
                        - All signed 32-bit integers are accepted, from -2147483648 to 2147483647.
                    * Priority is not the queue position.
                        - The position is determined by the relative priority.
                        - E.g. [(data_row_1, 5,1), (data_row_2, 2,1), (data_row_3, 10,1)]
                            will be assigned in the following order: [data_row_2, data_row_1, data_row_3]
                    * The priority only effects items in the queue.
                        - Assigning a priority will not automatically add the item back into the queue.
        Returns:
            bool, indicates if the operation was a success.
        """
        data = [t[:2] for t in data]
        self.validate_labeling_parameter_overrides(data)
        data_str = ",\n".join("{dataRow: {id: \"%s\"}, priority: %d }" %
                              (data_row.uid, priority)
                              for data_row, priority in data)
        id_param = "projectId"
        query_str = """mutation SetLabelingParameterOverridesPyApi($%s: ID!){
            project(where: { id: $%s }) {setLabelingParameterOverrides
            (data: [%s]) {success}}} """ % (id_param, id_param, data_str)
        res = self.client.execute(query_str, {id_param: self.uid})
        return res["project"]["setLabelingParameterOverrides"]["success"]

    def update_data_row_labeling_priority(
        self,
        data_rows: List[str],
        priority: int,
    ) -> bool:
        """
        Updates labeling parameter overrides to this project in bulk. This method allows up to 1 million data rows to be
        updated at once.

        See information on priority here:
            https://docs.labelbox.com/en/configure-editor/queue-system#reservation-system

        Args:
            data_rows (iterable): An iterable of data row ids.
            priority (int): Priority for the new override. See above for more information.

        Returns:
            bool, indicates if the operation was a success.
        """

        method = "createQueuePriorityUpdateTask"
        priority_param = "priority"
        project_param = "projectId"
        data_rows_param = "dataRowIds"
        query_str = """mutation %sPyApi(
              $%s: Int!
              $%s: ID!
              $%s: [ID!]
            ) {
              project(where: { id: $%s }) {
                %s(
                  data: { priority: $%s, dataRowIds: $%s }
                ) {
                  taskId
                }
              }
            }
        """ % (method, priority_param, project_param, data_rows_param,
               project_param, method, priority_param, data_rows_param)
        res = self.client.execute(
            query_str, {
                priority_param: priority,
                project_param: self.uid,
                data_rows_param: data_rows
            })["project"][method]

        task_id = res['taskId']

        task = self._wait_for_task(task_id)
        if task.status != "COMPLETE":
            raise LabelboxError(f"Priority was not updated successfully: " +
                                json.dumps(task.errors))
        return True

    def upsert_review_queue(self, quota_factor) -> None:
        """ Sets the the proportion of total assets in a project to review.

        More information can be found here:
            https://docs.labelbox.com/en/quality-assurance/review-labels#configure-review-percentage

        Args:
            quota_factor (float): Which part (percentage) of the queue
                to reinitiate. Between 0 and 1.
        """

        if not 0. <= quota_factor <= 1.:
            raise ValueError("Quota factor must be in the range of [0,1]")

        id_param = "projectId"
        quota_param = "quotaFactor"
        query_str = """mutation UpsertReviewQueuePyApi($%s: ID!, $%s: Float!){
            upsertReviewQueue(where:{project: {id: $%s}}
                            data:{quotaFactor: $%s}) {id}}""" % (
            id_param, quota_param, id_param, quota_param)
        res = self.client.execute(query_str, {
            id_param: self.uid,
            quota_param: quota_factor
        })

    def extend_reservations(self, queue_type) -> int:
        """ Extends all the current reservations for the current user on the given
        queue type.
        Args:
            queue_type (str): Either "LabelingQueue" or "ReviewQueue"
        Returns:
            int, the number of reservations that were extended.
        """
        if queue_type not in ("LabelingQueue", "ReviewQueue"):
            raise InvalidQueryError("Unsupported queue type: %s" % queue_type)

        id_param = "projectId"
        query_str = """mutation ExtendReservationsPyApi($%s: ID!){
            extendReservations(projectId:$%s queueType:%s)}""" % (
            id_param, id_param, queue_type)
        res = self.client.execute(query_str, {id_param: self.uid})
        return res["extendReservations"]

    def enable_model_assisted_labeling(self, toggle: bool = True) -> bool:
        """ Turns model assisted labeling either on or off based on input

        Args:
            toggle (bool): True or False boolean
        Returns:
            True if toggled on or False if toggled off
        """
        project_param = "project_id"
        show_param = "show"

        query_str = """mutation toggle_model_assisted_labelingPyApi($%s: ID!, $%s: Boolean!) {
            project(where: {id: $%s }) {
                showPredictionsToLabelers(show: $%s) {
                    id, showingPredictionsToLabelers
                }
            }
        }""" % (project_param, show_param, project_param, show_param)

        params = {project_param: self.uid, show_param: toggle}

        res = self.client.execute(query_str, params)
        return res["project"]["showPredictionsToLabelers"][
            "showingPredictionsToLabelers"]

    def bulk_import_requests(self) -> PaginatedCollection:
        """ Returns bulk import request objects which are used in model-assisted labeling.
        These are returned with the oldest first, and most recent last.
        """

        id_param = "project_id"
        query_str = """query ListAllImportRequestsPyApi($%s: ID!) {
            bulkImportRequests (
                where: { projectId: $%s }
                skip: %%d
                first: %%d
            ) {
                %s
            }
        }""" % (id_param, id_param,
                query.results_query_part(Entity.BulkImportRequest))
        return PaginatedCollection(self.client, query_str,
                                   {id_param: str(self.uid)},
                                   ["bulkImportRequests"],
                                   Entity.BulkImportRequest)

    def batches(self) -> PaginatedCollection:
        """ Fetch all batches that belong to this project

        Returns:
            A `PaginatedCollection` of `Batch`es
        """
        id_param = "projectId"
        query_str = """query GetProjectBatchesPyApi($from: String, $first: PageSize, $%s: ID!) {
            project(where: {id: $%s}) {id
            batches(after: $from, first: $first) { nodes { %s } pageInfo { endCursor }}}}
        """ % (id_param, id_param, query.results_query_part(Entity.Batch))
        return PaginatedCollection(
            self.client,
            query_str, {id_param: self.uid}, ['project', 'batches', 'nodes'],
            lambda client, res: Entity.Batch(client, self.uid, res),
            cursor_path=['project', 'batches', 'pageInfo', 'endCursor'],
            experimental=True)

    def task_queues(self) -> List[TaskQueue]:
        """ Fetch all task queues that belong to this project

        Returns:
            A `List` of `TaskQueue`s
        """
        query_str = """query GetProjectTaskQueuesPyApi($projectId: ID!) {
              project(where: {id: $projectId}) {
                taskQueues {
                  %s
                }
              }
            }
        """ % (query.results_query_part(Entity.TaskQueue))

        task_queue_values = self.client.execute(
            query_str, {"projectId": self.uid},
            timeout=180.0,
            experimental=True)["project"]["taskQueues"]

        return [
            Entity.TaskQueue(self.client, field_values)
            for field_values in task_queue_values
        ]

    def move_data_rows_to_task_queue(self, data_row_ids: List[str],
                                     task_queue_id: str):
        """

        Moves data rows to the specified task queue.

        Args:
            data_row_ids: a list of data row ids to be moved
            task_queue_id: the task queue id to be moved to, or None to specify the "Done" queue

        Returns:
            None if successful, or a raised error on failure

        """
        method = "createBulkAddRowsToQueueTask"
        query_str = """mutation AddDataRowsToTaskQueueAsyncPyApi(
          $projectId: ID!
          $queueId: ID
          $dataRowIds: [ID!]!
        ) {
          project(where: { id: $projectId }) {
            %s(
              data: { queueId: $queueId, dataRowIds: $dataRowIds }
            ) {
              taskId
            }
          }
        }
        """ % method

        task_id = self.client.execute(
            query_str, {
                "projectId": self.uid,
                "queueId": task_queue_id,
                "dataRowIds": data_row_ids
            },
            timeout=180.0,
            experimental=True)["project"][method]["taskId"]

        task = self._wait_for_task(task_id)
        if task.status != "COMPLETE":
            raise LabelboxError(f"Data rows were not moved successfully: " +
                                json.dumps(task.errors))

    def _wait_for_task(self, task_id: str) -> Task:
        task = Task.get_task(self.client, task_id)
        task.wait_till_done()

        return task

    def upload_annotations(
            self,
            name: str,
            annotations: Union[str, Path, Iterable[Dict]],
            validate: bool = False) -> 'BulkImportRequest':  # type: ignore
        """ Uploads annotations to a new Editor project.

        Args:
            name (str): name of the BulkImportRequest job
            annotations (str or Path or Iterable):
                url that is publicly accessible by Labelbox containing an
                ndjson file
                OR local path to an ndjson file
                OR iterable of annotation rows
            validate (bool):
                Whether or not to validate the payload before uploading.
        Returns:
            BulkImportRequest
        """

        if isinstance(annotations, str) or isinstance(annotations, Path):

            def _is_url_valid(url: Union[str, Path]) -> bool:
                """ Verifies that the given string is a valid url.

                Args:
                    url: string to be checked
                Returns:
                    True if the given url is valid otherwise False

                """
                if isinstance(url, Path):
                    return False
                parsed = urlparse(url)
                return bool(parsed.scheme) and bool(parsed.netloc)

            if _is_url_valid(annotations):
                return Entity.BulkImportRequest.create_from_url(
                    client=self.client,
                    project_id=self.uid,
                    name=name,
                    url=str(annotations),
                    validate=validate)
            else:
                path = Path(annotations)
                if not path.exists():
                    raise FileNotFoundError(
                        f'{annotations} is not a valid url nor existing local file'
                    )
                return Entity.BulkImportRequest.create_from_local_file(
                    client=self.client,
                    project_id=self.uid,
                    name=name,
                    file=path,
                    validate_file=validate,
                )
        elif isinstance(annotations, Iterable):
            return Entity.BulkImportRequest.create_from_objects(
                client=self.client,
                project_id=self.uid,
                name=name,
                predictions=annotations,  # type: ignore
                validate=validate)
        else:
            raise ValueError(
                f'Invalid annotations given of type: {type(annotations)}')

    def _wait_until_data_rows_are_processed(
            self,
            data_row_ids: Optional[List[str]] = None,
            global_keys: Optional[List[str]] = None,
            wait_processing_max_seconds: int = _wait_processing_max_seconds,
            sleep_interval=30):
        """ Wait until all the specified data rows are processed"""
        start_time = datetime.now()

        max_data_rows_per_poll = 100_000
        if data_row_ids is not None:
            for i in range(0, len(data_row_ids), max_data_rows_per_poll):
                chunk = data_row_ids[i:i + max_data_rows_per_poll]
                self._poll_data_row_processing_status(
                    chunk, [], start_time, wait_processing_max_seconds,
                    sleep_interval)

        if global_keys is not None:
            for i in range(0, len(global_keys), max_data_rows_per_poll):
                chunk = global_keys[i:i + max_data_rows_per_poll]
                self._poll_data_row_processing_status(
                    [], chunk, start_time, wait_processing_max_seconds,
                    sleep_interval)

    def _poll_data_row_processing_status(
            self,
            data_row_ids: List[str],
            global_keys: List[str],
            start_time: datetime,
            wait_processing_max_seconds: int = _wait_processing_max_seconds,
            sleep_interval=30):

        while True:
            if (datetime.now() -
                    start_time).total_seconds() >= wait_processing_max_seconds:
                raise ProcessingWaitTimeout(
                    """Maximum wait time exceeded while waiting for data rows to be processed. 
                    Try creating a batch a bit later""")

            all_good = self.__check_data_rows_have_been_processed(
                data_row_ids, global_keys)
            if all_good:
                return

            logger.debug(
                'Some of the data rows are still being processed, waiting...')
            time.sleep(sleep_interval)

    def __check_data_rows_have_been_processed(
            self,
            data_row_ids: Optional[List[str]] = None,
            global_keys: Optional[List[str]] = None):

        if data_row_ids is not None and len(data_row_ids) > 0:
            param_name = "dataRowIds"
            params = {param_name: data_row_ids}
        else:
            param_name = "globalKeys"
            global_keys = global_keys if global_keys is not None else []
            params = {param_name: global_keys}

        query_str = """query CheckAllDataRowsHaveBeenProcessedPyApi($%s: [ID!]) {
            queryAllDataRowsHaveBeenProcessed(%s:$%s) {
                allDataRowsHaveBeenProcessed
           }
        }""" % (param_name, param_name, param_name)

        response = self.client.execute(query_str, params)
        return response["queryAllDataRowsHaveBeenProcessed"][
            "allDataRowsHaveBeenProcessed"]


class ProjectMember(DbObject):
    user = Relationship.ToOne("User", cache=True)
    role = Relationship.ToOne("Role", cache=True)
    access_from = Field.String("access_from")


class LabelingParameterOverride(DbObject):
    """ Customizes the order of assets in the label queue.

    Attributes:
        priority (int): A prioritization score.
        number_of_labels (int): Number of times an asset should be labeled.
    """
    priority = Field.Int("priority")
    number_of_labels = Field.Int("number_of_labels")

    data_row = Relationship.ToOne("DataRow", cache=True)


LabelerPerformance = namedtuple(
    "LabelerPerformance", "user count seconds_per_label, total_time_labeling "
    "consensus average_benchmark_agreement last_activity_time")
LabelerPerformance.__doc__ = (
    "Named tuple containing info about a labeler's performance.")


def _check_converter_import():
    if 'LBV1Converter' not in globals():
        raise ImportError(
            "Missing dependencies to import converter. "
            "Use `pip install labelbox[data] --upgrade` to add missing dependencies. "
            "or download raw json with project.export_labels()")
