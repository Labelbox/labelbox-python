from labelbox import Client
from labelbox import Project
from labelbox import Dataset
import os 
import logging
import fire

os.system('clear')

client = Client(os.environ['apikey'])
project = client.get_project("ckcz6buerdyfq0855l6hoo4ot")


print(f"project name is {project.name}")

datasets = client.get_datasets(where=Dataset.name == "Bka")
dataset = list(datasets)[0]

print(f"\ndataset name is {dataset.name}")

# name EQ Sample Project AND deleted EQ False

# other_datasets = client.get_datasets(where=(Dataset.name == project.name))
other_datasets = client.get_datasets(where=(Project.name == project.name))

print(list(other_datasets))

# logging.basicConfig(level=logging.DEBUG)
# # client = Client(os.environ['apikey'])

#__________________________________________________________________
# project = client.get_project("ckd93k6zr5n0f0812yw9y33b7")
# dataset = client.get_dataset("ckdf5yf3vu48f0762f3qjpylz")

# row = list(dataset.data_rows())[0]

# row.create_metadata("TEXT","HELLO")
