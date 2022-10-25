def run(fn, model_run):
    try:
        fn()
    except Exception as e:
        model_run.update_status(error_message=error)
        pipelines[pipeline].update_status(PipelineState.FAILED,
                                          json_data['model_run_id'],
                                          error_message=str(e))
    else:
        status


def model_run(payload):

    def etl():
        payload

    run(etl)
