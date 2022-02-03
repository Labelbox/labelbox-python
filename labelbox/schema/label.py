from typing import TYPE_CHECKING

from labelbox.orm import query
from labelbox.orm.db_object import DbObject, Updateable, BulkDeletable
from labelbox.orm.model import Entity, Field, Relationship

if TYPE_CHECKING:
    from labelbox import Benchmark, Review
""" Client-side object type definitions. """


class Label(DbObject, Updateable, BulkDeletable):
    """ Label represents an assessment on a DataRow. For example one label could
    contain 100 bounding boxes (annotations).

    Attributes:
        label (str)
        seconds_to_label (float)
        agreement (float)
        benchmark_agreement (float)
        is_benchmark_reference (bool)

        project (Relationship): `ToOne` relationship to Project
        data_row (Relationship): `ToOne` relationship to DataRow
        reviews (Relationship): `ToMany` relationship to Review
        created_by (Relationship): `ToOne` relationship to User

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reviews.supports_filtering = False

    label = Field.String("label")
    seconds_to_label = Field.Float("seconds_to_label")
    agreement = Field.Float("agreement")
    benchmark_agreement = Field.Float("benchmark_agreement")
    is_benchmark_reference = Field.Boolean("is_benchmark_reference")
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")

    project = Relationship.ToOne("Project")
    data_row = Relationship.ToOne("DataRow")
    reviews = Relationship.ToMany("Review", False)
    created_by = Relationship.ToOne("User", False, "created_by")

    @staticmethod
    def bulk_delete(labels) -> None:
        """ Deletes all the given Labels.

        Args:
            labels (list of Label): The Labels to delete.
        """
        BulkDeletable._bulk_delete(labels, False)

    def create_review(self, **kwargs) -> "Review":
        """ Creates a Review for this label.

        Args:
            **kwargs: Review attributes. At a minimum, a `Review.score` field value must be provided.
        """
        kwargs[Entity.Review.label.name] = self
        kwargs[Entity.Review.project.name] = self.project()
        return self.client._create(Entity.Review, kwargs)

    def create_benchmark(self) -> "Benchmark":
        """ Creates a Benchmark for this Label.

        Returns:
            The newly created Benchmark.
        """
        label_id_param = "labelId"
        query_str = """mutation CreateBenchmarkPyApi($%s: ID!) {
            createBenchmark(data: {labelId: $%s}) {%s}} """ % (
            label_id_param, label_id_param,
            query.results_query_part(Entity.Benchmark))
        res = self.client.execute(query_str, {label_id_param: self.uid})
        return Entity.Benchmark(self.client, res["createBenchmark"])
