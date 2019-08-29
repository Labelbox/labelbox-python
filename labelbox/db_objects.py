import logging
import json
import time

from labelbox import query, utils
from labelbox.schema import Field, DbObject


""" Defines client-side objects representing database content. """


logger = logging.getLogger(__name__)


def _to_many(destination_type_name, filter_deleted, relationship_name=None):
    """ Creates a method to be used within a DbObject subtype for
    getting DB objects related to so source DB object in a to-many
    relationship.

    Args:
        destination_type_name (str): Name of the DbObject subtype that's
            on the other side of the relationship. Name is used instead
            of the type itself because the type might not be defined in
            the moment this function is called.
        filter_deleted (bool): If or not an implicit `where` clause should
            be added containing {`deleted`: false}. Required in some cases,
            but not available in others.
        relationship_name (str): Name of the relationship to expand. If
            None, then it's derived from `destionation_type_name` by
            converting to camelCase and adding "s".

    Return:
        A callable that accepts the following arguments:
            self (DbObject): source of the relationship expansion
            where (None, Comparison or LogicalExpression): The filtering
                clause.
            order_by (None or (Field, Field.Order)): The sorting clause.
        The callable returns an iterable of DbObjects.
    """
    if relationship_name is None:
        relationship_name = utils.camel_case(destination_type_name) + "s"

    def expansion(self, where=None, order_by=None):
        destination_type = next(
            t for t in DbObject.__subclasses__()
            if t.__name__.split(".")[-1] == destination_type_name)

        if filter_deleted:
            not_deleted = destination_type.deleted == False
            where = not_deleted if where is None else where & not_deleted

        query_string, params = query.relationship(
            self, relationship_name, destination_type, True, where, order_by)
        return query.PaginatedCollection(
            self.client, query_string, params,
            [utils.camel_case(type(self).type_name()), relationship_name],
            destination_type)

    return expansion


def _to_one(destination_type_name, relationship_name=None):
    """ Creates a method to be used within a DbObject subtype for
    getting a DB object related to so source DB object in a to-one
    relationship.

    Args:
        destination_type_name (str): Name of the DbObject subtype that's
            on the other side of the relationship. Name is used instead
            of the type itself because the type might not be defined in
            the moment this function is called.
        relationship_name (str): Name of the relationship to expand. If
            None, then it's derived from `destionation_type_name` by
            converting to camelCase.

    Return:
        A callable that accepts a single argument: the DB object that
            is the source of the relationship expansion. It returns a callable
            used for querying a to-one relationship.
    """
    if relationship_name is None:
        relationship_name = utils.camel_case(destination_type_name)

    def expansion(self):
        destination_type = next(
            t for t in DbObject.__subclasses__()
            if t.__name__.split(".")[-1] == destination_type_name)

        query_string, params = query.relationship(
            self, relationship_name, destination_type, False, None, None)
        result = self.client.execute(query_string, params)["data"]
        result = result[utils.camel_case(type(self).type_name())]
        result = result[relationship_name]
        return destination_type(self.client, result)

    return expansion


class Project(DbObject):
    name = Field.String("name")
    description = Field.String("description")
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    setup_complete = Field.DateTime("setup_complete")

    # Relationships
    datasets = _to_many("Dataset", True)

    # TODO Relationships
    # organization
    # createdBy
    # datasets
    # labeledDatasets
    # labels
    # ...a lot more, define which are required for v0.1

    # TODO Mutable (fetched) attributes
    # ...many, define which are required for v0.1


