"""
SDK4.0 Datarow & Dataset modules demo
"""

# %%
import sys
sys.path.append('..')
import labelbox_dev as lb # use the experimental package
import uuid

API_KEY = ""
lb.Session.initialize(api_key=API_KEY)

# Create
dataset = lb.dataset.create(
    {
      "name": 'image_dataset', 
      "description": "image dataset"
    }
)
print(dataset)

# %%
# Error case: if the user input is not valid (name is not a str), then an error will be thrown
lb.dataset.create(
    {
      "name": 123, 
      "description": "this is wrong and should not be created"
    }
)

# %%
# Update the dataset name or description
dataset.update(
    {
      "name": "updated image_dataset", 
      "description": "updated description"
    }
)
print(dataset)

# %%
# Get by id 
print(lb.dataset.get_by_id(dataset.id))

# Get by name
# To be implemented

# Delete
dataset.delete()

# Error case: confirm it is indeed deleted and cannot be found
print(lb.dataset.get_by_id(dataset.id))

#%%
"""## DataRow Module"""

assets = [
  {
    "row_data": "https://storage.googleapis.com/labelbox-datasets/image_sample_data/image-sample-1.jpg",
    "global_key": "https://storage.googleapis.com/labelbox-datasets/image_sample_data/image-sample-1.jpg" + str(uuid.uuid4()),
    "media_type": "IMAGE",
    "metadata": [{"schema_id": "cko8s9r5v0001h2dk9elqdidh", "value": "tag_string"}],
    "attachments": [{"type": "IMAGE_OVERLAY", "value": "https://storage.googleapis.com/labelbox-sample-datasets/Docs/rgb.jpg", "name": "RGB" }]
  },
  {
    "row_data": "https://storage.googleapis.com/labelbox-datasets/image_sample_data/image-sample-2.jpg",
    "global_key": "https://storage.googleapis.com/labelbox-datasets/image_sample_data/image-sample-2.jpg" + str(uuid.uuid4()),
    "media_type": "IMAGE",
    "metadata": [{"schema_id": "cko8s9r5v0001h2dk9elqdidh", "value": "tag_string"}],
    "attachments": [{"type": "TEXT_URL", "value": "https://storage.googleapis.com/labelbox-sample-datasets/Docs/text_attachment.txt"}]
  }
]

dataset = lb.dataset.create({"name": 'image_dataset', "description": "image dataset"})

# Create a single data row
datarow = lb.data_row.create_one(dataset_id=dataset.id, data_row=
          {
            "row_data": "https://storage.googleapis.com/labelbox-datasets/image_sample_data/image-sample-1.jpg",
            "global_key": "https://storage.googleapis.com/labelbox-datasets/image_sample_data/image-sample-1.jpg" + str(uuid.uuid4()),
            "media_type": "IMAGE",
            "metadata": [{"schema_id": "cko8s9r5v0001h2dk9elqdidh", "value": "tag_string"}],
            "attachments": [{"type": "IMAGE_OVERLAY", "value": "https://storage.googleapis.com/labelbox-sample-datasets/Docs/rgb.jpg", "name": "RGB" }]
          })
print(datarow)

# Bulk upload data rows 
task = lb.data_row.create(dataset_id=dataset.id, data_rows=assets, run_async=True)
task.wait_until_done() # Discussion: should this mean processed? ideally yes, because batch management, model run, etc all depends on datarow being fully processed. 
print(task.errors)
print(task.results)

# Error case: upload the same datarows again will have errors due to duplicate global keys
task_2 = lb.data_row.create(dataset_id=dataset.id, data_rows=assets, run_async=True)
task_2.wait_until_done()
print(task_2.errors)

# Get data row(s) by id
data_row_ids = [res['id'] for res in task.results['created_data_rows']]

data_row = lb.data_row.get_by_id(data_row_ids[0])
print(data_row)

get_dr_task = lb.data_row.get_by_ids(data_row_ids, run_async=True)
get_dr_task.wait_until_done()
print(get_dr_task.errors)
print(get_dr_task.results)

# Get data row(s) by global key
data_row_global_keys = [res['global_key'] for res in task.results['created_data_rows']]
print(data_row_global_keys)

data_rows = lb.data_row.get_by_global_keys(data_row_global_keys)
print(data_rows)

# Update data rows - here we will update global keys of data rows in first task
for d in data_rows:
  data_row = lb.data_row.get_by_id(d.id) # Get data row by id
  data_row.update({"global_key": str(uuid.uuid4())})

# now you can rerun the above task_2 upload cell again and it should work since global keys have been uploaded.

# Delete a data row
for result in task.results['created_data_rows']:
  data_row = lb.data_row.get_by_id(result['id'])
  data_row.delete()
# %%
