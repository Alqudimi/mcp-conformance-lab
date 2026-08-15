# MCP Conformance Lab — Task Checklist

## Phase 1: Foundation

### Task 1: Package scaffold and quality gates

**Description:** إنشاء Python package قابل للتثبيت مع pyproject، CLI entry point، typed configuration skeleton، lint/type/test tooling، وملفات المشروع الأساسية.

**Acceptance criteria:**
- [ ] `pip install -e '.[dev]'` ينجح في بيئة نظيفة.
- [ ] `mcp-conformance --help` يعرض أوامر واضحة.
- [ ] Ruff وmypy وpytest يعملون من أول commit.

**Verification:** `python -m pytest`, `ruff check .`, `mypy src`.

**Dependencies:** None.

**Files likely touched:** `pyproject.toml`, `src/mcp_conformance_lab/cli.py`, `src/mcp_conformance_lab/version.py`, `tests/test_cli.py`.

**Estimated scope:** Medium.

### Task 2: Domain models, errors, canonicalization, and policy

**Description:** تعريف النماذج العامة والعقود الثابتة للأهداف والنتائج والأدلة، مع serialization canonical وhashing وسياسات الأمان والـ exit codes.

**Acceptance criteria:**
- [ ] النماذج ترفض المدخلات غير الصحيحة وتقبل config version 1.
- [ ] نفس البيانات تنتج نفس canonical bytes وSHA-256 على كل تشغيل.
- [ ] حالات severity/status/error تحول إلى exit codes موحدة.

**Verification:** unit tests للـ models والcanonicalization والـ redaction والـ path safety.

**Dependencies:** Task 1.

**Files likely touched:** `domain/models.py`, `domain/errors.py`, `domain/canonical.py`, `domain/policies.py`, `config/schema.py`, `config/loader.py`.

**Estimated scope:** Medium.

### Checkpoint: Foundation

- [ ] التثبيت والـ CLI الأساسي يعملان.
- [ ] اختبارات domain والسياسات تمر.
- [ ] لا توجد أسرار أو placeholders غير مقصودة.

## Phase 2: Transport and discovery

### Task 3: Transport adapter protocol and Streamable HTTP adapter

**Description:** بناء boundary مستقرة فوق MCP Python SDK لإدارة جلسة Streamable HTTP bounded session، مع تحويل أخطاء النقل والبروتوكول إلى أخطاء typed.

**Acceptance criteria:**
- [ ] adapter ينفذ initialize/list tools/list resources/list prompts عند توفرها.
- [ ] timeouts وMCP errors وHTTP failures تظهر كحالات قابلة للتقرير.
- [ ] لا تخرج headers الحساسة إلى logs أو evidence.

**Verification:** HTTP fixture integration tests للنجاح، 4xx/5xx، session failure، oversized response، وtimeout.

**Dependencies:** Task 2.

**Files likely touched:** `transports/protocol.py`, `transports/http.py`, `application/discover.py`, `tests/integration/test_http_transport.py`.

**Estimated scope:** Medium.

### Task 4: Safe stdio adapter and fixture server

**Description:** دعم تشغيل خادم fixture عبر argv بدون shell، مع explicit opt-in، minimal environment، cwd validation، process-group timeout cleanup، وخادم demo غير مدمر.

**Acceptance criteria:**
- [ ] stdio لا يعمل إلا عند `allow_exec: true`.
- [ ] shell metacharacters لا تفسر كأوامر.
- [ ] timeout أو child failure ينهي العملية ويُسجل السبب.

**Verification:** subprocess integration tests للـ argv isolation، env isolation، timeout cleanup، non-zero exit، وmalformed output.

**Dependencies:** Task 2.

**Files likely touched:** `transports/stdio.py`, `examples/fixture_server.py`, `tests/integration/test_stdio_transport.py`.

**Estimated scope:** Large.

### Checkpoint: Transport

- [ ] HTTP وstdio fixture discovery يعملان.
- [ ] اختبارات الحدود الأمنية للنقل تمر.
- [ ] لا يوجد تشغيل تلقائي لخادم غير موثوق.

## Phase 3: Contracts and conformance

### Task 5: Contract snapshot and baseline comparison

**Description:** تحويل discovery إلى snapshot versioned، حساب digest، واكتشاف additions/removals/changes breaking وغير breaking.

**Acceptance criteria:**
- [ ] snapshot stable regardless of map ordering.
- [ ] baseline missing/new/changed/invalid حالات distinct.
- [ ] comparator يذكر path والقيمة القديمة والجديدة مع severity.

**Verification:** unit tests للترتيب، duplicate names، baseline migration، وbreaking diff.

**Dependencies:** Tasks 3 and 4.

**Files likely touched:** `application/snapshot.py`, `application/compare.py`, `domain/models.py`, `tests/unit/test_snapshot.py`, `tests/unit/test_compare.py`.

**Estimated scope:** Medium.

### Task 6: Deterministic conformance rule registry

**Description:** إنشاء واجهة rule مستقرة ومجموعة قواعد MVP لا تعتمد على LLM: protocol metadata، capabilities، pagination, duplicate identifiers, schema validity, structured output, error mapping, and size limits.

