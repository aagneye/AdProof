"""Genblaze replay wrapper — fork runs with optional step overrides."""


def replay_run(run_id: str, overrides: dict | None = None) -> str:
    """Replay a run from stored manifest. Returns new run_id."""
    raise NotImplementedError