class Dataset(DbObject):
    name = Field.String("name")
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")

    # Relationships
    projects = _to_many("Project", True)
    data_rows = _to_many("DataRow", False)

    def create_data_rows(self, items):
        """ Creates multiple DataRow objects based on the given items.
        Each element in `items` can be either a `str` or a `dict`. If
        it's a `str`, then it's interpreted as a file path. The file
        is uploaded to Labelbox and a DataRow referencing it is created.
        If an item is a `dict`, then it should map `DataRow` fields to values.
        At the minimum it must contain a `DataRow.row_data` key and value.

        Args:
            items (iterable of (dict or str)): See above for details.
        Return:
            Task representing the data import on the server side. The Task
            can be used for inspecting task progress and waiting until it's done.
        Raise:
            InvalidQueryError: if the `items` parameter does not conform to
                the specification above.
            MalformedRequestError: if the server did not accept the DataRow
                creation request.
            ResourceNotFoundError: if unable to retrieve the Task based on the
                task_id of the import process. This could imply that the import
                failed.
        """
        def convert_item(item):
            if isinstance(item, str):
                with open(item, "rb") as f:
                    item_data = f.read()
                item_url = self.client.upload_data(item_data)
                # Convert item from str into a dict so it gets processed
                # like all other dicts.
                item = {DataRow.row_data: item_url,
                        DataRow.external_id: item}

            if DataRow.row_data not in item:
                raise InvalidQueryError(
                    "DataRow.row_data missing when creating DataRow.")

            invalid_keys = set(item) - set(DataRow.fields())
            if invalid_keys:
                raise InvalidQueryError(
                    "Invalid fields found when creating DataRow: %r" % invalid_keys)

            # Item is valid, convert it to a dict {graphql_field_name: value}
            # Need to change the name of DataRow.row_data to "data"
            return {"data" if key == DataRow.row_data else key.graphql_name: value
                    for key, value in item.items()}

        # Prepare and upload the desciptor file
        data = json.dumps([convert_item(item) for item in items])
        descriptor_url = self.client.upload_data(data)

        # Create data source
        res = self.client.execute(*query.create_data_rows(self.uid, descriptor_url))
        res = res["data"]["appendRowsToDataset"]

        if not res["accepted"]:
            raise MalformedRequestError(
                "Server did not accept DataRow creation request", data)

        # Fetch and return the task.
        task_id = res["taskId"]
        user = self.client.get_user()
        task = list(user.created_tasks(where=Task.uid == task_id))
        # Cache user in a private variable as the relationship can't be
        # resolved due to server-side limitations (see Task.created_by)
        # for more info.
        if len(task) != 1:
            raise ResourceNotFoundError(Task, task_id)
        task = task[0]
        task._user = user
        return task

    # TODO Relationships
    # organization
    # createdBy
    # projects
    # dataRows

    # TODO Fetched attributes
    # rowCount
    # createdLabelCount


class DataRow(DbObject):
    external_id = Field.String("external_id")
    row_data = Field.String("row_data")
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")

    # Relationships
    dataset = _to_one("Dataset")

    # TODO other attributes


class User(DbObject):
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    email = Field.String("email")
    name = Field.String("nickname")
    nickname = Field.String("name")

    # Relationships
    organization = _to_one("Organization")
    created_tasks = _to_many("Task", False, "createdTasks")

    # TODO other attributes


class Organization(DbObject):
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    name = Field.String("name")

    # Relationships
    users = _to_many("User", False)

    # TODO other attributes


class Task(DbObject):

    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    name = Field.String("name")
    status = Field.String("status")
    completion_percentage = Field.Float("completion_percentage")

    # Relationships

    # "created_by" can't be treated as a relationship because there's
    # currently no way on the server to make a query starting from
    # a single task.
    # created_by = _to_one("User", "createdBy")

    def refresh(self):
        """ Refreshes Task data from the server. """
        tasks = list(self._user.created_tasks(where=Task.uid == self.uid))
        if len(tasks) != 1:
            raise ResourceNotFoundError(Task, task_id)
        for field in self.fields():
            setattr(self, field.name, getattr(tasks[0], field.name))

    def wait_till_done(self, timeout_seconds=3600, check_frequency_seconds=1):
        """ Waits until the task is completed. Periodically queries the server
        to update the task attributes.
        Args:
            timeout_seconds (float): Maximum time this method can block, in
                seconds. Defaults to one hour.
            check_frequency_seconds (float): Sleep time between two checks,
                in seconds. Defaults to one second.
        """
        while True:
            if self.status != "IN_PROGRESS":
                return
            sleep_time_seconds = min(check_frequency_seconds, timeout_seconds)
            logger.debug("Task.wait_till_done sleeping for %.2f seconds" %
                         sleep_time_seconds)
            if sleep_time_seconds <= 0:
                break
            timeout_seconds -= check_frequency_seconds
            time.sleep(sleep_time_seconds)
            self.refresh()

    # TODO other attributes
