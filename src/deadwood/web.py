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


def town_map() -> Response:
    sv = progress.solved()
    rows = []
    for lv in all_levels():
        mark = '<span class="ok">✓ taken</span>' if lv.slug in sv else '<span class="dim">open</span>'
        rows.append(
            f'<div class="lvl"><div>'
            f'<a href="/l/{lv.slug}">{lv.num:02d} · {html.escape(lv.title)}</a> '
            f'<span class="tier">{html.escape(lv.tier)}</span><br>'
            f'<span class="dim">{html.escape(lv.brief)} — {html.escape(lv.category)}</span>'
            f'</div><div>{mark}</div></div>')
    taken = len(sv & {lv.slug for lv in all_levels()})
    body = f"""
    <h1>Deadwood</h1>
    <div class="panel warn">⚠ Intentionally vulnerable, on purpose and by design. Bound to
    127.0.0.1. <b>Never expose this to a network.</b></div>
    <p class="dim">A leveled web-security range — tutorial to impossible. Scout each room with
    <span class="gold">wraith</span>, take it with <span class="gold">hickok</span>. Capture the
    flag, then read the vulnerable source and the fix.</p>
    <p class="dim">{taken}/{len(all_levels())} rooms taken.</p>
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
    keep = f"&source=1" if show_src else ""

    parts = [
        f'<h1>{lv.num:02d} · {html.escape(lv.title)} '
        f'<span class="tier">{html.escape(lv.tier)}</span></h1>',
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
