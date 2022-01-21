## ETl / Train / Deploy / Analyze using GCP and Labelbox

#### Overview

Run ETL jobs, train and deploy models, and track the performance using this code. The code deploys a service called the `coordinator`. It exposes a rest api for launching various pipelines. The coordinator only has to be deployed once and then will be controllable via the labelbox web app (WIP). This project is designed to be easily extended for custom workflows. However, we will support the following models with no additional configuration required:

1. Image Radio Classification
2. Image Checklist / Dropdown Classification
3. Image Bounding Box Detection
4. Text Radio Classification
5. Text Checklist / Dropdown Classification
6. Text Named Entity Recognition


#### Usage / Requirements

1. Configure Environment:
    * Env Vars:
        - `LABELBOX_API_KEY`
        - `WEBHOOK_SECRET`
        - `GCS_BUCKET`
    * GCP Credentials
        - All jobs require a GCP service account and permissions to read / write to a GCS bucket, cloud run deployments, read / write to GCR, and access to vertex ai. Credentials must be here: `~/.config/gcloud/development-sa-creds.json`.
2. Run `./build.sh` to build the container
2. Making a request to the service (find an example in `test/test_local.py`) in another shell

#### Design

The coordinator is an api for managing etl/training/deployment pipelines. The coordinator doesn't do any data processing. Instead it executes stages in the pipeline by running containers in vertex ai. The code is organizationed such that all logic for coordinating the workflows are under `src/coordinator` and any standalone job is defined under `src/jobs`.

... WIP sorry :)


#### Custom Workflows / Extending

To add a new job and integrate into a new or existing pipeline please follow the following steps:

1. Define the job
    * Create a new directory under `jobs/<etl/training>/<data type>/<job name>.py`
    * Write the logic for the job. Include a cli to pass in any arguments.
    * Add a Dockerfile
    * Test to make sure this works as a stand alone script
2. Define a new job in the coordinator.
    * This should inherit from the base JobClass
    * Should live in a directory that mirriors the job directory
    * E.g. `coordinator/<etl/training>/<data type>/<job name>.py`
3. Add the job to a pipeline in `coordinator/pipeline.py`
4. Update `docker-compose.yaml` to include the new pipeline
5. Add tests



Restrictions:
1. Currently we only support training and ETL pipelines
2. All pipelines must have an ETL and training phase defined (although defining a job that doesn't do anything is valid)
3. Data is only passed 1 way (from coordinator to task)



