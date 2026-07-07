"""Job worker — consumes queue, runs pipeline, updates DB."""

import sys


def execute_run(brief_id: str, run_id: str):
    """Called by RQ worker to execute a pipeline run."""
    from pipeline.ad_pipeline import run_pipeline

    # TODO: load brief from DB, update run status, call pipeline
    run_pipeline(brief_id=brief_id, run_id=run_id, brief_text="")


if __name__ == "__main__":
    from rq import Worker
    from jobs.queue import _connection, queue

    worker = Worker([queue], connection=_connection)
    worker.work()
