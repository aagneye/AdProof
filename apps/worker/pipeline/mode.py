"""Pipeline mode: explicit mock vs live — no silent fallback."""

from config import get_settings


def get_pipeline_mode() -> str:
    return get_settings().pipeline_mode.lower()


def is_mock_mode() -> bool:
    return get_pipeline_mode() == "mock"


def is_live_mode() -> bool:
    return get_pipeline_mode() == "live"
