"""Typed errors used across the application boundary."""

from __future__ import annotations


class ConformanceError(Exception):
    """Base class for expected application failures."""

    code = "CONFORMANCE_ERROR"

    def __init__(self, message: str, *, details: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(ConformanceError):
    """Raised when a target or policy cannot be validated."""

    code = "CONFIGURATION_ERROR"


class TransportError(ConformanceError):
    """Raised when an MCP transport cannot be established or maintained."""

    code = "TRANSPORT_ERROR"


class TransportTimeoutError(TransportError):
    """Raised when a transport operation exceeds its configured timeout."""

    code = "TRANSPORT_TIMEOUT"


class ProtocolError(ConformanceError):
    """Raised when an MCP response violates an expected protocol boundary."""

    code = "PROTOCOL_ERROR"


class EvidenceError(ConformanceError):
    """Raised when an evidence bundle cannot be written or verified."""

    code = "EVIDENCE_ERROR"
