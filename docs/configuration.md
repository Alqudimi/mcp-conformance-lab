# Configuration

يستخدم MCP Conformance Lab ملف YAML versioned. يبدأ الملف بـ `schema_version: 1` واسم target، ثم يحدد transport وpolicy وbaseline وreports. يتم رفض الحقول غير المعروفة حتى لا يتحول خطأ إملائي في إعداد أمني إلى default صامت.

## Stdio

```yaml
schema_version: 1
name: local-fixture
transport:
  kind: stdio
  command: python3
  args: [examples/fixture_server.py]
  allow_exec: true
  cwd: ..
policy:
  allow_exec: true
  inherit_environment: false
  connect_timeout_seconds: 10
  case_timeout_seconds: 5
  max_output_bytes: 1048576
  max_items: 1000
  fail_on: high
```

The two `allow_exec` flags are intentional. The transport declares that this target is approved to spawn, while the policy declares that the run is allowed to execute processes at all. Both are required. `args` is an array and is never interpreted by a shell. `cwd` is resolved against the config file directory and can be constrained by `allowed_working_root`.

## Streamable HTTP

```yaml
schema_version: 1
name: remote-server
transport:
  kind: streamable_http
  url: https://localhost:8000/mcp
  headers_env:
    Authorization: MCP_AUTH_HEADER
policy:
  connect_timeout_seconds: 10
  case_timeout_seconds: 5
  max_output_bytes: 1048576
  max_items: 1000
  fail_on: high
```

`headers_env` maps a header name to an environment variable name. The value is resolved at runtime and is not copied into the YAML or evidence files. Redirects are disabled by the adapter, and callers should use an endpoint they trust. The MVP does not discover or store credentials.

## Policy fields

| Field | Default | Meaning |
|---|---:|---|
| `connect_timeout_seconds` | 10 | Maximum time for initialization |
| `case_timeout_seconds` | 5 | Maximum time for one bounded operation |
| `max_output_bytes` | 1 MiB | Output bound for future execution cases |
| `max_items` | 1000 | Maximum number of returned collection items |
| `allow_exec` | false | Global permission for stdio process execution |
| `inherit_environment` | false | Whether to inherit the host environment |
| `fail_on` | high | Minimum severity that makes the process fail |

The policy is not a sandbox. A user who explicitly runs an untrusted stdio server should place it in a disposable container or VM with restricted filesystem and network permissions.

## Baseline and reports

`baseline` points to a canonical `ContractSnapshot` JSON file. `reports.directory` is the parent directory for atomic evidence bundles. Relative paths resolve from the YAML file, not from the current shell directory. Report formats are currently `terminal`, `json`, and `sarif`.
