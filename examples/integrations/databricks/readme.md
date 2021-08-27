# Databricks + Labelbox

##### Use the Labelbox Connector to easily work with unstructured data in Databricks

--------


#### labelbox_databricks_example.ipynb
* Take a DataFrame of unstructured data
* Create the dataset in Labelbox with the Connector
* Annotate in Labelbox
* Load annotations into Databricks for easy querying and model training

#### api_key_db_template.ipynb
* This is a helper notebook for users without access to the Databricks Secrets API
* Allows you to store your Labelbox API key outside of your main notebook, for better security
* We do recommend you use the Secrets API whenever possible
