# Contributing to MCP Conformance Lab

شكرًا لاهتمامك بالمساهمة. الهدف من المشروع هو الحفاظ على أداة صغيرة وحتمية وآمنة لاختبار خوادم MCP، لذلك نفضل التغييرات المركزة التي تضيف دليلًا قابلًا لإعادة الإنتاج بدل الميزات الواسعة غير المختبرة.

## قبل فتح Pull Request

اقرأ `tasks/plan.md` وراجع حدود الأمان في `README.md`. شغّل بوابات الجودة محليًا:

```bash
python -m pytest -q
ruff check src tests
ruff format --check src tests
mypy src
```

إذا غيّرت package metadata أو dependencies، شغّل أيضًا `python -m build` و`pip-audit`. لا تضع secrets أو evidence runs محلية في git.

## قواعد جديدة

كل rule جديدة يجب أن تملك `rule_id` ثابتًا، وحالات pass وfail وerror في الاختبارات، ورسالة remediation قابلة للتنفيذ. إذا غيرت rule عقدة evidence أو exit code، حدّث الوثائق وأضف ملاحظة في `CHANGELOG.md`.

## Transport adapters

لا تعيد تنفيذ JSON-RPC إذا كان MCP SDK يوفر boundary مناسبة. يجب أن تبقى الأسرار خارج YAML والأدلة، وأن تكون subprocess argv صريحة بلا shell، وأن تكون timeouts وحدود الحجم قابلة للضبط ومختبرة.

## Pull Requests

اكتب وصفًا يشرح المشكلة، القرار المعماري، الاختبارات المنفذة، وأي trade-off مقصود. يجب أن يمر CI قبل الدمج. تجنب خلط refactor واسع مع تغيير سلوكي في rule واحدة.
