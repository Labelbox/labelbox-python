# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_set_labeling_parameter_overrides 1'] = [
    (
        (
            'https://api.labelbox.com/graphql'
        ,),
        {
            'data': b'{"query": "mutation SetLabelingParameterOverridesPyApi($projectId: ID!){\\n            project(where: { id: $projectId }) {setLabelingParameterOverrides\\n            (data: [{dataRow: {id: \\"1\\"}, priority: 4, numLabels: 3 },\\n{dataRow: {id: \\"2\\"}, priority: 3, numLabels: 2 },\\n{dataRow: {id: \\"3\\"}, priority: 8, numLabels: 5 }]) {success}}} ", "variables": {"projectId": "mock_id"}}',
            'headers': {
                'Accept': 'application/json',
                'Authorization': 'Bearer dummy_key',
                'Content-Type': 'application/json'
            },
            'timeout': 10.0
        }
    )
]

snapshots['test_set_labeling_parameter_overrides 2'] = [
    (
        (
            'https://api.labelbox.com/graphql'
        ,),
        {
            'data': b'{"query": "mutation SetLabelingParameterOverridesPyApi($projectId: ID!){\\n            project(where: { id: $projectId }) {setLabelingParameterOverrides\\n            (data: [{dataRow: {id: \\"1\\"}, priority: 4, numLabels: 3 },\\n{dataRow: {id: \\"2\\"}, priority: 3, numLabels: 2 },\\n{dataRow: {id: \\"3\\"}, priority: 8, numLabels: 5 }]) {success}}} ", "variables": {"projectId": "mock_id"}}',
            'headers': {
                'Accept': 'application/json',
                'Authorization': 'Bearer dummy_key',
                'Content-Type': 'application/json'
            },
            'timeout': 10.0
        }
    )
]
