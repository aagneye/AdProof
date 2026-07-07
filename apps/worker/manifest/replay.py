"""Fork/replay helpers for pipeline runs."""

from sqlalchemy.orm import Session

from pipeline.runner import execute_run


def execute_fork(
    db: Session,
    brief_id: str,
    run_id: str,
    fork_override: dict | None = None,
) -> None:
    """Execute pipeline on an already-created child run."""
    execute_run(db, brief_id, run_id, fork_override=fork_override)
