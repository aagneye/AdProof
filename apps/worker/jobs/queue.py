"""Redis job queue — enqueue pipeline runs."""

import os

import redis
from rq import Queue

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

_connection = redis.from_url(REDIS_URL)
queue = Queue("adproof-pipeline", connection=_connection)


def enqueue_run(brief_id: str, run_id: str) -> str:
    """Enqueue a pipeline job. Returns job ID."""
    job = queue.enqueue("jobs.worker.execute_run", brief_id, run_id)
    return job.id
