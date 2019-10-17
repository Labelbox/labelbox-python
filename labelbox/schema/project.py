from collections import namedtuple
from datetime import datetime, timezone
import json
import logging
import time

from labelbox import utils
from labelbox.exceptions import InvalidQueryError
from labelbox.orm import query
from labelbox.orm.db_object import DbObject, Updateable, Deletable
from labelbox.orm.model import Entity, Field, Relationship
from labelbox.pagination import PaginatedCollection


logger = logging.getLogger(__name__)


class Project(DbObject, Updateable, Deletable):
    """ A Project is a container that includes a labeling frontend, an ontology,
    datasets and labels.
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

    def create_label(self, **kwargs):
        """ Creates a label on this project.
        Kwargs:
            Label attributes. At the minimum the label `DataRow`
            and `Type` relationships and `label`, `seconds_to_label`
            fields.
        """
        # Copy-paste of Client._create code so we can inject
        # a connection to Type. Type objects are on their way to being
        # deprecated and we don't want the Py client lib user to know
        # about them. At the same time they're connected to a Label at
        # label creation in a non-standard way (connect via name).

        Label = Entity.named("Label")
        kwargs[Label.project] = self
        data = {Label.attribute(attr) if isinstance(attr, str) else attr:
                value.uid if isinstance(value, DbObject) else value
                for attr, value in kwargs.items()}

        query_str, params = query.create(Label, data)
        # Inject connection to Type
        query_str = query_str.replace("data: {",
                                      "data: {type: {connect: {name: \"Any\"}} ")
        res = self.client.execute(query_str, params)
        res = res["data"]["createLabel"]
        return Label(self.client, res)

    def labels(self, datasets=None, order_by=None):
        query_string, params = _project_labels(self, datasets, order_by)
        return PaginatedCollection(self.client, query_string, params,
                                   ["project", "labels"], Entity.named("Label"))

    def export_labels(self, timeout_seconds=60):
        """ Calls the server-side Label exporting that generates a JSON
        payload, and returns the URL to that payload.
        Args:
            timeout_seconds (float): Max waiting time, in seconds.
        Return:
            URL of the data file with this Project's labels. If the server
                didn't generate during the `timeout_seconds` period, None
                is returned.
        """
        sleep_time = 2
        query_str, id_param = _export_labels()
        while True:
            res = self.client.execute(query_str, {id_param: self.uid})[
                "data"]["exportLabels"]
            if not res["shouldPoll"]:
                return res["downloadUrl"]

            timeout_seconds -= sleep_time
            if timeout_seconds <= 0:
                return None

            logger.debug("Project '%s' label export, waiting for server...",
                         self.uid)
            time.sleep(sleep_time)

    def labeler_performance(self):
        """ Returns the labeler performances for this Project.
        Returns:
            A PaginatedCollection of LabelerPerformance objects.
        """
        query_str, params = _labeler_performance(self)

        def create_labeler_performance(client, result):
            result["user"] = Entity.named("User")(client, result["user"])
            result["lastActivityTime"] = datetime.fromtimestamp(
                result["lastActivityTime"] / 1000, timezone.utc)
            return LabelerPerformance(**{utils.snake_case(key): value
                                         for key, value in result.items()})

        return PaginatedCollection(self.client, query_str, params,
                                   ["project", "labelerPerformance"],
                                   create_labeler_performance)

    def review_metrics(self, net_score):
        """ Returns this Project's review metrics.
        Args:
            net_score (None or Review.NetScore): Indicates desired metric.
        Return:
            int, aggregation count of reviews for given net_score.
        """
        if net_score not in (None,) + tuple(Entity.named("Review").NetScore):
            raise InvalidQueryError("Review metrics net score must be either None "
                                    "or one of Review.NetScore values")
        query_str, params = _project_review_metrics(self, net_score)
        res = self.client.execute(query_str, params)
        return res["data"]["project"]["reviewMetrics"]["labelAggregate"]["count"]

    def setup(self, labeling_frontend, labeling_frontend_options):
        """ Finalizes the Project setup.
        Args:
            labeling_frontend (LabelingFrontend): The labeling frontend to use.
            labeling_frontend_options (dict or str): Labeling frontend options,
                a.k.a. project ontology. If given a `dict` it will be converted
                to `str` using `json.dumps`.
        """
        organization = self.client.get_organization()
        if not isinstance(labeling_frontend_options, str):
            labeling_frontend_options = json.dumps(labeling_frontend_options)

        LFO = Entity.named("LabelingFrontendOptions")
        labeling_frontend_options = self.client._create(
            LFO, {LFO.project: self, LFO.labeling_frontend: labeling_frontend,
                  LFO.customization_options: labeling_frontend_options,
                  LFO.organization: organization
                  })

        self.labeling_frontend.connect(labeling_frontend)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.update(setup_complete=timestamp)

    def set_labeling_parameter_overrides(self, data):
        """ Adds labeling parameter overrides to this project.
        Args:
            data (iterable): An iterable of tuples. Each tuple must contain
                (DataRow, priority, numberOfLabels) for the new override.
        Return:
            bool indicating if the operation was a success.
        """
        query_str, params = _set_labeling_parameter_overrides(self, data)
        res = self.client.execute(query_str, params)
        return res["data"]["project"]["setLabelingParameterOverrides"]["success"]

    def unset_labeling_parameter_overrides(self, data_rows):
        """ Removes labeling parameter overrides to this project.
        Args:
            data_rows (iterable): An iterable of DataRows.
        Return:
            bool indicating if the operation was a success.
        """
        query_str, params = _unset_labeling_parameter_overrides(self, data_rows)
        res = self.client.execute(query_str, params)
        return res["data"]["project"]["unsetLabelingParameterOverrides"]["success"]


class LabelingParameterOverride(DbObject):
    priority = Field.Int("priority")
    number_of_labels = Field.Int("number_of_labels")


LabelerPerformance = namedtuple(
    "LabelerPerformance", "user count seconds_per_label, total_time_labeling "
    "consensus average_benchmark_agreement last_activity_time")
LabelerPerformance.__doc__ = "Named tuple containing info about a labeler's " \
    "performance."


def _project_labels(project, datasets, order_by):
    """ Returns the query and params for getting a Project's labels
    relationship. A non-standard relationship query is used to support
    filtering on Datasets.
    Args:
        datasets (list or None): The datasets filter. If None it's
            ignored.
    Return:
        (query_string, params)
    """
    Label = Entity.named("Label")

    if datasets is not None:
        where = " where:{dataRow: {dataset: {id_in: [%s]}}}" % ", ".join(
            '"%s"' % dataset.uid for dataset in datasets)
    else:
        where = ""

    if order_by is not None:
        query.check_order_by_clause(Label, order_by)
        order_by_str = "orderBy: %s_%s" % (
            order_by[0].graphql_name, order_by[1].name.upper())
    else:
        order_by_str = ""

    query_str = """query GetProjectLabelsPyApi($project_id: ID!)
        {project (where: {id: $project_id})
            {labels (skip: %%d first: %%d%s%s) {%s}}}""" % (
        where, order_by_str, query.results_query_part(Label))
    return query_str, {"project_id": project.uid}


def _export_labels():
    """ Returns the query and ID param for exporting a Project's
    labels.
    Return:
        (query_string, id_param_name)
    """
    id_param = "projectId"
    query_str = """mutation GetLabelExportUrlPyApi($%s: ID!) {exportLabels(data:{
        projectId: $%s } ) {
        downloadUrl createdAt shouldPoll } }
    """ %  (id_param, id_param)
    return (query_str, id_param)


def _labeler_performance(project):
    project_id_param = "projectId"
    query_str = """query LabelerPerformancePyApi($%s: ID!) {
        project(where: {id: $%s}) {
            labelerPerformance(skip: %%d first: %%d) {
                count user {%s} secondsPerLabel totalTimeLabeling consensus
                averageBenchmarkAgreement lastActivityTime}
        }
    }""" % (project_id_param, project_id_param,
            query.results_query_part(Entity.named("User")))

    return query_str, {project_id_param: project.uid}


def _project_review_metrics(project, net_score):
    project_id_param = "project_id"
    net_score_literal = "None" if net_score is None else net_score.name
    query_str = """query ProjectReviewMetricsPyApi($%s: ID!){
        project(where: {id:$%s})
        {reviewMetrics {labelAggregate(netScore: %s) {count}}}
    }""" % (project_id_param, project_id_param, net_score_literal)

    return query_str, {project_id_param: project.uid}


def _set_labeling_parameter_overrides(project, data):
    """ Constructs a query for setting labeling parameter overrides.
    Args:
        project (Project): The project to set param overrides for.
            data (iterable): An iterable of tuples. Each tuple must contain
                (DataRow, priority, numberOfLabels) for the new override.
    Return:
        (query_string, query_parameters)
    """
    data_str = ",\n".join(
        "{dataRow: {id: \"%s\"}, priority: %d, numLabels: %d }" % (
            data_row.uid, priority, num_labels)
        for data_row, priority, num_labels in data)
    query_str = """mutation setLabelingParameterOverridesPyApi {
        project(where: { id: "%s" }) {
            setLabelingParameterOverrides(data: [%s]) { success } } } """ % (
                project.uid, data_str)
    return query_str, {}


def _unset_labeling_parameter_overrides(project, data_rows):
    """ Constructs a query for unsetting labeling parameter overrides.
    Args:
        project (Project): The project to set param overrides for.
        data_rows (iterable): An iterable of DataRow objects
            for which the to set as parameter overrides.
    Return:
        (query_string, query_parameters)
    """
    data_str = ",\n".join("{dataRowId: \"%s\"}" % data_row.uid
                          for data_row in data_rows)
    query_str = """mutation unsetLabelingParameterOverridesPyApi {
        project(where: { id: "%s" }) {
            unsetLabelingParameterOverrides(data: [%s]) { success } } } """ % (
                project.uid, data_str)
    return query_str, {}
