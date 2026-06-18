"""The core pages (chrome around the levels): the town map, each level's briefing
with progressive hints and a view-source/fix reveal, and flag submission."""

from __future__ import annotations

import html
import re
from urllib.parse import parse_qs

from deadwood import flags, progress, ui
from deadwood.level import Level, Request, Response, all_levels


def _md(text: str) -> str:
    """Trusted level copy → safe HTML: escape, then `code` and **bold** spans."""
    t = html.escape(text)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    return t


def _tier(lv) -> str:
    return f'<span class="tier t-{lv.tier.lower()}">{html.escape(lv.tier)}</span>'


def town_map() -> Response:
    sv = progress.solved()
    levels = all_levels()
    taken = len(sv & {lv.slug for lv in levels})
    pct = round(100 * taken / len(levels)) if levels else 0
    rows = []
    for lv in levels:
        done = lv.slug in sv
        mark = '<span class="taken">✓ taken</span>' if done else '<span class="dim">open</span>'
        rows.append(
            f'<div class="lvl"><div>'
            f'<span class="num">{lv.num:02d}</span><a href="/l/{lv.slug}">{html.escape(lv.title)}</a> '
            f'{_tier(lv)}<br>'
            f'<span class="dim">{html.escape(lv.brief)} — {html.escape(lv.category)}</span>'
            f'</div><div>{mark}</div></div>')
    body = f"""
    <h1>Deadwood</h1>
    <div class="panel warn">⚠ Intentionally vulnerable, on purpose and by design. Bound to
    127.0.0.1. <b>Never expose this to a network.</b></div>
    <p class="dim">A leveled web-security range — tutorial to impossible. Scout each room with
    <span class="gold">wraith</span>, take it with <span class="gold">hickok</span>. Capture the
    flag, then read the vulnerable source and the fix.</p>
    <div class="panel">
      <div style="display:flex;justify-content:space-between"><b>Progress</b>
        <span class="dim">{taken}/{len(levels)} rooms</span></div>
      <div class="bar"><span style="width:{pct}%"></span></div>
    </div>
    <div class="panel">{''.join(rows)}</div>
    """
    return Response(ui.shell("Town Map", body))


def briefing(lv: Level, req: Request) -> Response:
    solved = lv.slug in progress.solved()
    try:
        n_hints = max(0, int(req.query.get("hint", "0") or 0))
    except ValueError:
        n_hints = 0
    show_src = req.query.get("source") == "1"
    keep = "&source=1" if show_src else ""

    parts = [
        f'<h1>{lv.num:02d} · {html.escape(lv.title)} {_tier(lv)}</h1>',
        f'<p class="dim">{html.escape(lv.category)}</p>',
        f'<div class="panel"><b>Objective.</b> {_md(lv.objective)}</div>',
        f'<p><a href="/l/{lv.slug}/app"><button>open the app →</button></a> '
        f'<span class="dim">the target you point wraith / hickok at</span></p>',
    ]

    for i in range(min(n_hints, len(lv.hints))):
        parts.append(f'<div class="panel">💡 <b>hint {i + 1}.</b> {_md(lv.hints[i])}</div>')
    if n_hints < len(lv.hints):
        label = "reveal a hint" if n_hints == 0 else "reveal the next hint"
        parts.append(f'<p><a href="/l/{lv.slug}?hint={n_hints + 1}{keep}">'
                     f'{label} ({n_hints}/{len(lv.hints)})</a></p>')
    else:
        parts.append('<p class="dim">all hints revealed.</p>')

    if solved:
        parts.append(f'<div class="panel ok"><b>✓ taken.</b> flag: '
                     f'<span class="gold">{html.escape(lv.flag())}</span></div>')
    else:
        parts.append(f'''<form method="post" action="/l/{lv.slug}/flag" class="panel">
        <b>Submit the flag.</b><br><br>
        <input name="flag" placeholder="DEADWOOD{{...}}" size="46"> <button>check</button></form>''')

    hint_keep = f"&hint={n_hints}" if n_hints else ""
    if show_src:
        parts.append(f'<div class="panel"><b>The vulnerable source.</b><pre>'
                     f'{html.escape(lv.source)}</pre><b>How to fix it.</b><br>{_md(lv.remediation)}</div>')
    else:
        parts.append(f'<p><a href="/l/{lv.slug}?source=1{hint_keep}">view the vulnerable source '
                     f'&amp; the fix</a> <span class="dim">(spoiler)</span></p>')

    parts.append('<p class="dim" style="margin-top:18px"><a href="/">&larr; town map</a></p>')
    return Response(ui.shell(lv.title, "".join(parts)))


