import hashlib
import hmac
import os
import json
import logging
import argparse

from fastapi import FastAPI, BackgroundTasks, Header, Request, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.logger import logger
import uvicorn

from mock_pipeline import etl, train

secret = os.environ['WEBHOOK_SECRET']
logger = logging.getLogger("uvicorn")
logger.setLevel(logging.DEBUG)
app = FastAPI()

pipelines = {'bounding_box': {'etl': etl, 'train': train}}


async def run(project_id):
    logger.info("Starting ETL")
    training_file_uri = await run_in_threadpool(
        lambda: pipelines[args.pipeline]['etl'](project_id))
    logger.info(f"ETL Complete. Uploaded to {training_file_uri}")
    logger.info("Starting training")
    model_id = await run_in_threadpool(lambda: pipelines[args.pipeline]['train']
                                       (training_file_uri))
    logger.info(f"Training complete. Model id : {model_id}")
    return model_id


@app.post("/model_run")
async def model_run(request: Request,
                    background_tasks: BackgroundTasks,
                    X_Hub_Signature: str = Header(None)):
    payload = await request.body()
    computed_signature = hmac.new(secret, msg=payload,
                                  digestmod=hashlib.sha1).hexdigest()
    if X_Hub_Signature != "sha1=" + computed_signature:
        raise HTTPException(
            status_code=500,
            detail=
            "Error: computed_signature does not match signature provided in the headers"
        )

    data = json.loads(payload.decode("utf8"))
    logger.info(f"DATA {data}")
    background_tasks.add_task(run, data)


@app.get("/ping")
def health_check():
    return "pong"


if __name__ == '__main__':
    # Eventually we will support different types
    # depending on the data that is exported in the payload
    # Then we won't require users to specify the pipeline
    parser = argparse.ArgumentParser(description='Server for handling jobs')
    parser.add_argument('pipeline', choices=list(pipelines.keys()))
    parser.add_argument('--deploy',
                        default=False,
                        type=bool,
                        help='Run the server locally')
    args = parser.parse_args()

    if args.deploy:
        raise ValueError("Only local mode supported for now")

    uvicorn.run(app, host='0.0.0.0', port=8000)
