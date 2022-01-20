import hashlib
import hmac
import os
import json
import logging
import argparse
import docker
from typing import Dict
from google.cloud import storage

from fastapi import FastAPI, BackgroundTasks, Header, Request, HTTPException, Depends
from fastapi.concurrency import run_in_threadpool
from fastapi.logger import logger
import uvicorn
from pipelines import pipelines
import time
from job import JobStatus

docker_client = docker.from_env()

secret = os.environ['WEBHOOK_SECRET']
lb_api_key = os.environ['LABELBOX_API_KEY']
gcs_bucket = os.environ['GCS_BUCKET']
# Check that google application creds exist. Make sure they have the right permissions too...
# # Verify / GOOGLE_APPLICATION_CREDENTIALS

logger = logging.getLogger("uvicorn")
logger.setLevel(logging.DEBUG)
app = FastAPI()


async def run_local(project_id, pipeline):
    logger.info("Starting ETL")

    nowgmt = time.strftime("%Y-%m-%d_%H:%M:%S", time.gmtime())
    gcs_key = f'etl/bounding-box/{nowgmt}.jsonl'

    status = await run_in_threadpool(
        lambda: pipelines[pipeline]['etl'].run_local(
            project_id, gcs_bucket, gcs_key, lb_api_key, docker_client))

    if status != JobStatus.SUCCESS:
        # In the future we will notify labelbox
        raise Exception("Job failed..")

    training_file_uri = f"gs://{gcs_bucket}/{gcs_key}"

    logger.info("ETL Complete. Uploaded to %s", training_file_uri)
    model_id = await run_in_threadpool(
        lambda: pipelines[pipeline]['train'].run_local(training_file_uri))
    logger.info("Training complete. Model id : %s", model_id)

    return model_id


async def run_remote(*args, **kwargs):
    raise NotImplementedError("")


@app.get("/models")
async def models():
    return list(pipelines.keys())


@app.post("/project")
async def model_run(request: Request,
                    background_tasks: BackgroundTasks,
                    X_Hub_Signature: str = Header(None)):
    req = await request.body()
    computed_signature = hmac.new(secret.encode(),
                                  msg=req,
                                  digestmod=hashlib.sha1).hexdigest()
    if X_Hub_Signature != "sha1=" + computed_signature:
        raise HTTPException(
            status_code=500,
            detail=
            "Error: computed_signature does not match signature provided in the headers"
        )
    data = json.loads(req.decode("utf8"))
    validate_payload(data)
    background_tasks.add_task(run_remote if args.deploy else run_local,
                              data['project_id'], data['model'])


def validate_payload(data: Dict[str, str]):
    # Temporary check until the export payload is finalized
    assert 'project_id' in data
    assert 'model' in data
    assert data['model'] in list(pipelines.keys())


@app.get("/ping")
def health_check():
    return "pong"


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Server for handling jobs')
    # TODO: Optionally support directly running a pipeline.
    parser.add_argument('--deploy',
                        default=False,
                        required=False,
                        type=bool,
                        help='Run the server on google cloud')
    # Add command for rebuild / push
    args = parser.parse_args()

    if args.deploy:
        raise ValueError("Only local mode supported for now")

    uvicorn.run(app, host='0.0.0.0', port=8000)