**Acceptance criteria:**
- [ ] كل rule تنتج Finding typed مع evidence reference.
- [ ] القواعد قابلة للتشغيل منفردة عبر policy.
- [ ] القاعدة الفاشلة لا تتحول إلى pass ولا تخفي operational errors.

**Verification:** rule unit tests plus fixture integration matrix covering pass/fail/skip/error.

**Dependencies:** Task 5.

**Files likely touched:** `rules/protocol.py`, `rules/builtin.py`, `rules/schema_cases.py`, `application/execute.py`, `tests/unit/test_rules.py`.

**Estimated scope:** Large.

### Checkpoint: Core behavior

- [ ] fixture server ينتج snapshot وfindings فعلية.
- [ ] breaking change متعمد يجعل CLI يفشل.
- [ ] كل finding يحتوي دليلًا قابلًا للإشارة.

## Phase 4: Evidence and reports

### Task 7: Atomic evidence bundle and JSON/SARIF reporters

**Description:** كتابة run manifest وcontract/results/references مع hashes وحدود حجم، ثم تقارير JSON وSARIF وملخص Rich.

**Acceptance criteria:**
- [ ] evidence directory يكتب ذريًا ولا يترك bundle نصف مكتمل.
- [ ] secret-looking environment fields redacted، وtruncation معلنة.
- [ ] JSON وSARIF يطابقان schema المتوقع ويحتويان rule IDs وlocations/evidence refs.

**Verification:** tests للـ atomic writes، tampering detection، redaction، SARIF parsing، وlarge output.

**Dependencies:** Tasks 5 and 6.

**Files likely touched:** `evidence/bundle.py`, `evidence/json_report.py`, `evidence/sarif.py`, `application/report.py`, `tests/unit/test_evidence.py`.

**Estimated scope:** Large.

### Task 8: End-to-end CLI commands and examples

**Description:** ربط أوامر `discover`, `snapshot`, `check`, `baseline`, `verify` مع config loading وreports وexit codes، وإنشاء demo scenario قابل للتشغيل من README.

**Acceptance criteria:**
- [ ] المستخدم يستطيع تشغيل fixture demo بأمرين أو أقل.
- [ ] `check --format json` و`--format sarif` يعملان.
- [ ] `baseline` ثم تغيير fixture ثم `check` يثبت regression.

**Verification:** CLI subprocess tests من clean temp directories، plus manual demo run.

**Dependencies:** Tasks 3–7.

**Files likely touched:** `cli.py`, `application/*.py`, `examples/`, `tests/e2e/test_cli_flow.py`.

**Estimated scope:** Large.

## Phase 5: Project quality and release readiness

### Task 9: Documentation and Open Source foundation

**Description:** كتابة README وdocs architecture/config/security/testing/troubleshooting وLICENSE وCONTRIBUTING وCODE_OF_CONDUCT وSECURITY وCHANGELOG وtemplates.

**Acceptance criteria:**
- [ ] quick start قابل للتنفيذ من clean checkout.
- [ ] security limitations واضحة ولا توجد claims غير مثبتة.
- [ ] contributor workflow وrelease process موثقان.

**Verification:** documentation smoke script يتحقق من الروابط والأوامر الأساسية.

**Dependencies:** Task 8.

**Files likely touched:** `README.md`, `docs/*.md`, `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `CHANGELOG.md`.

**Estimated scope:** Large.

### Task 10: CI/CD, security scan, benchmarks, and final review

**Description:** إضافة GitHub Actions للـ lint/type/tests/coverage/build/audit، benchmark صغير، review أمني وأداء، وإصلاح regression قبل النشر.

**Acceptance criteria:**
- [ ] CI يفشل عند lint/type/test/build/audit failure.
- [ ] coverage وbenchmark output قابلان لإعادة التشغيل.
- [ ] لا secrets في git، وdependency audit وCodeQL/Scorecard configuration موجودة حيث تناسب.

**Verification:** run all local gates، ثم push branch وقراءة نتيجة Actions فعليًا.

**Dependencies:** Tasks 8 and 9.

**Files likely touched:** `.github/workflows/ci.yml`, `.github/workflows/security.yml`, `scripts/benchmark.py`, `tests/`, `pyproject.toml`.

**Estimated scope:** Large.

### Task 11: Explicit baseline failure semantics

**Description:** Treat a configured-but-missing, unreadable, or invalid baseline as a machine-readable conformance finding instead of silently skipping comparison or terminating before evidence/report generation.

**Acceptance criteria:**
- [x] A configured missing baseline produces `MCP-BASELINE-MISSING` with high severity and error status.
- [x] A malformed baseline produces `MCP-BASELINE-INVALID` with high severity and error status.
- [x] A valid baseline continues through the existing deterministic comparator.

**Verification:** `python -m pytest -q`, `ruff check src tests`, `ruff format --check src tests`, `mypy src`, and `python -m build`.

**Dependencies:** Tasks 5, 7, and 8.

**Files touched:** `src/mcp_conformance_lab/application/service.py`, `src/mcp_conformance_lab/cli.py`, `tests/unit/test_baseline.py`.

**Estimated scope:** Small.

### Checkpoint: Release candidate

- [ ] clean install/build/test/lint/type/security/docs checks pass.
- [x] baseline configuration failures are explicit, typed, and tested.
- [ ] README demo and baseline regression flow pass.
- [ ] package metadata and license are correct.
- [ ] repository is ready for publication.
