# Architecture

MCP Conformance Lab is intentionally a CLI-first system. Its core boundary is a read-only discovery session followed by deterministic snapshot rules and local evidence generation. The project does not require a database, message broker, hosted API, or dashboard for its MVP because the primary artifact is a portable result that belongs beside a build.

## Layers

| Layer | Responsibility | Depends on |
|---|---|---|
| Domain | Immutable models, severity/status semantics, canonicalization, safe policies, typed errors | Python and Pydantic |
| Application | Discovery, snapshot normalization, baseline comparison, orchestration | Domain and transport contracts |
| Transports | MCP SDK session lifecycle for stdio and Streamable HTTP | Official MCP Python SDK, AnyIO, HTTPX |
| Rules | Deterministic checks over a `ContractSnapshot` | Domain models and JSON Schema |
| Evidence | Atomic bundle writing, manifest verification, JSON/SARIF rendering | Domain and filesystem |
| CLI | User-facing command parsing, exit codes, and output selection | Application and Evidence |

The dependency direction is deliberate. Domain code does not import transports or CLI code. A future transport or report format can be added behind an existing application boundary without rewriting the rules. The MCP SDK is isolated in `transports/` and the discovery mapper, which reduces the cost of SDK API drift.

## Runtime flow

```text
config.yaml
    │
    ▼
validated LabConfig
    │
    ▼
transport adapter ── stdio or Streamable HTTP ──► ClientSession
    │                                                │
    └────────────────────────────────────────────────┘
                         initialize + list pages
                                      │
                                      ▼
                              ContractSnapshot
                                      │
                   canonical sort + SHA-256 digest
                                      │
                    deterministic rules + baseline diff
                                      │
                                      ▼
                    Findings ──► JSON / SARIF / evidence
```

## Contract boundaries

`LabConfig` is the external input contract. It is versioned, rejects unknown fields, resolves relative paths against the configuration file, and keeps secrets out of the file by resolving HTTP headers from environment variable names. `ContractSnapshot` is the internal compatibility boundary. It contains only public server metadata and advertised collections, and it is independent of transport-specific SDK objects.

`Finding` is the output contract. Every rule produces a machine-readable rule ID, severity, status, message, target, and optional remediation. Exit codes are computed from findings and a policy threshold; the CLI never parses human-readable text to decide success.

## Extension points

A new transport implements the same session lifecycle used by the application service. A new rule implements `ConformanceRule.evaluate(context)` and should remain deterministic over a snapshot or an explicitly bounded session operation. A new report format consumes `RunReport` rather than raw SDK objects. These boundaries make plugins possible later without requiring a plugin framework in the MVP.

## Failure flow

Configuration failures stop before process startup. Transport failures produce typed `TRANSPORT_ERROR` or `TRANSPORT_TIMEOUT` outcomes. Protocol failures remain distinct from rule failures, and evidence-write failures are fatal because an unverifiable run must not be reported as successful. The process uses non-zero exit codes for actionable findings at or above the configured `fail_on` threshold.
