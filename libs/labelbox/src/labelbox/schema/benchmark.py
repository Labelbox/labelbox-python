from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field, Relationship


class Benchmark(DbObject):
    """Represents a benchmark label.

    The Benchmarks tool works by interspersing data to be labeled, for
    which there is a benchmark label, to each person labeling. These
    labeled data are compared against their respective benchmark and an
    accuracy score between 0 and 100 percent is calculated.

    Attributes:
        created_at (datetime)
        last_activity (datetime)
        average_agreement (float)
        completed_count (int)

        created_by (Relationship): `ToOne` relationship to User
        reference_label (Relationship): `ToOne` relationship to Label
    """

    created_at = Field.DateTime("created_at")
    created_by = Relationship.ToOne("User", False, "created_by")
    last_activity = Field.DateTime("last_activity")
    average_agreement = Field.Float("average_agreement")
    completed_count = Field.Int("completed_count")

    reference_label = Relationship.ToOne("Label", False, "reference_label")

    def delete(self) -> None:
        label_param = "labelId"
        query_str = """mutation DeleteBenchmarkPyApi($%s: ID!) {
            deleteBenchmark(where: {labelId: $%s}) {id}} """ % (
            label_param,
            label_param,
        )
        self.client.execute(
            query_str, {label_param: self.reference_label().uid}
        )
