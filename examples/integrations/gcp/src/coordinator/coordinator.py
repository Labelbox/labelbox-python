import hashlib
import hmac
import os
import json
import logging
import argparse
import docker
from typing import Dict, Any, Callable

from fastapi import BackgroundTasks, FastAPI, HTTPException, Header, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.logger import logger
import uvicorn
from pipelines import pipelines, pipeline_name
import time
from job import JobState, JobStatus

secret = os.environ['WEBHOOK_SECRET']

logger = logging.getLogger("uvicorn")
logger.setLevel(logging.DEBUG)
app = FastAPI()


async def run_job(fn: Callable[[Dict[str, Any]], JobStatus]) -> JobStatus:
    try:
        status = await run_in_threadpool(fn)
    except Exception as e:
        status = JobStatus(JobState.FAILED, errors=str(e))

    if status.state != JobState.SUCCESS:
        # In the future we will notify labelbox
        raise Exception(f"Job failed: {status.errors}")
    return status


async def run_local(json_data: Dict[str, Any], pipeline: pipeline_name):
    logger.info("Starting ETL.")
    status = await run_job(
        lambda: pipelines[pipeline]['etl'].run_local(json_data))
    logger.info("Starting Training.")
    await run_job(lambda: pipelines[pipeline]['train'].run_local(status.result))
    logger.info("Pipeline Ran Successfully!")
    # TODO: Notify labelbox


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
    background_tasks.add_task(run_remote if args.deploy else run_local, data,
                              data['pipeline'])


def validate_payload(data: Dict[str, str]):
    # Check that the pipeline to run
    assert 'pipeline' in data
    assert data['pipeline'] in list(pipelines.keys())


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
