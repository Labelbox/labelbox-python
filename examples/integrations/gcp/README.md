## ETl / Train / Deploy / Analyze using GCP and Labelbox

### Overview

Run ETL jobs, train models, deploy models, and track model performance all from a single service. The code deploys a service called the `coordinator`. It exposes a rest api for launching various pipelines. The coordinator only has to be deployed once and then will be controllable via the labelbox web app (WIP). This project is designed to be easily extended for custom workflows. However, we will support the following models with no additional configuration required:

1. Image Radio Classification
2. Image Checklist / Dropdown Classification
3. Image Bounding Box Detection
4. Text Radio Classification
5. Text Checklist / Dropdown Classification
6. Text Named Entity Recognition


### Usage / Requirements

1. Configure Environment:
    * Env Vars:
        - `LABELBOX_API_KEY`
        - `WEBHOOK_SECRET`
        - `GCS_BUCKET`
    * GCP Credentials
        - All jobs require a GCP service account and permissions to read / write to a GCS bucket, cloud run deployments, read / write to GCR, and access to vertex ai. Credentials must be here: `~/.config/gcloud/development-sa-creds.json`.
2. Run `./run.sh` to build the container. This also pushes the containers to gcr.
    - Note that you can optionally deploy to gcp by running `./deployment/deploy.sh`. Make sure have `GOOGLE_PROJECT` and `GOOGLE_SERVICE_ACCOUNT` env vars set before running this. There are a few more requirements that are not automated at this time (such as setting secrets).
3. Making a request to the service in another shell.  You can use `test/seed/seed_image_single_classification.py` to seed the project and then `test/test_image_classification.py` to kick off the pipeline.



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


The whole system is designed to be deployed


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

