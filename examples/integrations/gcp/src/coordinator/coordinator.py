from typing import Dict, Any
import hashlib
import hmac
import json
import logging
import datetime

from fastapi import BackgroundTasks, FastAPI, HTTPException, Header, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.logger import logger
import uvicorn

from config import pipelines, PipelineName, WEBHOOK_SECRET

logger = logging.getLogger("uvicorn")
logger.setLevel(logging.DEBUG)
app = FastAPI()


async def run(json_data: Dict[str, Any], pipeline: PipelineName):
    try:
        await run_in_threadpool(pipelines[pipeline].run_local, json_data)
    except Exception as e:
        # TODO: Notify labelbox
        logger.info(f"Job failed. Error: {e}")


@app.get("/models")
async def models():
    return list(pipelines.keys())


@app.post("/project")
async def model_run(request: Request,
                    background_tasks: BackgroundTasks,
                    X_Hub_Signature: str = Header(None)):
    req = await request.body()
    computed_signature = hmac.new(WEBHOOK_SECRET.encode(),
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
    background_tasks.add_task(run, data, data['pipeline'])


def validate_payload(data: Dict[str, str]):
    valid_pipelines = list(pipelines.keys())
    if 'pipeline' not in data:
        raise KeyError(
            "Must provide `pipeline` key indicating which pipeline to run. "
            f"Should be one of: {valid_pipelines}")
    if not (data['pipeline'] in list(pipelines.keys())):
        raise ValueError(
            f"Unkonwn pipeline `{data['pipeline']}`. Expected one of {valid_pipelines}"
        )
    if 'job_name' not in data:
        data[
            'job_name'] = f'{data["pipeline"]}_{str(datetime.datetime.now()).replace(" ", "_")}'
    pipelines[data['pipeline']].parse_args(data)


@app.get("/ping")
def health_check():
    return "pong"


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
