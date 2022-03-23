## ETl / Train / Deploy / Analyze using GCP and Labelbox

### Overview

Run ETL jobs, train models, deploy models, and track model performance all from a single service. The code deploys a service called the `coordinator` to google cloud. It exposes a rest api for launching various pipelines. The coordinator only has to be deployed once and then will be controllable via the labelbox web app (WIP). This project is designed to be easily extended for custom workflows. However, we will support the following models with no additional configuration required:

1. Image Radio Classification
2. Image Checklist / Dropdown Classification
3. Image Bounding Box Detection
4. Text Radio Classification
5. Text Checklist / Dropdown Classification
6. Text Named Entity Recognition


### Deployment

Deploy the coordinator service on port 8000

1. Set the following env vars locally:
    - `GOOGLE_SERVICE_ACCOUNT`
        - Google service account. Will have the following format: `<name>@<project>.iam.gserviceaccount.com`
    - `GCS_BUCKET`
        - GCS bucket to store all of the artifacts
    - `GOOGLE_PROJECT`
        - Google cloud project name
    - `WEBHOOK_SECRET`
        - This can be anything. You will have to use the same secret when making a request to the service
    - `LABELBOX_API_KEY`
2. Make sure python3 is in your path and `google-cloud-secret-manager` is installed. Run the below code. If it throws an error then you need to install `google-cloud-secret-manager` with pip.
    - python3 -c "from google.cloud import secretmanager"
3. Deploy the service
    - To the cloud: `./deployments/deploy.sh`
    - Locally: `./run.sh`


### Cleanup

1. Run the `./deployments/teardown.sh` script
    - This will delete the coordinator service and the ingress
2. Clean up any resources in the google cloud console including:
    - GCR images
    - Vertex resources
        - Endpoints
        - Models
        - Datasets
    - Secrets stored in secret manager
    - Resources stored in `GCS_BUCKET`


### Design

The coordinator is an api for managing etl/training/deployment jobs. The coordinator doesn't do any data processing. Instead it runs various pipelines by running containers in vertex ai. The code is organizationed such that all logic for coordinating the workflows are under `src/coordinator` and any custom jobs are defined under `src/jobs`.


Key terms:
* `Job`:
    - A job is a single task such as etl, training, deployment, or model evaluation.
    - It exposes a run method that executes the job.
* `Pipeline`:
    - A pipeline contains the logic for running a series of jobs.
    - It exposes three functions.
        1. parse_args: Used to validate the dict payload that contains the pipeline parameters
        2. run: A function that defines the behavior of the pipeline when run from the local machine


### Custom Pipelines / Extending

#### Creating Custom Jobs
* A custom job can be used to run any arbitrary job on gcp. This is not necessary if you already have a container on gcs that defines the job or the job can be run from a remote client (in this case run from the pipeline). To create the custom job do the following:
1. Create a new directory under the `jobs` directory.
2. Write the logic for the job. Include a cli to pass in any arguments.
3. Add a Dockerfile
5. Add to the docker compose
6. Add tests

#### Extending a Pipeline
1. Find the pipeline you want to extend under `coordinator/pipelines/...`
2. Create a new class that inherits from the base job class. Define an implementation for `run`.
3. Add the new job to the pipeline and update the pipeline's `run` function


#### Creating a New Pipeline
1. Copy a pipeline found under `coordinator/pipelines/...`
2. Update the logic for your new job
3. Add the job to a pipeline in `coordinator/config.py`
    * Update `pipelines` to include the new workflow
    * Add the new pipeline name `PipelineName` type as a Literal

