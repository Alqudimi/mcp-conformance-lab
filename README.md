# MCP Conformance Lab

[![CI](https://github.com/Alqudimi/mcp-conformance-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/Alqudimi/mcp-conformance-lab/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Deterministic conformance, security, and regression testing for Model Context Protocol servers.**

MCP Conformance Lab يحول اختبار خادم MCP من جلسة يدوية إلى بوابة قابلة لإعادة التشغيل قبل الدمج. يكتشف العقد العامة للخادم عبر `stdio` أو **Streamable HTTP**، يتحقق من قواعد حتمية، يحسب contract digest، يقارن baseline، ويصدر أدلة محلية وتقارير JSON وSARIF مناسبة لـ CI.

> المشروع local-first: لا يرسل أوصاف الأدوات أو النتائج إلى خدمة تحليل خارجية، ولا يعتمد على LLM في الحكم الأساسي.

## لماذا هذا المشروع؟

أدوات الفحص التفاعلي والماسحات الأمنية مفيدة لاكتشاف الخادم أو الإشارة إلى مخاطر، لكن فرق التطوير تحتاج أيضًا إلى إجابة قابلة للإثبات عن سؤال مختلف: **هل ما زال الخادم يطابق العقد التي وافقنا عليها بعد هذا التغيير؟** لا يكفي نجاح `tools/list` مرة واحدة؛ فالتغييرات في schema أو capabilities أو identifiers أو pagination قد تكسر عميلًا لاحقًا حتى لو ظل الخادم قابلًا للاتصال.

يعالج MCP Conformance Lab هذه الفجوة عبر snapshot canonical، وقواعد conformance قابلة للتكرار، وbaseline diff، وحزمة evidence تحتوي على ملفات محلية وhashes. الأداة لا تحاول أن تكون Gateway أو Firewall أو بديلًا عن MCP Inspector أو الماسحات المتخصصة؛ بل تركز على **contract testing قبل الدمج**.

## الميزات الحالية

| المجال | ما يقدمه MVP |
|---|---|
| النقل | `stdio` وStreamable HTTP عبر MCP Python SDK |
| الاكتشاف | handshake، protocol version، server info، capabilities، tools، resources، prompts، pagination |
| القواعد | uniqueness، JSON Schema validity، capability consistency |
| baseline | canonical snapshot، SHA-256 digest، كشف الإضافة والحذف والتغيير، والإبلاغ الصريح عن baseline المفقود أو غير الصالح |
| الأدلة | `contract.json`، `results.json`، `run.json`، `manifest.sha256` |
| التقارير | terminal، JSON، SARIF 2.1.0 |
| الأمان | stdio معطل افتراضيًا، argv بلا shell، بيئة محدودة، timeouts، حدود items وoutput، headers من environment |
| الجودة | unit tests، integration smoke tests، Ruff، mypy، pytest، GitHub Actions |

## التثبيت

يتطلب المشروع **Python 3.11 أو أحدث**. من checkout نظيف:

```bash
python -m pip install .
```

للتطوير المحلي:

```bash
python -m pip install -e '.[dev]'
```

## تشغيل سريع آمن

يحتوي `examples/fixture_server.py` على خادم محلي غير مدمر، ويحتوي `examples/fixture.yaml` على إعداد يوضح أن تشغيل stdio يحتاج إلى opt-in صريح في كل من النقل والسياسة:

```bash
mcp-conformance discover \
  --config examples/fixture.yaml \
  --format terminal
```

إنشاء baseline ثم فحص الانحدار:

```bash
mcp-conformance baseline --config examples/fixture.yaml
mcp-conformance check --config examples/fixture.yaml --format sarif
```

سيُحفظ baseline في `.mcp-lab/fixture-baseline.json`، وستُحفظ حزمة evidence تحت `.mcp-lab/runs/`. إذا كان baseline مضبوطًا في الإعداد لكنه مفقود أو غير صالح، يفشل الفحص بـ finding صريح (`MCP-BASELINE-MISSING` أو `MCP-BASELINE-INVALID`) بدل تجاهل المقارنة. للتحقق من سلامة أحدث حزمة:

```bash
mcp-conformance verify .mcp-lab/runs/<run-id>
```

للاطلاع على كل الأوامر:

```bash
mcp-conformance --help
```

## استخدام Streamable HTTP

يقبل الإعداد هدفًا من الشكل التالي:

```yaml
schema_version: 1
name: my-server
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
reports:
  directory: .mcp-lab/runs
  formats: [terminal, json, sarif]
```

القيم السرية لا توضع في YAML. يقرأ adapter قيمة `MCP_AUTH_HEADER` من environment، ويمنع تسجيلها في الأدلة. يوجد مثال محلي في `examples/http_fixture.yaml`.

## نموذج الإخراج

تتكون حزمة evidence من ملفات صغيرة ومحمولة يمكن فحصها في CI أو إرفاقها مع نتيجة build:

```text
run.json          # target, run id, timestamp, contract digest
contract.json     # canonical contract snapshot
results.json      # findings and statuses
manifest.sha256   # hashes of the three files above
```

حقل `contract_digest` يثبت سلامة المحتوى بالنسبة إلى canonical representation. **لا يدعي المشروع أن SHA-256 المحلي توقيع موقّع أو non-repudiation**؛ يمكن إضافة Sigstore/Cosign في طبقة اختيارية لاحقة.

## نموذج الأمان

الافتراضي هو الرفض الآمن. لا يُشغّل target عبر stdio إلا بعد ضبط `transport.allow_exec: true` و`policy.allow_exec: true`. تمرر الأوامر كـ argv list مع `shell=False`، وتُستخدم بيئة محدودة ما لم يطلب المستخدم صراحة توريث environment. تُفرض حدود زمنية على الاتصال والحالة، ويُرفض تجاوز working-root المسموح، وتُرسل headers الحساسة من متغيرات البيئة بدل ملفات الإعداد.

هذه الحدود **ليست sandbox** ولا تمنع خادمًا خبيثًا من إساءة استخدام صلاحيات نظام التشغيل إذا منحته explicit opt-in. عند اختبار كود غير موثوق، استخدم container أو VM disposable مع شبكة وصلاحيات محدودة. لا ينفذ MVP أدوات MCP ذات side effects تلقائيًا؛ قواعد execution المستقبلية يجب أن تحمل سياسة واضحة وتحتاج opt-in مستقلًا.

## المعمارية

```text
CLI
 └── Application Services
      ├── Target Resolver
      │    ├── Stdio Adapter
      │    └── Streamable HTTP Adapter
      ├── MCP Discovery
      ├── Contract Snapshot + SHA-256
      ├── Deterministic Rule Registry
      ├── Baseline Comparator
      ├── Evidence Bundle Writer
      └── JSON / SARIF / Terminal Renderers

Domain: models, policies, errors, canonicalization
Infrastructure: MCP SDK, process boundary, filesystem, hashing
```

للتفاصيل، راجع [خطة التنفيذ والمعمارية](tasks/plan.md) و[قائمة المهام](tasks/todo.md).

## الاختبارات وبوابات الجودة

```bash
python -m pytest -q
ruff check src tests
ruff format --check src tests
mypy src
python -m build
pip-audit
```

تغطي الاختبارات canonicalization، config validation، baseline diff، redaction boundary، stdio opt-in، HTTP headers، evidence tampering، SARIF shape، وCLI flows. لا تُقبل claims في الوثائق إلا إذا كان لها أمر أو اختبار قابل للتشغيل.

## حدود النطاق الحالية

لا يحتوي MVP على dashboard أو registry أو Gateway أو LLM-based judgment أو remote evidence store. كما لا يحاول إعادة تنفيذ OpenSSF Scorecard أو SLSA أو Cosign؛ بل يقدم contract-level evidence يمكن ربطه بهذه الأنظمة مستقبلًا. اختيار هذا النطاق مقصود حتى تبقى النواة صغيرة، حتمية، قابلة للصيانة، وقابلة للمراجعة.

## المساهمة

اقرأ [CONTRIBUTING.md](CONTRIBUTING.md) قبل فتح pull request. يجب أن يتضمن كل تغيير في rule اختبارًا لحالات pass وfail وerror، وأن يوضح أي تغيير في contract أو evidence schema. للمشكلات الأمنية، راجع [SECURITY.md](SECURITY.md) بدل نشر تفاصيل الاستغلال في issue عامة.

## الترخيص

هذا المشروع مرخص بموجب [MIT License](LICENSE).
