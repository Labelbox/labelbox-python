## ETl / Train / Deploy / Analyze using GCP and Labelbox


# You need GCLOUD installed and configured

### Overview

Run ETL jobs, train models, deploy models, and track model performance all from a single service. The code deploys a service called the `coordinator` to google cloud. It exposes a rest api for launching various pipelines. The coordinator only has to be deployed once and then will be controllable via the labelbox web app (WIP). This project is designed to be easily extended for custom workflows. However, we will support the following models with no additional configuration required:

1. Image Radio Classification
2. Image Checklist / Dropdown Classification
3. Image Bounding Box Detection
4. Text Radio Classification
5. Text Checklist / Dropdown Classification
6. Text Named Entity Recognition

### Requirements

1. docker-compose installed
2. gcloud cli installed (and configured for the proper service account)


### Deployment

Deploy the coordinator service on port 8000

1. Set the following env vars locally:
    - `DEPLOYMENT_NAME`
        - This is the name that all of the google resources will use. This will enable multiple deployments. E.g. prod-training-service or dev-training-service.
    - `GCS_BUCKET`
        - GCS bucket to store all of the artifacts. If the bucket doesn't exist it will automatically be created.
    - `GOOGLE_PROJECT`
        - Google cloud project name.
    - `SERVICE_SECRET`
        - This can be anything. You will have to use the same secret when making a request to the service.
    - `GOOGLE_APPLICATION_CREDENTIALS`
        - Path to the application credentials.
    - `GOOGLE_SERVICE_ACCOUNT`
        - Google service account. Will have the following format: `<name>@<project>.iam.gserviceaccount.com`.
    - `LABELBOX_API_KEY`
2. Deploy the service
    - To the cloud: `./deployment/deploy.sh`
    - Locally: `./run.sh`


### Managing training deployments


* Delete the training deployment
    - Set `DEPLOYMENT_NAME` env vars
    - Run the `./deployment/teardown.sh` script
        - Deletes the firewall, static ip, coordinator instance and the secrets
        - The gcs bucket and gcr training artifacts, the gcr images will not be updated, and all vertex artifacts will remain.

* Updating secrets
    - Set `LABELBOX_API_KEY`, `SERVICE_SECRET`, and `DEPLOYMENT_NAME` env vars
    - Run `./deployment/reload_secrets.sh`

* Updating the coordinator
    - Change your code locally
    - Make sure the `DEPLOYMENT_NAME` env var is set, and run `deployment/reload_coordinator.sh`

* Updating containerized jobs
    - The training pipeline always uses the latest images. This means that anytime you build and push, the coordinator will use the pushed code automatically. <b>Do not push containers to GCR for a deployment that is being used in production unless you want those changes to be used</b>/.
    - Update your code locally, run `docker-compose build <container_name>`, and then `docker-compose push <container_name>`.



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
