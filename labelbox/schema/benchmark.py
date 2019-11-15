from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field, Relationship


class Benchmark(DbObject):
    """ Benchmarks (also known as Golden Standard) is a quality assurance tool
    for training data. Training data quality is the measure of accuracy and
    consistency of the training data. Benchmarks works by interspersing data
    to be labeled, for which there is a benchmark label, to each person labeling.
    These labeled data are compared against their respective benchmark and an
    accuracy score between 0 and 100 percent is calculated.
    """
    created_at = Field.DateTime("created_at")
    created_by = Relationship.ToOne("User", False, "created_by")
    last_activity = Field.DateTime("last_activity")
    average_agreement = Field.Float("average_agreement")
    completed_count = Field.Int("completed_count")

    reference_label = Relationship.ToOne("Label", False, "reference_label")

    def delete(self):
        query_str, params = _delete_benchmark(self.reference_label())
        self.client.execute(query_str, params)


def _delete_benchmark(label):
    label_id_param = "labelId"
    query_str = """mutation DeleteBenchmarkPyApi($%s: ID!) {
        deleteBenchmark(where: {labelId: $%s}) {id}} """ % (
            label_id_param, label_id_param)
    return query_str, {label_id_param: label.uid}