# --- the wider surface: things a recon pass (wraith) should light up beyond the
# levels — exposed files, a virtual host, and a soft-404 to calibrate noise against.

# Sensitive paths that shouldn't be reachable but are (content discovery).
_SENSITIVE = {
    "/.git/config": ("text/plain; charset=utf-8",
                     "[core]\n\trepositoryformatversion = 0\n\tbare = false\n"
                     '[remote "origin"]\n\turl = git@github.com:deadwood-trust/ledger.git\n'),
    "/backup.sql": ("text/plain; charset=utf-8",
                    "-- Deadwood Trust — nightly dump (DO NOT SHIP)\n"
                    "INSERT INTO employees(username,pw_md5) VALUES('admin','5f4dcc3b5aa765d61d8327deb882cf99');\n"
                    "-- … 8MB truncated …\n"),
    "/.env": ("text/plain; charset=utf-8",
              "DB_PASSWORD=goldrush\nSESSION_SECRET=dead-mans-hand\n"
              "SMTP_RELAY=telegraph:hunter2@relay.deadwood-trust.example\n"),
}

# Bare hostnames that serve an internal site instead of the public floor (vhost).
_INTERNAL_VHOSTS = {"internal", "staging", "vault", "ops", "dev", "admin", "backup"}
DEFAULT_HOSTS = {"127.0.0.1", "localhost", "::1", ""}


def sensitive_path(route: str) -> Response | None:
    hit = _SENSITIVE.get(route)
    if hit is None:
        return None
    return Response(hit[1], content_type=hit[0])


def is_internal_vhost(host: str) -> bool:
    return host.split(".")[0] in _INTERNAL_VHOSTS


def vhost_page() -> Response:
    return Response(ui.shell("Internal", '<h1>Deadwood Trust — Internal Ops</h1>'
                             '<p class="dim">staging mirror · not for the public floor</p>'
                             '<div class="panel">DB console, payroll exports and the vault log live '
                             'behind this name. If you can read this, the vhost is exposed.</div>',
                             subtitle="internal — not for the public floor"))


def soft_404() -> Response:
    # 200, not 404 — a soft-404, so a content scanner has to calibrate the "missing"
    # page by its body and tell real hits apart from the noise.
    return Response(ui.shell("not found", '<h1>No such page</h1>'
                             '<p class="dim">The trail ends here. Back to the '
                             '<a href="/">town map</a>.</p>'))


def submit_flag(lv: Level, req: Request) -> Response:
    data = parse_qs(req.body.decode("utf-8", "replace"))
    value = (data.get("flag") or [""])[0]
    if flags.check(lv.slug, value):
        progress.mark(lv.slug)
        body = (f'<div class="panel ok"><h2>✓ {html.escape(lv.title)} — taken.</h2>'
                f'<p>that\'s the hand. <span class="gold">{html.escape(lv.flag())}</span></p></div>'
                f'<p><a href="/">&larr; town map</a></p>')
    else:
        body = (f'<div class="panel err"><h2>✗ not it.</h2>'
                f'<p class="dim">keep working the room.</p></div>'
                f'<p><a href="/l/{lv.slug}">&larr; back to the briefing</a></p>')
    return Response(ui.shell("flag", body))
