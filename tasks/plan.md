# Implementation Plan: MCP Conformance Lab

## Overview

**MCP Conformance Lab** هو أداة CLI وPython library لاختبار خوادم Model Context Protocol قبل الدمج أو النشر. يكتشف الخادم عبر stdio أو Streamable HTTP، يبني contract snapshot canonical، يشغّل مجموعة اختبارات حتمية وآمنة على الأدوات والموارد وPrompts وقدرات البروتوكول، يقارن النتيجة مع baseline اختياري، ثم يصدر findings وevidence bundle بصيغة JSON وSARIF. المنتج local-first؛ لا يرسل بيانات الخادم إلى خدمة خارجية، ولا يستخدم LLM كحكم أساسي.

## Product Vision and Scope

المستخدم المستهدف هو مطور MCP أو فريق AI platform أو maintainer يريد أن يعرف أن الخادم يطابق العقد المعلنة وأن التغييرات لا تسبب regression. القيمة الأساسية هي تحويل اختبار خادم MCP من جلسة يدوية في Inspector إلى بوابة قابلة للتكرار في GitHub Actions.

### MVP

1. دعم `stdio` وStreamable HTTP عبر adapters واضحة.
2. اكتشاف `initialize` و`tools/list` و`resources/list` و`prompts/list` مع التحقق من شكل الاستجابات.
3. إنشاء snapshot canonical مع digest ثابت للأدوات والموارد والPrompts والقدرات.
4. اختبارات protocol/conformance حتمية: handshake، capabilities، pagination، duplicate identifiers، malformed schema، timeouts، structured output، error mapping، output-size limits، وread-only safety rules.
5. policy file بصيغة YAML مع حدود timeout وmax output وenvironment وallow-exec.
6. تشغيل fixtures محلية وخادم demo آمن، مع explicit opt-in قبل تنفيذ أمر stdio خارجي.
7. baseline diff مع سياسة `fail-on` قابلة للضبط.
8. تقارير JSON وSARIF وملخص طرفية واضح، وحزمة evidence تحتوي manifest canonical ونتائج الاختبارات وhashes.
9. اختبارات unit وintegration وCLI وsecurity/failure paths وCI كاملة.

### Advanced Features

Signed evidence عبر Sigstore/Cosign كإضافة اختيارية، property-based schema generation، adapters لـ GitHub Actions وMCP Inspector، فحص behavioral للـ tool descriptions، وواجهة web read-only اختيارية. هذه الميزات لا تدخل MVP إلا إذا لم تهدد استقرار النواة.

### Future Roadmap

يمكن إضافة adapters للنقل الحديث أو بروتوكولات MCP اللاحقة، remote evidence stores، OpenTelemetry، مقارنة baseline عبر فروع Git، plugin marketplace للقواعد، وواجهة مراجعة تقارن عقدتين بصريًا.

## Architecture Decisions

| القرار | الاختيار | السبب |
|---|---|---|
| اللغة | Python 3.11+ | أقوى محور في حساب المستخدم، ودعم MCP Python SDK، وسرعة بناء CLI قابلة للاختبار |
| CLI | Typer + Rich | واجهة typed ورسائل طرفية مفيدة دون بناء UI كامل |
| نماذج البيانات | Pydantic v2 | تحقق حدودي، JSON schema، ونماذج واضحة قابلة للتوثيق |
| بروتوكول MCP | `mcp` Python SDK، بإصدار مقيد ضمن major واحد | الاستفادة من `ClientSession` و`stdio_client` و`streamable_http_client` دون إعادة تنفيذ JSON-RPC |
| التزامن | AnyIO/asyncio عبر حدود محددة | تشغيل النقل والاختبارات مع timeouts وإلغاء واضح |
| إعدادات المستخدم | YAML validated إلى typed config | ملف قابل للقراءة في repository، مع defaults آمنة ورفض الحقول غير المعروفة |
| تخزين الأدلة | filesystem bundle محلي | portable، diffable، ولا يحتاج قاعدة بيانات أو خدمة مستضافة في MVP |
| canonicalization | JSON sorted keys + UTF-8 + SHA-256 | digest حتمي ومفهوم، مع التصريح بأنه integrity وليس توقيع هوية |
| التقارير | JSON كعقد أساسي وSARIF كتكامل CI | JSON للاستهلاك البرمجي وSARIF للـ code scanning/annotations |
| التنفيذ الخارجي | disabled by default، مع allowlist وحدود | لا تشغيل مفاجئ لخوادم غير موثوقة ولا تسريب environment |
| الإضافات | rule registry داخلية بواجهات مستقرة | إضافة قواعد مستقبلًا دون خلط domain مع transport أو CLI |

