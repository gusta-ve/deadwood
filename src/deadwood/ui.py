"""The look — one dark, gold-lit HTML shell shared by the info pages and the
vulnerable apps, so the whole range feels like one frontier town. No assets, no
dependencies; the CSS is inline."""

from __future__ import annotations

_CSS = """
:root{--bg:#0d0b08;--panel:#17130d;--ink:#e8dcc5;--dim:#9a8d77;--gold:#ffb946;--line:#2a2118;--bad:#e2543c;--ok:#7bbf6a}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 ui-monospace,SFMono-Regular,Menlo,monospace}
a{color:var(--gold);text-decoration:none}a:hover{text-decoration:underline}
header{border-bottom:1px solid var(--line);padding:14px 22px;display:flex;gap:14px;align-items:baseline}
header .brand{color:var(--gold);font-weight:700;letter-spacing:.5px}
header .tag{color:var(--dim);font-size:13px}
main{max-width:980px;margin:0 auto;padding:26px 22px}
h1,h2{font-weight:700;letter-spacing:.4px}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:18px 20px;margin:16px 0}
.dim{color:var(--dim)}.gold{color:var(--gold)}.err{color:var(--bad)}.ok{color:var(--ok)}
table{border-collapse:collapse;width:100%}
td,th{border:1px solid var(--line);padding:7px 10px;text-align:left}
th{color:var(--dim);font-weight:600}
input,button{font:inherit;background:#0a0805;color:var(--ink);border:1px solid var(--line);border-radius:7px;padding:8px 11px}
button{color:var(--gold);cursor:pointer}button:hover{border-color:var(--gold)}
pre{background:#0a0805;border:1px solid var(--line);border-radius:8px;padding:12px 14px;overflow:auto;color:#cdbf9f}
.tier{font-size:12px;border:1px solid var(--line);border-radius:999px;padding:2px 9px;color:var(--dim)}
.warn{border-color:#5a2418;background:#1d0f0a;color:#f0b6a6}
.lvl{display:flex;justify-content:space-between;gap:12px;align-items:center;border-bottom:1px solid var(--line);padding:12px 8px;border-radius:8px}
.lvl:last-child{border-bottom:0}
.lvl:hover{background:#1b160e}
.num{color:var(--dim);font-variant-numeric:tabular-nums;margin-right:6px}
.tier.t-tutorial{color:#7bbf6a;border-color:#2f4a28}
.tier.t-easy{color:#5bb3a6;border-color:#234a44}
.tier.t-medium{color:#ffb946;border-color:#4a3a18}
.tier.t-hard{color:#e58a3c;border-color:#4a3018}
.tier.t-brutal{color:#e2543c;border-color:#4a1f18}
.tier.t-impossible{color:#c77dff;border-color:#3a2a4a}
.bar{height:9px;background:#120d08;border:1px solid var(--line);border-radius:999px;overflow:hidden;margin:8px 0 4px}
.bar>span{display:block;height:100%;background:linear-gradient(90deg,#96541e,#ffb946)}
.taken{color:var(--ok)}
footer{color:var(--dim);font-size:12px;text-align:center;padding:26px}
"""


def shell(title: str, body: str, subtitle: str = "an intentionally vulnerable range — localhost only") -> str:
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · deadwood</title><style>{_CSS}</style></head><body>
<header><span class="brand">deadwood</span><span class="tag">{subtitle}</span>
<span style="margin-left:auto"><a href="/">town map</a></span></header>
<main>{body}</main>
<footer>deadwood · the practice town for wraith &amp; hickok · authorized local use only</footer>
</body></html>"""
