import json
import time
import logging
from collections import namedtuple
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Union, Iterable
from urllib.parse import urlparse

from labelbox import utils
from labelbox.schema.data_row import DataRow
from labelbox.orm import query
from labelbox.schema.bulk_import_request import BulkImportRequest
from labelbox.exceptions import InvalidQueryError
from labelbox.orm.db_object import DbObject, Updateable, Deletable
from labelbox.orm.model import Entity, Field, Relationship
from labelbox.pagination import PaginatedCollection

try:
    datetime.fromisoformat  # type: ignore[attr-defined]
except AttributeError:
    from backports.datetime_fromisoformat import MonkeyPatch
    MonkeyPatch.patch_fromisoformat()

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
        auto_audit_number_of_labels (int)
        auto_audit_percentage (float)

        datasets (Relationship): `ToMany` relationship to Dataset
        created_by (Relationship): `ToOne` relationship to User
        organization (Relationship): `ToOne` relationship to Organization
        reviews (Relationship): `ToMany` relationship to Review
        labeling_frontend (Relationship): `ToOne` relationship to LabelingFrontend
        labeling_frontend_options (Relationship): `ToMany` relationship to LabelingFrontendOptions
        labeling_parameter_overrides (Relationship): `ToMany` relationship to LabelingParameterOverride
        webhooks (Relationship): `ToMany` relationship to Webhook
        benchmarks (Relationship): `ToMany` relationship to Benchmark
        active_prediction_model (Relationship): `ToOne` relationship to PredictionModel
        predictions (Relationship): `ToMany` relationship to Prediction
        ontology (Relationship): `ToOne` relationship to Ontology
    """
    name = Field.String("name")
    description = Field.String("description")
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    setup_complete = Field.DateTime("setup_complete")
    last_activity_time = Field.DateTime("last_activity_time")
    auto_audit_number_of_labels = Field.Int("auto_audit_number_of_labels")
    auto_audit_percentage = Field.Float("auto_audit_percentage")

    # Relationships
    datasets = Relationship.ToMany("Dataset", True)
    created_by = Relationship.ToOne("User", False, "created_by")
    organization = Relationship.ToOne("Organization", False)
    reviews = Relationship.ToMany("Review", True)
    labeling_frontend = Relationship.ToOne("LabelingFrontend")
    labeling_frontend_options = Relationship.ToMany(
        "LabelingFrontendOptions", False, "labeling_frontend_options")
    labeling_parameter_overrides = Relationship.ToMany(
        "LabelingParameterOverride", False, "labeling_parameter_overrides")
    webhooks = Relationship.ToMany("Webhook", False)
    benchmarks = Relationship.ToMany("Benchmark", False)
    active_prediction_model = Relationship.ToOne("PredictionModel", False,
                                                 "active_prediction_model")
    predictions = Relationship.ToMany("Prediction", False)
    ontology = Relationship.ToOne("Ontology", True)

    def members(self):
        """ Fetch all current members for this project

        Returns:
            A `PaginatedCollection of `ProjectMember`s

        """
        id_param = "projectId"
        query_str = """query ProjectMemberOverviewPyApi($%s: ID!) {
             project(where: {id : $%s}) { id members(skip: %%d first: %%d){ id user { %s } role { id name } }
           }
        }""" % (id_param, id_param, query.results_query_part(Entity.User))
        return PaginatedCollection(self.client, query_str,
                                   {id_param: str(self.uid)},
                                   ["project", "members"], ProjectMember)

    def create_label(self, **kwargs):
        """ Creates a label on a Legacy Editor project. Not supported in the new Editor.
        Args:
            **kwargs: Label attributes. At minimum, the label `DataRow`.
        """
        # Copy-paste of Client._create code so we can inject
        # a connection to Type. Type objects are on their way to being
        # deprecated and we don't want the Py client lib user to know
        # about them. At the same time they're connected to a Label at
        # label creation in a non-standard way (connect via name).
        logger.warning(
            "`create_label` is deprecated and is not compatible with the new editor."
        )

        Label = Entity.Label

        kwargs[Label.project] = self
        kwargs[Label.seconds_to_label] = kwargs.get(Label.seconds_to_label.name,
                                                    0.0)
        data = {
            Label.attribute(attr) if isinstance(attr, str) else attr:
            value.uid if isinstance(value, DbObject) else value
            for attr, value in kwargs.items()
        }

        query_str, params = query.create(Label, data)
        # Inject connection to Type
        query_str = query_str.replace(
            "data: {", "data: {type: {connect: {name: \"Any\"}} ")
        res = self.client.execute(query_str, params)
        return Label(self.client, res["createLabel"])

    def labels(self, datasets=None, order_by=None):
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

    def export_labels(self, timeout_seconds=60):
        """ Calls the server-side Label exporting that generates a JSON
        payload, and returns the URL to that payload.

        Will only generate a new URL at a max frequency of 30 min.

        Args:
            timeout_seconds (float): Max waiting time, in seconds.
        Returns:
            URL of the data file with this Project's labels. If the server didn't
            generate during the `timeout_seconds` period, None is returned.
        """
        sleep_time = 2
        id_param = "projectId"
        query_str = """mutation GetLabelExportUrlPyApi($%s: ID!)
            {exportLabels(data:{projectId: $%s }) {downloadUrl createdAt shouldPoll} }
        """ % (id_param, id_param)

        while True:
            res = self.client.execute(query_str, {id_param: self.uid})
            res = res["exportLabels"]
            if not res["shouldPoll"]:
                return res["downloadUrl"]

            timeout_seconds -= sleep_time
            if timeout_seconds <= 0:
                return None

            logger.debug("Project '%s' label export, waiting for server...",
                         self.uid)
            time.sleep(sleep_time)

    def export_issues(self, status=None):
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

    def upsert_instructions(self, instructions_file: str):
        """
        * Uploads instructions to the UI. Running more than once will replace the instructions
            
        Args:
            instructions_file (str): Path to a local file.
                * Must be either a pdf, text, or html file.

        Raises:
            ValueError:
                * project must be setup 
                * instructions file must end with one of ".text", ".txt", ".pdf", ".html"
        """

        if self.setup_complete is None:
            raise ValueError(
                "Cannot attach instructions to a project that has not been set up."
            )

        frontend = self.labeling_frontend()
        frontendId = frontend.uid

        if frontend.name != "Editor":
            logger.warning(
                f"This function has only been tested to work with the Editor front end. Found %s",
                frontend.name)

        supported_instruction_formats = (".text", ".txt", ".pdf", ".html")
        if not instructions_file.endswith(supported_instruction_formats):
            raise ValueError(
                f"instructions_file must end with one of {supported_instruction_formats}. Found {instructions_file}"
            )

        lfo = list(self.labeling_frontend_options())[-1]
        instructions_url = self.client.upload_file(instructions_file)
        customization_options = json.loads(lfo.customization_options)
        customization_options['projectInstructions'] = instructions_url
        option_id = lfo.uid

        self.client.execute(
            """mutation UpdateFrontendWithExistingOptionsPyApi (
                    $frontendId: ID!, 
                    $optionsId: ID!, 
                    $name: String!, 
                    $description: String!, 
                    $customizationOptions: String!
                ) {
                    updateLabelingFrontend(
                        where: {id: $frontendId}, 
                        data: {name: $name, description: $description}
                    ) {id}
                    updateLabelingFrontendOptions(
                        where: {id: $optionsId}, 
                        data: {customizationOptions: $customizationOptions}
                    ) {id}
                }""", {
                "frontendId": frontendId,
                "optionsId": option_id,
                "name": frontend.name,
                "description": "Video, image, and text annotation",
                "customizationOptions": json.dumps(customization_options)
            })

    def labeler_performance(self):
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
            return LabelerPerformance(
                **
                {utils.snake_case(key): value for key, value in result.items()})

        return PaginatedCollection(self.client, query_str, {id_param: self.uid},
                                   ["project", "labelerPerformance"],
                                   create_labeler_performance)

    def review_metrics(self, net_score):
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

    def setup(self, labeling_frontend, labeling_frontend_options):
        """ Finalizes the Project setup.

        Args:
            labeling_frontend (LabelingFrontend): Which UI to use to label the
                data.
            labeling_frontend_options (dict or str): Labeling frontend options,
                a.k.a. project ontology. If given a `dict` it will be converted
                to `str` using `json.dumps`.
        """
        organization = self.client.get_organization()
        if not isinstance(labeling_frontend_options, str):
            labeling_frontend_options = json.dumps(labeling_frontend_options)

        self.labeling_frontend.connect(labeling_frontend)

        LFO = Entity.LabelingFrontendOptions
        labeling_frontend_options = self.client._create(
            LFO, {
                LFO.project: self,
                LFO.labeling_frontend: labeling_frontend,
                LFO.customization_options: labeling_frontend_options,
                LFO.organization: organization
            })

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.update(setup_complete=timestamp)

    def validate_labeling_parameter_overrides(self, data):
        for idx, row in enumerate(data):
            if len(row) != 3:
                raise TypeError(
                    f"Data must be a list of tuples containing a DataRow, priority (int), num_labels (int). Found {len(row)} items. Index: {idx}"
                )
            data_row, priority, num_labels = row
            if not isinstance(data_row, DataRow):
                raise TypeError(
                    f"data_row should be be of type DataRow. Found {type(data_row)}. Index: {idx}"
                )

            for name, value in [["Priority", priority],
                                ["Number of labels", num_labels]]:
                if not isinstance(value, int):
                    raise TypeError(
                        f"{name} must be an int. Found {type(value)} for data_row {data_row}. Index: {idx}"
                    )
                if value < 1:
                    raise ValueError(
                        f"{name} must be greater than 0 for data_row {data_row}. Index: {idx}"
                    )

    def set_labeling_parameter_overrides(self, data):
        """ Adds labeling parameter overrides to this project.
                
        See information on priority here:
            https://docs.labelbox.com/en/configure-editor/queue-system#reservation-system
    
            >>> project.set_labeling_parameter_overrides([
            >>>     (data_row_1, 2, 3), (data_row_2, 1, 4)])

        Args:
            data (iterable): An iterable of tuples. Each tuple must contain
                (DataRow, priority<int>, number_of_labels<int>) for the new override.

                Priority:
                    * Data will be labeled in priority order.
                        - A lower number priority is labeled first.
                        - Minimum priority is 1.
                    * Priority is not the queue position.
                        - The position is determined by the relative priority.
                        - E.g. [(data_row_1, 5,1), (data_row_2, 2,1), (data_row_3, 10,1)] 
                            will be assigned in the following order: [data_row_2, data_row_1, data_row_3]
                    * Datarows with parameter overrides will appear before datarows without overrides.
                    * The priority only effects items in the queue.
                        - Assigning a priority will not automatically add the item back into the queue.  
                Number of labels:
                    * The number of times a data row should be labeled.
                        - Creates duplicate data rows in a project (one for each number of labels).
                    * New duplicated data rows will be added to the queue.
                        - Already labeled duplicates will not be sent back to the queue.
                    * The queue will never assign the same datarow to a single labeler more than once.
                        - If the number of labels is greater than the number of labelers working on a project then
                            the extra items will remain in the queue (this can be fixed by removing the override at any time).
                    * Setting this to 1 will result in the default behavior (no duplicates).
        Returns:
            bool, indicates if the operation was a success.
        """
        self.validate_labeling_parameter_overrides(data)
        data_str = ",\n".join(
            "{dataRow: {id: \"%s\"}, priority: %d, numLabels: %d }" %
            (data_row.uid, priority, num_labels)
            for data_row, priority, num_labels in data)
        id_param = "projectId"
        query_str = """mutation SetLabelingParameterOverridesPyApi($%s: ID!){
            project(where: { id: $%s }) {setLabelingParameterOverrides
            (data: [%s]) {success}}} """ % (id_param, id_param, data_str)
        res = self.client.execute(query_str, {id_param: self.uid})
        return res["project"]["setLabelingParameterOverrides"]["success"]

    def unset_labeling_parameter_overrides(self, data_rows):
        """ Removes labeling parameter overrides to this project.

        * This will remove unlabeled duplicates in the queue.

        Args:
            data_rows (iterable): An iterable of DataRows.
        Returns:
            bool, indicates if the operation was a success.
        """
        id_param = "projectId"
        query_str = """mutation UnsetLabelingParameterOverridesPyApi($%s: ID!){
            project(where: { id: $%s}) {
            unsetLabelingParameterOverrides(data: [%s]) { success }}}""" % (
            id_param, id_param, ",\n".join(
                "{dataRowId: \"%s\"}" % row.uid for row in data_rows))
        res = self.client.execute(query_str, {id_param: self.uid})
        return res["project"]["unsetLabelingParameterOverrides"]["success"]

    def upsert_review_queue(self, quota_factor):
        """ Sets the the proportion of total assets in a project to review.

        More information can be found here: 
            https://docs.labelbox.com/en/quality-assurance/review-labels#configure-review-percentage

        Args:
            quota_factor (float): Which part (percentage) of the queue
                to reinitiate. Between 0 and 1.
        """

        if not 0. < quota_factor < 1.:
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

    def extend_reservations(self, queue_type):
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

    def create_prediction_model(self, name, version):
        """ Creates a PredictionModel connected to a Legacy Editor Project.

        Args:
            name (str): The new PredictionModel's name.
            version (int): The new PredictionModel's version.
        Returns:
            A newly created PredictionModel.
        """

        logger.warning(
            "`create_prediction_model` is deprecated and is not compatible with the new editor."
        )

        PM = Entity.PredictionModel
        model = self.client._create(PM, {
            PM.name.name: name,
            PM.version.name: version
        })
        self.active_prediction_model.connect(model)
        return model

    def create_prediction(self, label, data_row, prediction_model=None):
        """ Creates a Prediction within a Legacy Editor Project. Not supported
        in the new Editor.

        Args:
            label (str): The `label` field of the new Prediction.
            data_row (DataRow): The DataRow for which the Prediction is created.
            prediction_model (PredictionModel or None): The PredictionModel
                within which the new Prediction is created. If None then this
                Project's active_prediction_model is used.
        Return:
            A newly created Prediction.
        Raises:
            labelbox.excepions.InvalidQueryError: if given `prediction_model`
                is None and this Project's active_prediction_model is also
                None.
        """
        logger.warning(
            "`create_prediction` is deprecated and is not compatible with the new editor."
        )

        if prediction_model is None:
            prediction_model = self.active_prediction_model()
            if prediction_model is None:
                raise InvalidQueryError(
                    "Project '%s' has no active prediction model" % self.name)

        label_param = "label"
        model_param = "prediction_model_id"
        project_param = "project_id"
        data_row_param = "data_row_id"

        Prediction = Entity.Prediction
        query_str = """mutation CreatePredictionPyApi(
            $%s: String!, $%s: ID!, $%s: ID!, $%s: ID!) {createPrediction(
            data: {label: $%s, predictionModelId: $%s, projectId: $%s,
                   dataRowId: $%s})
            {%s}}""" % (label_param, model_param, project_param, data_row_param,
                        label_param, model_param, project_param, data_row_param,
                        query.results_query_part(Prediction))
        params = {
            label_param: label,
            model_param: prediction_model.uid,
            data_row_param: data_row.uid,
            project_param: self.uid
        }
        res = self.client.execute(query_str, params)
        return Prediction(self.client, res["createPrediction"])

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

    def upload_annotations(
            self,
            name: str,
            annotations: Union[str, Path, Iterable[Dict]],
            validate: bool = True) -> 'BulkImportRequest':  # type: ignore
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
                return BulkImportRequest.create_from_url(client=self.client,
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
                return BulkImportRequest.create_from_local_file(
                    client=self.client,
                    project_id=self.uid,
                    name=name,
                    file=path,
                    validate_file=validate,
                )
        elif isinstance(annotations, Iterable):
            return BulkImportRequest.create_from_objects(
                client=self.client,
                project_id=self.uid,
                name=name,
                predictions=annotations,  # type: ignore
                validate=validate)
        else:
            raise ValueError(
                f'Invalid annotations given of type: {type(annotations)}')


class ProjectMember(DbObject):
    user = Relationship.ToOne("User", cache=True)
    role = Relationship.ToOne("Role", cache=True)


class LabelingParameterOverride(DbObject):
    """ Customizes the order of assets in the label queue.

    Attributes:
        priority (int): A prioritization score.
        number_of_labels (int): Number of times an asset should be labeled.
    """
    priority = Field.Int("priority")
    number_of_labels = Field.Int("number_of_labels")


LabelerPerformance = namedtuple(
    "LabelerPerformance", "user count seconds_per_label, total_time_labeling "
    "consensus average_benchmark_agreement last_activity_time")
LabelerPerformance.__doc__ = (
    "Named tuple containing info about a labeler's performance.")
