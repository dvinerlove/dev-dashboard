# -*- coding: utf-8 -*-
"""i18n coverage: все ключи t("KEY")/be.tr("KEY") в коде есть в словарях
RU и EN. Запуск: python _t/i18n_check.py — exit 1 при промахе."""
import io, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "frontend", "src")

loc = io.open(os.path.join(SRC, "lib", "locales.ts"), encoding="utf-8").read()
fe_ru = set(re.findall(r'^\s+"(\w+)":', loc.split("export const EN")[0], re.M))
fe_en = set(re.findall(r'^\s+"(\w+)":', loc.split("export const EN")[1], re.M))

fe_used = set()
for root, _d, files in os.walk(SRC):
    for f in files:
        if f.endswith((".ts", ".tsx")) and f != "locales.ts":
            s = io.open(os.path.join(root, f), encoding="utf-8").read()
            fe_used.update(re.findall(r'\bt\("([A-Z_]+)"', s))

sys.path.insert(0, ROOT)
import backend as be  # noqa: E402
be_used = set()
for f in ("core.py", "dashboard.py", "backend.py", "mcp_server.py",
          "storage.py", "process_tree.py", "platform_impl.py"):
    s = io.open(os.path.join(ROOT, f), encoding="utf-8").read()
    # \btr( ловит be.tr("K") и голый tr("K") внутри backend.py;
    # все SCREAMING-литералы в аргументах — tr("A" if x else "B") тоже.
    # Динамические tr(var) (PILL_*, CATS) статически не проверяются.
    for args in re.findall(r'\btr\(([^)]*)\)', s):
        be_used.update(re.findall(r'"([A-Z_]+)"', args))

bad = False
for name, used, ru, en in (("frontend", fe_used, fe_ru, fe_en),
                           ("backend", be_used, set(be.RU), set(be.EN))):
    miss_ru, miss_en = used - ru, used - en
    if miss_ru or miss_en:
        bad = True
        print(f"{name}: MISSING RU={sorted(miss_ru)} EN={sorted(miss_en)}")
    else:
        print(f"{name}: {len(used)} keys used, all covered "
              f"(dict {len(ru)})")
sys.exit(1 if bad else 0)
