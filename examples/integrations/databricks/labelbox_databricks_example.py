# Databricks notebook source
# MAGIC %md
# MAGIC # Labelbox Connector for Databricks Tutorial Notebook

# COMMAND ----------

# MAGIC %md
# MAGIC #### Pre-requisites
# MAGIC 1. This tutorial notebook requires a Lablbox API Key. Please login to your [Labelbox Account](app.labelbox.com) and generate an [API Key](https://app.labelbox.com/account/api-keys)
# MAGIC 2. A few cells below will install the Labelbox SDK and Connector Library. This install is notebook-scoped and will not affect the rest of your cluster. 
# MAGIC 3. Please make sure you are running at least the latest LTS version of Databricks. 
# MAGIC 
# MAGIC #### Notebook Preview
# MAGIC This notebook will guide you through these steps: 
# MAGIC 1. Connect to Labelbox via the SDK 
# MAGIC 2. Create a labeling dataset from a table of unstructured data in Databricks
# MAGIC 3. Programmatically set up an ontology and labeling project in Labelbox
# MAGIC 4. Load Bronze and Silver annotation tables from an example labeled project 
# MAGIC 5. Additional cells describe how to handle video annotations and use Labelbox Diagnostics and Catalog 
# MAGIC 
# MAGIC Additional documentation links are provided at the end of the notebook.

# COMMAND ----------

# MAGIC %md
# MAGIC Thanks for trying out the Databricks and Labelbox Connector! You or someone from your organization signed up for a Labelbox trial through Databricks Partner Connect. This notebook was loaded into your Shared directory to help illustrate how Labelbox and Databricks can be used together to power unstructured data workflows. 
# MAGIC 
# MAGIC Labelbox can be used to rapidly annotate a variety of unstructured data from your Data Lake ([images](https://labelbox.com/product/image), [video](https://labelbox.com/product/video), [text](https://labelbox.com/product/text), and [geospatial tiled imagery](https://docs.labelbox.com/docs/tiled-imagery-editor)) and the Labelbox Connector for Databricks makes it easy to bring the annotations back into your Lakehouse environment for AI/ML and analytical workflows. 
# MAGIC 
# MAGIC If you would like to watch a video of the workflow, check out our [Data & AI Summit Demo](https://databricks.com/session_na21/productionizing-unstructured-data-for-ai-and-analytics). 
# MAGIC 
# MAGIC 
# MAGIC <img src="https://labelbox.com/static/images/partnerships/collab-chart.svg" alt="example-workflow" width="800"/>
# MAGIC 
# MAGIC <h5>Questions or comments? Reach out to us at [ecosystem+databricks@labelbox.com](mailto:ecosystem+databricks@labelbox.com)

# COMMAND ----------

# DBTITLE 1,Install Labelbox Library & Labelbox Connector for Databricks
# MAGIC %pip install labelbox labelspark

# COMMAND ----------

#This will import Koalas or Pandas-on-Spark based on your DBR version. 
from pyspark import SparkContext
from packaging import version
sc = SparkContext.getOrCreate()
if version.parse(sc.version) < version.parse("3.2.0"):
  import databricks.koalas as pd 
  needs_koalas = True  
else:
  import pyspark.pandas as pd
  needs_koalas = False

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configure the SDK
# MAGIC 
# MAGIC Now that Labelbox and the Databricks libraries have been installed, you will need to configure the SDK. You will need an API key that you can create through the app [here](https://app.labelbox.com/account/api-keys). You can also store the key using Databricks Secrets API. The SDK will attempt to use the env var `LABELBOX_API_KEY`

# COMMAND ----------

from labelbox import Client, Dataset
from labelbox.schema.ontology import OntologyBuilder, Tool, Classification, Option
import labelspark

API_KEY = "" 

if not(API_KEY):
  raise ValueError("Go to Labelbox to get an API key")
  
client = Client(API_KEY)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Fetch seed data
# MAGIC 
# MAGIC Next we'll load a demo dataset into a Spark table so you can see how to easily load assets into Labelbox via URL. For simplicity, you can get a Dataset ID from Labelbox and we'll load those URLs into a Spark table for you (so you don't need to worry about finding data to get this demo notebook to run). Below we'll grab the "Example Nature Dataset" included in Labelbox trials.
# MAGIC 
# MAGIC Also, Labelbox has native support for AWS, Azure, and GCP cloud storage. You can connect Labelbox to your storage via [Delegated Access](https://docs.labelbox.com/docs/iam-delegated-access) and easily load those assets for annotation. For more information, you can watch this [video](https://youtu.be/wlWo6EmPDV4).

