from labelbox.orm import query
from labelbox.orm.db_object import DbObject, Updateable, BulkDeletable
from labelbox.orm.model import Entity, Field, Relationship


""" Client-side object type definitions. """


class Label(DbObject, Updateable, BulkDeletable):
    """ Label represents an assessment on a DataRow. For example one label could
    contain 100 bounding boxes (annotations).
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reviews.supports_filtering = False

    label = Field.String("label")
    seconds_to_label = Field.Float("seconds_to_label")
    agreement = Field.Float("agreement")
    benchmark_agreement = Field.Float("benchmark_agreement")
    is_benchmark_reference = Field.Boolean("is_benchmark_reference")

    project = Relationship.ToOne("Project")
    data_row = Relationship.ToOne("DataRow")
    reviews = Relationship.ToMany("Review", False)

    @staticmethod
    def bulk_delete(labels):
        """ Deletes all the given Labels.
        Args:
            labels (list of Label): The Labels to delete.
        """
        BulkDeletable._bulk_delete(labels, False)

    def create_review(self, **kwargs):
        """ Creates a Review for this label.
        Kwargs:
            Review attributes. At a minimum a `Review.score` field
            value must be provided.
        """
        Review = Entity.named("Review")
        kwargs[Review.label.name] = self
        kwargs[Review.project.name] = self.project()
        return self.client._create(Review, kwargs)

    def create_benchmark(self):
        """ Creates a Benchmark for this Label.
        Return:
            The newly created Benchmark.
        """
        query_str, params = _create_benchmark(self)
        res = self.client.execute(query_str, params)
        res = res["data"]["createBenchmark"]
        return Entity.named("Benchmark")(self.client, res)


def _create_benchmark(label):
    label_id_param = "labelId"
    query_str = """mutation CreateBenchmarkPyApi($%s: ID!) {
        createBenchmark(data: {labelId: $%s}) {%s}} """ % (
            label_id_param, label_id_param,
            query.results_query_part(Entity.named("Benchmark")))
    return query_str, {label_id_param: label.uid}
