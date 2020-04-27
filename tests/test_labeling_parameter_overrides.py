from snapshottest import snapshot

from conftest import MockResponse, mock_project
from labelbox import DataRow

def test_labeling_parameter_overrides(snapshot):

    mock_response = MockResponse(
        json_data={
            'message': 'success',
            'data': {
                'project': {
                    'setLabelingParameterOverrides': {
                        'success': True,
                    },
                },
            },
        },
        status_code=200)

    with mock_project(snapshot, mock_response) as project:
        project.set_labeling_parameter_overrides(
            [
                (1, 4, 3),
                (2, 3, 2),
                (3, 8, 5),
            ]
        )


    class MockDataRow(DataRow):
        def __init__(self, uid: str) -> None:
            self.uid = uid

    assert isinstance(MockDataRow(4), DataRow)
    with mock_project(snapshot, mock_response) as project:
        project.set_labeling_parameter_overrides(
            [
                (MockDataRow(1), 4, 3),
                (MockDataRow(2), 3, 2),
                (MockDataRow(3), 8, 5),
            ]
        )