## Component Architecture

```text
CLI
 └── Application Services
      ├── Target Resolver
      │    ├── Stdio Adapter (explicit opt-in)
      │    └── Streamable HTTP Adapter
      ├── MCP Session Boundary
      ├── Discovery Service
      ├── Contract Snapshot Service
      ├── Conformance Runner
      │    ├── Built-in Rules
      │    └── Schema Case Generator
      ├── Baseline Comparator
      ├── Evidence Writer
      └── Report Renderers (terminal, JSON, SARIF)

Domain Layer: immutable models, policies, findings, result semantics
Infrastructure Layer: MCP SDK, process management, filesystem, hashing, clock
```

## Module Boundaries

```text
src/mcp_conformance_lab/
├── cli.py                         # Typer commands and exit-code mapping
├── version.py
├── domain/
│   ├── models.py                  # Target, Contract, TestCase, Finding, Evidence
│   ├── errors.py                  # Typed domain/application errors
│   ├── policies.py                # Safe defaults and policy decisions
│   └── canonical.py               # Stable serialization and digest rules
├── application/
│   ├── discover.py                # MCP discovery use case
│   ├── snapshot.py                # Contract snapshot use case
│   ├── execute.py                 # Test plan execution and limits
│   ├── compare.py                 # Baseline comparison
│   └── report.py                  # Report orchestration
├── transports/
│   ├── protocol.py                # Transport adapter protocol
│   ├── stdio.py                   # Spawned process adapter
│   └── http.py                    # Streamable HTTP adapter
├── rules/
│   ├── protocol.py                # Rule interface and context
│   ├── builtin.py                 # Deterministic conformance rules
│   └── schema_cases.py             # Bounded schema-aware cases
├── evidence/
│   ├── bundle.py                  # Atomic evidence directory writer
│   ├── json_report.py
│   └── sarif.py
└── config/
    ├── loader.py                  # YAML loading and validation
    └── schema.py                  # Config model and versioning
```

## Public Contracts

### Target configuration

```yaml
schema_version: 1
name: demo-server
transport:
  kind: stdio
  command: python
  args: [examples/fixture_server.py]
  allow_exec: true
  cwd: .
  env: {}
policy:
  connect_timeout_seconds: 10
  case_timeout_seconds: 5
  max_output_bytes: 1048576
  max_items: 1000
  inherit_environment: false
  fail_on: high
baseline: .mcp-lab/baseline.json
reports:
  directory: .mcp-lab/runs
  formats: [terminal, json, sarif]
```

The config loader rejects unknown top-level fields, validates enum values and positive limits, resolves relative paths against the config file directory, and never treats a string field as a shell command. `args` remains an argv list; shell syntax is not interpreted.

### Finding contract

Each finding has `finding_id`, `rule_id`, `severity`, `status`, `title`, `message`, `target`, `evidence_refs`, and optional `remediation`. Severity is `info`, `low`, `medium`, `high`, or `critical`. Status is `passed`, `failed`, `skipped`, or `error`. Exit code is derived from the highest actionable finding, not from free-form text.

### Evidence contract

Each run contains `run.json`, `contract.json`, `results.json`, `manifest.sha256`, and bounded request/response excerpts. Sensitive environment names are redacted, large outputs are truncated with explicit metadata, and evidence is written atomically to a temporary directory before rename.

