# -*- coding: utf-8 -*-
"""i18n coverage: every t("KEY")/be.tr("KEY") key used in the code exists in each
locales/<lang>.json locale (UI — flat keys, backend — the "server" section).
Run: python _t/i18n_check.py — exit 1 on a miss."""
import glob, io, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "frontend", "src")

locales = {}
for f in glob.glob(os.path.join(ROOT, "locales", "*.json")):
    locales[os.path.basename(f)[:-5]] = json.load(
        io.open(f, encoding="utf-8"))

fe_used = set()
for root, _d, files in os.walk(SRC):
    for f in files:
        if f.endswith((".ts", ".tsx")):
            s = io.open(os.path.join(root, f), encoding="utf-8").read()
            fe_used.update(re.findall(r'\bt\("([A-Z_]+)"', s))

be_used = set()
for f in ("core.py", "dashboard.py", "backend.py", "mcp_server.py",
          "storage.py", "process_tree.py", "platform_impl.py"):
    s = io.open(os.path.join(ROOT, f), encoding="utf-8").read()
    # \btr( catches be.tr("K") and bare tr("K") inside backend.py;
    # all SCREAMING literals in args — tr("A" if x else "B") too.
    # Dynamic tr(var) (PILL_*, CATS) are not statically checked.
    for args in re.findall(r'\btr\(([^)]*)\)', s):
        be_used.update(re.findall(r'"([A-Z_]+)"', args))

bad = False
for lang, loc in sorted(locales.items()):
    flat = {k for k, v in loc.items() if isinstance(v, str)}
    srv = set(loc.get("server", {}))
    miss, miss_srv = fe_used - flat, be_used - srv
    if miss or miss_srv:
        bad = True
        print(f"{lang}: MISSING ui={sorted(miss)} server={sorted(miss_srv)}")
    else:
        print(f"{lang}: {len(fe_used)} ui + {len(be_used)} server keys used, "
              f"all covered (dict {len(flat)}+{len(srv)})")
sys.exit(1 if bad else 0)
