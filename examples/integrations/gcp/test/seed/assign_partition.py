from labelbox import Client, ModelRun
import time

model_run_id = "<SET THIS>"

client = Client(enable_experimental=True)
model_run = client._get_single(ModelRun, model_run_id)
data_row_ids = []
for mrdr in model_run.model_run_data_rows():
    data_row_ids.append(mrdr.data_row().uid)

result = client.execute("""
mutation assignDataSplitPyApi($modelRunId: ID!, $data: CreateAssignDataRowsToDataSplitTaskInput!){
      createAssignDataRowsToDataSplitTask(modelRun : {id: $modelRunId}, data: $data)
}
""", {
    'modelRunId': model_run.uid,
    'data': {
        'assignments': [{
            'split': 'TRAINING',
            'dataRowIds': data_row_ids
        }]
    }
},
                        experimental=True)

n_attempts = 10
for _ in range(n_attempts):
    time.sleep(1)
    result = client.execute("""
    query assignDataRowsToDataSplitTaskStatusPyApi($task_id: ID!){assignDataRowsToDataSplitTaskStatus(
      where: {id : $task_id}
        ){status errorMessage}}
      """, {'task_id': result['createAssignDataRowsToDataSplitTask']},
                            experimental=True)
    print(result)