## Data Flow

1. CLI loads and validates the policy at the boundary.
2. Target resolver validates transport-specific requirements.
3. Adapter establishes an MCP session with a bounded timeout.
4. Discovery collects protocol version, server info, capabilities, tools, resources, and Prompts.
5. Snapshot service canonicalizes the public contract and computes a digest.
6. Runner executes only the selected safe rules and records bounded evidence.
7. Comparator checks baseline existence, digest changes, additions, removals, and breaking changes.
8. Report service writes JSON/SARIF/terminal output and maps findings to an exit code.

## Error Flow

Transport failures, protocol errors, validation errors, rule failures, and evidence-write failures are distinct typed errors. A malformed target configuration fails before process startup. A subprocess timeout terminates the process group where supported and reports `TRANSPORT_TIMEOUT`. A protocol error records the JSON-RPC code without exposing secrets. A rule error is not silently converted to pass. Evidence failures cause a non-zero exit because an unverifiable result must not be presented as successful.

## Security Model

The default posture is deny-by-default. Stdio execution requires `allow_exec: true` and an explicit command plus argv. The process receives a minimal environment unless `inherit_environment` is explicitly enabled; secret-looking names are always redacted from evidence. `shell=False` is mandatory. Working directories must resolve under an allowed root and symlinks are rejected for evidence paths. HTTP targets require explicit URL and optional headers loaded from environment variable names, never literal secret values in YAML. Responses are size-bounded and parsed as untrusted data. The MVP will not claim to sandbox arbitrary code; it only provides bounded process handling and recommends a disposable container or VM for hostile servers.

## Performance Strategy

The main cost is network/process I/O, not hashing. Discovery is sequential per session to preserve protocol order; independent static checks can run concurrently after discovery. Hashing streams bounded chunks. A benchmark fixture will measure discovery, snapshot, and 100-tool contract comparison. No performance claim will be made without recorded benchmark output.

## Test Strategy

Unit tests cover canonicalization, config validation, severity/exit mapping, redaction, path safety, schema case generation, and baseline diffs. Integration tests use an in-process fixture MCP server and a subprocess fixture over stdio. HTTP integration uses a local test server. CLI tests validate human-readable output, JSON/SARIF schema, exit codes, and failure scenarios. Security tests cover shell metacharacters, environment leakage, path traversal, symlink rejection, oversized output, timeout cleanup, malformed JSON, duplicate names, and non-zero child exit.

## Implementation Order and Checkpoints

The implementation proceeds bottom-up but vertically: each slice ends in a runnable command and focused tests. High-risk transport and process-boundary behavior is implemented early. No web UI or remote service is added before the CLI evidence path is stable.

## Definition of Done

The MVP is done only when a clean environment can install the package, run the fixture demo, generate and verify a baseline, fail on an intentional breaking change, emit valid JSON and SARIF, pass unit/integration/CLI/security tests, pass lint and type checks, complete dependency auditing, and run successfully in GitHub Actions. All claims in the README must point to a command or workflow that was actually executed.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| MCP SDK API drift | High | Pin compatible major version, isolate SDK imports in transports, add contract tests |
| Executing an untrusted stdio server | Critical | Disabled by default, explicit opt-in, minimal env, timeout, fixture mode, security warning |
| Tool side effects during tests | High | Read-only discovery first, no arbitrary tool calls by default, per-rule `destructive` flag false unless explicit |
| False positives from schema generation | Medium | Deterministic bounded cases, evidence for every finding, allow rule suppression with justification |
| Large or malicious outputs | High | Byte limits, streaming reads, truncation metadata, process termination on overflow |
| Baseline incompatibility | Medium | Versioned schema, additive fields, explicit migration error, no silent acceptance |
| Over-expansion into gateway/platform | High | Keep MVP CLI/library only and reject auth, dashboard, registry, and LLM analysis from core scope |
