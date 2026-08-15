"""Configuration loading at the external input boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from ..domain.errors import ConfigurationError
from .schema import LabConfig, StdioTransportConfig


def _resolve_path(value: Path | None, base_dir: Path) -> Path | None:
    """Resolve a relative path against the configuration file directory."""
    if value is None:
        return None
    return value if value.is_absolute() else (base_dir / value).resolve()


def _resolve_config_paths(config: LabConfig, base_dir: Path) -> LabConfig:
    """Return a copy with all path-bearing fields rooted at the config directory."""
    transport = config.transport
    if isinstance(transport, StdioTransportConfig):
        transport = transport.model_copy(update={"cwd": _resolve_path(transport.cwd, base_dir)})
    reports = config.reports.model_copy(
        update={"directory": _resolve_path(config.reports.directory, base_dir)}
    )
    return config.model_copy(
        update={
            "transport": transport,
            "baseline": _resolve_path(config.baseline, base_dir),
            "reports": reports,
        }
    )


def load_config(path: Path) -> LabConfig:
    """Load and validate a YAML configuration file."""
    config_path = path.expanduser().resolve()
    if not config_path.is_file():
        raise ConfigurationError(f"configuration file does not exist: {config_path}")
    try:
        raw: Any = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigurationError(f"could not read configuration: {config_path}") from exc
    if not isinstance(raw, dict):
        raise ConfigurationError("configuration root must be a mapping")
    try:
        config = LabConfig.model_validate(raw)
    except ValidationError as exc:
        raise ConfigurationError(
            "configuration validation failed",
            details={"errors": exc.errors()},
        ) from exc
    return _resolve_config_paths(config, config_path.parent)