# COMMAND ----------

sample_dataset = next(client.get_datasets(where=(Dataset.name == "Example Nature Dataset")))
sample_dataset.uid

# COMMAND ----------

# can parse the directory and make a Spark table of image URLs
SAMPLE_TABLE = "sample_unstructured_data"

tblList = spark.catalog.listTables()

if not any([table.name == SAMPLE_TABLE for table in tblList]):
   
  df = pd.DataFrame([
    {
      "external_id": dr.external_id,
      "row_data": dr.row_data
    } for dr in sample_dataset.data_rows()
  ]).to_spark()
  df.registerTempTable(SAMPLE_TABLE)
  print(f"Registered table: {SAMPLE_TABLE}")

# COMMAND ----------

# MAGIC %md
# MAGIC You should now have a temporary table "sample_unstructured_data" which includes the file names and URLs for some demo images. We're going to share this table with Labelbox using the Labelbox Connector for Databricks!

# COMMAND ----------

display(sqlContext.sql(f"select * from {SAMPLE_TABLE} LIMIT 5"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create a Labeling Project
# MAGIC 
# MAGIC Projects are where teams create labels. A project is requires a dataset of assets to be labeled and an ontology to configure the labeling interface.
# MAGIC 
# MAGIC ### Step 1: Create a dataaset
# MAGIC 
# MAGIC The [Labelbox Connector for Databricks](https://pypi.org/project/labelspark/) expects a spark table with two columns; the first column "external_id" and second column "row_data"
# MAGIC 
# MAGIC external_id is a filename, like "birds.jpg" or "my_video.mp4"
# MAGIC 
# MAGIC row_data is the URL path to the file. Labelbox renders assets locally on your users' machines when they label, so your labeler will need permission to access that asset. 
# MAGIC 
# MAGIC Example: 
# MAGIC 
# MAGIC | external_id | row_data                             |
# MAGIC |-------------|--------------------------------------|
# MAGIC | image1.jpg  | https://url_to_your_asset/image1.jpg |
# MAGIC | image2.jpg  | https://url_to_your_asset/image2.jpg |
# MAGIC | image3.jpg  | https://url_to_your_asset/image3.jpg |

# COMMAND ----------

unstructured_data = spark.table(SAMPLE_TABLE)

demo_dataset = labelspark.create_dataset(client, unstructured_data, name = "Databricks Demo Dataset")

# COMMAND ----------

print("Open the dataset in the App")
print(f"https://app.labelbox.com/data/{demo_dataset.uid}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 2: Create a project
# MAGIC 
# MAGIC You can use the labelbox SDK to build your ontology (we'll do that next) You can also set your project up entirely through our website at app.labelbox.com.
# MAGIC 
# MAGIC Check out our [ontology creation documentation.](https://docs.labelbox.com/docs/configure-ontology)

# COMMAND ----------

# Create a new project
project_demo = client.create_project(name="Labelbox and Databricks Example")
project_demo.datasets.connect(demo_dataset)  # add the dataset to the queue

ontology = OntologyBuilder()

tools = [
  Tool(tool=Tool.Type.BBOX, name="Frog"),
  Tool(tool=Tool.Type.BBOX, name="Flower"),
  Tool(tool=Tool.Type.BBOX, name="Fruit"),
  Tool(tool=Tool.Type.BBOX, name="Plant"),
  Tool(tool=Tool.Type.SEGMENTATION, name="Bird"),
  Tool(tool=Tool.Type.SEGMENTATION, name="Person"),
  Tool(tool=Tool.Type.SEGMENTATION, name="Sleep"),
  Tool(tool=Tool.Type.SEGMENTATION, name="Yak"),
  Tool(tool=Tool.Type.SEGMENTATION, name="Gemstone"),
]
for tool in tools: 
  ontology.add_tool(tool)

conditions = ["clear", "overcast", "rain", "other"]

weather_classification = Classification(
    class_type=Classification.Type.RADIO,
    instructions="what is the weather?", 
    options=[Option(value=c) for c in conditions]
)  
ontology.add_classification(weather_classification)


# Setup editor
for editor in client.get_labeling_frontends():
    if editor.name == 'Editor':
        project_demo.setup(editor, ontology.asdict()) 

print("Project Setup is complete.")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 3: Go label data

# COMMAND ----------

print("Open the project to start labeling")
print(f"https://app.labelbox.com/projects/{project_demo.uid}/overview")

# COMMAND ----------

raise ValueError("Go label some data before continuing")

# COMMAND ----------

# MAGIC %md
# MAGIC ##Exporting labels/annotations
# MAGIC 
# MAGIC After creating labels in Labelbox you can export them to use in Databricks for model training and analysis.

# COMMAND ----------

LABEL_TABLE = "exported_labels"

# COMMAND ----------

labels_table = labelspark.get_annotations(client, project_demo.uid, spark, sc)
labels_table.registerTempTable(LABEL_TABLE)
display(labels_table)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Other features of Labelbox
# MAGIC 
# MAGIC <h3> [Model Assisted Labeling](https://docs.labelbox.com/docs/model-assisted-labeling) </h3>
# MAGIC Once you train a model on your initial set of unstructured data, you can plug that model into Labelbox to support a Model Assisted Labeling workflow. Review the outputs of your model, make corrections, and retrain with ease! You can reduce future labeling costs by >50% by leveraging model assisted labeling.
# MAGIC 
# MAGIC <img src="https://files.readme.io/4c65e12-model-assisted-labeling.png" alt="MAL" width="800"/>
# MAGIC 
# MAGIC <h3> [Catalog](https://docs.labelbox.com/docs/catalog) </h3>
# MAGIC Once you've created datasets and annotations in Labelbox, you can easily browse your datasets and curate new ones in Catalog. Use your model embeddings to find images by similarity search. 
# MAGIC 
# MAGIC <img src="https://files.readme.io/14f82d4-catalog-marketing.jpg" alt="Catalog" width="800"/>
# MAGIC 
# MAGIC <h3> [Model Diagnostics](https://labelbox.com/product/model-diagnostics) </h3>
# MAGIC Labelbox complements your MLFlow experiment tracking with the ability to easily visualize experiment predictions at scale. Model Diagnostics helps you quickly identify areas where your model is weak so you can collect the right data and refine the next model iteration. 
# MAGIC 
# MAGIC <img src="https://images.ctfassets.net/j20krz61k3rk/4LfIELIjpN6cou4uoFptka/20cbdc38cc075b82f126c2c733fb7082/identify-patterns-in-your-model-behavior.png" alt="Diagnostics" width="800"/>

# COMMAND ----------

# DBTITLE 1,More Info
# MAGIC %md
# MAGIC While using the Labelbox Connector for Databricks, you will likely use the Labelbox SDK (e.g. for programmatic ontology creation). These resources will help familiarize you with the Labelbox Python SDK: 
# MAGIC * [Visit our docs](https://labelbox.com/docs/python-api) to learn how the SDK works
# MAGIC * Checkout our [notebook examples](https://github.com/Labelbox/labelspark/tree/master/notebooks) to follow along with interactive tutorials
# MAGIC * view our [API reference](https://labelbox.com/docs/python-api/api-reference).
# MAGIC 
# MAGIC <h4>Questions or comments? Reach out to us at [ecosystem+databricks@labelbox.com](mailto:ecosystem+databricks@labelbox.com)

# COMMAND ----------

# MAGIC %md
# MAGIC Copyright Labelbox, Inc. 2021. The source in this notebook is provided subject to the [Labelbox Terms of Service](https://docs.labelbox.com/page/terms-of-service).  All included or referenced third party libraries are subject to the licenses set forth below.
# MAGIC 
# MAGIC |Library Name|Library license | Library License URL | Library Source URL |
# MAGIC |---|---|---|---|
# MAGIC |Labelbox Python SDK|Apache-2.0 License |https://github.com/Labelbox/labelbox-python/blob/develop/LICENSE|https://github.com/Labelbox/labelbox-python
# MAGIC |Labelbox Connector for Databricks|Apache-2.0 License |https://github.com/Labelbox/labelspark/blob/master/LICENSE|https://github.com/Labelbox/labelspark
# MAGIC |Python|Python Software Foundation (PSF) |https://github.com/python/cpython/blob/master/LICENSE|https://github.com/python/cpython|
# MAGIC |Apache Spark|Apache-2.0 License |https://github.com/apache/spark/blob/master/LICENSE|https://github.com/apache/spark|
