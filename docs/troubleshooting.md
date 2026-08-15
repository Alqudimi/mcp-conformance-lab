# Troubleshooting

## `stdio execution is disabled`

هذا الرفض مقصود. يجب ضبط `transport.allow_exec: true` و`policy.allow_exec: true` معًا. إذا كان target غير موثوق، لا تفعّل الخيار على جهازك الرئيسي؛ استخدم container أو VM disposable.

## `configuration validation failed`

تحقق من `schema_version`، و`transport.kind`، وأن `args` قائمة لا نص shell، وأن قيم timeouts وlimits موجبة. المسارات النسبية تُفسر من مجلد ملف YAML، لذلك قد تحتاج إلى `cwd: ..` في ملفات الإعداد الموجودة داخل `examples/`.

## `MCP-BASELINE-*`

هذه النتائج تعني أن العقد الحالية تختلف عن baseline. راجع `results.json` لمعرفة ما إذا كان العنصر أضيف أو حذف أو تغير. لا تستبدل baseline تلقائيًا؛ راجع التغيير أولًا ثم شغّل `baseline` عمدًا إذا كان التغيير متوقعًا.

## `Evidence verification failed`

الـ bundle تغير بعد كتابته أو أن manifest غير صالح. أعد تشغيل الفحص لإنشاء bundle جديدة، ولا تستخدم نتيجة فشل التحقق كدليل نجاح.

## Streamable HTTP لا يتصل

تحقق من endpoint `/mcp`، وأن الخادم يعمل، وأن environment variables المطلوبة في `headers_env` موجودة. لا يحاول adapter اتباع redirects، ولا يطبع قيمة header المفقودة أو السرية.

## تحذيرات صادرة من fixture

قد تطبع بعض إصدارات MCP SDK تحذيرات داخلية إلى stderr أثناء بدء FastMCP. لا تؤثر هذه التحذيرات في JSON الذي يخرج عبر stdout، لكن يجب فصل stdout وstderr في CI إذا كان التقرير سيُستهلك آليًا.
