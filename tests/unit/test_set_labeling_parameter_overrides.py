'''Unit tests for project.set_labeling_parameter_overrides'''
from snapshottest import snapshot

from test_utils import MockResponse, mock_project
from labelbox import DataRow

def test_set_labeling_parameter_overrides(snapshot):
    '''Verifies network call is formatted as specified by the API contract.'''

    # mocked response from Labelbox backend
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

    # tests set_labeling_parameter_overrides can take tuples where
    # the 0th element is a uid
    with mock_project(snapshot, mock_response) as project:
        project.set_labeling_parameter_overrides(
            [
                ('1', 4, 3),
                ('2', 3, 2),
                ('3', 8, 5),
            ]
        )

    class MockDataRow(DataRow):
        '''Mock DataRow to hold uid string.'''
        def __init__(self, uid: str) -> None:
            '''Initializes with given uid for attribute access.'''
            self.uid = uid

    with mock_project(snapshot, mock_response) as project:
        project.set_labeling_parameter_overrides(
            [
                (MockDataRow('1'), 4, 3),
                (MockDataRow('2'), 3, 2),
                (MockDataRow('3'), 8, 5),
            ]
        )
