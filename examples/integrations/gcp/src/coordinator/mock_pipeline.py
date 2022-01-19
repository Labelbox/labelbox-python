from time import sleep


def etl(project_id: str) -> str:
    sleep(2)
    gcs_uri = "gcs://fake-location/..."
    return gcs_uri


def train(training_file: str) -> str:
    sleep(2)
    vertex_model_id = "123"
    return vertex_model_id
