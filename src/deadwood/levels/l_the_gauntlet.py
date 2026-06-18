"""Level — The Gauntlet. UNION SQL injection behind a keyword WAF: it strips single
quotes and blocks the literal `UNION SELECT` — but only case-sensitively and only
across real whitespace, so case-folding (`UnIoN SeLeCt`) or an inline comment
(`UNION/**/SELECT`) walks straight through, and quote-free literals carry the data."""

from __future__ import annotations

import html
import re

from deadwood import ui
from deadwood.level import Level, Request, Response, register

# The WAF: a case-SENSITIVE match on `UNION SELECT` across real whitespace. Naive on
# purpose — it never normalises case or strips comments first, so both classic
# evasions defeat it (while a verbatim `UNION SELECT` from a tool is blocked).
_WAF = re.compile(r"UNION\s+SELECT")


@register
class TheGauntlet(Level):
    num = 10
    slug = "the-gauntlet"
    title = "The Gauntlet"
    tier = "Hard"
    category = "SQL injection — UNION behind a keyword WAF"
    brief = "The gate strips your quotes and bars 'UNION SELECT'. Spell it differently."
    objective = ("The staff directory at `/l/the-gauntlet/app?id=1`, now behind a WAF that strips "
                 "single quotes and blocks the literal `UNION SELECT`. Evade the keyword filter and "
                 "read the flag from `secrets` (label `the-gauntlet`).")
    hints = [
        "id=1 works; id=1 UNION SELECT 1,2,3 is blocked by the gate. The block is on the exact "
        "words `UNION SELECT` — and quotes get stripped from your input too.",
        "SQL keywords are case-insensitive, but the filter isn't: UnIoN SeLeCt sails past it. So does "
        "an inline comment in the gap: UNION/**/SELECT (the engine reads the comment as a space).",
        "Quotes are stripped, so don't use string literals — char(...) builds them quote-free, and you "
        "can dump the whole table without a WHERE: id=0 UnIoN SeLeCt 1,label,value FROM secrets-- -",
        "hickok encodes literals quote-free already; the keyword evasion is the gap this room probes: "
        "`hickok sql -u 'http://127.0.0.1:8666/l/the-gauntlet/app?id=1' -p id --dump secrets`",
    ]
    remediation = ("Parameterize. A denylist on keywords is a perpetual game of spelling — case, "
                   "comments, encoding all evade it; binding the parameter ends it.")
    source = (
        "raw = req.query.get('id', '1')\n"
        "if re.search(r'UNION\\s+SELECT', raw):     # case-sensitive, whitespace-only — naive\n"
        "    return BLOCKED_PAGE\n"
        "idv = raw.replace(\"'\", '')               # quotes stripped\n"
        'sql = f"SELECT id, name, role FROM employees WHERE id={idv}"'
    )

    def seed(self, db):
        db.execute("INSERT INTO secrets (label, value) VALUES (?,?)", ("the-gauntlet", self.flag()))
        db.commit()

    def handle(self, req: Request, db) -> Response:
        raw = req.query.get("id", "1")
        if _WAF.search(raw):
            return Response(ui.shell("The Gauntlet", '<h1>Staff Directory</h1>'
                                     '<p class="err">⛔ the gate blocked that — no UNION SELECT.</p>'
                                     '<p class="dim"><a href="/l/the-gauntlet">&larr; briefing</a></p>'))
        idv = raw.replace("'", "")                  # the quote filter
        sql = f"SELECT id, name, role FROM employees WHERE id={idv}"
        try:
            rows = db.execute(sql).fetchall()
            note = ""
        except Exception as exc:
            rows, note = [], f'<p class="err">query error: {html.escape(str(exc))}</p>'
        body_rows = "".join(
            f"<tr><td>{html.escape(str(r[0]))}</td><td><b>{html.escape(str(r[1]))}</b></td>"
            f"<td>{html.escape(str(r[2]))}</td></tr>" for r in rows
        ) or '<tr><td colspan="3" class="dim">no matching employee</td></tr>'
        body = f"""
        <h1>Deadwood Trust — Staff Directory <span class="dim">(gated)</span></h1>
        <form method="get" action="/l/the-gauntlet/app">
          <input name="id" value="{html.escape(raw)}" size="52"> <button>look up</button>
        </form>
        {note}
        <table><tr><th>#</th><th>name</th><th>role</th></tr>{body_rows}</table>
        <p class="dim" style="margin-top:18px"><a href="/l/the-gauntlet">&larr; back to the briefing</a></p>
        """
        return Response(ui.shell("The Gauntlet — Staff Directory", body))
