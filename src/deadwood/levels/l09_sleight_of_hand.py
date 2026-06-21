"""Level 9 — Sleight of Hand. UNION SQL injection behind an input filter that
strips quotes and blocks the schema catalog."""

from __future__ import annotations

import html

from deadwood import ui
from deadwood.level import Level, Request, Response, register

_BLOCKED = ("sqlite_master", "information_schema", "pragma")


@register
class SleightOfHand(Level):
    num = 9
    slug = "sleight-of-hand"
    title = "Sleight of Hand"
    tier = "Hard"
    category = "SQL injection — UNION behind an input filter"
    brief = "The directory's back — but it eats your quotes and bars the catalog."
    objective = ("The same staff directory at `/l/sleight-of-hand/app?id=1`, now behind a filter "
                 "that strips single/double quotes and blocks the schema catalog "
                 "(`sqlite_master`/`pragma`). Read the flag from `secrets` regardless.")
    hints = [
        "Quotes are stripped from your input, and sqlite_master / pragma / information_schema are "
        "blocked outright. The textbook payloads die here.",
        "String literals don't need quotes: char(65,66,67) or 0x414243 instead of 'ABC'.",
        "Can't read the catalog to list tables? Guess the name — count(*) FROM secrets succeeds "
        "(no quotes, no catalog) if the table exists.",
        "It's still 3 columns. UNION SELECT with quote-free literals, reading from secrets by name.",
        "hickok handles both at once: `hickok sql -u 'http://127.0.0.1:8666/l/sleight-of-hand/app?id=1' "
        "-p id --dump secrets` — it encodes literals quote-free and falls back to common table names.",
    ]
    remediation = ("Parameterize. Blocklisting quotes and keywords is a losing game — hex/char "
                   "literals and by-name probing walk around it. Binding the parameter as an integer "
                   "closes it for good.")
    source = (
        "idv = req.query.get('id','1').replace(\"'\", '').replace('\"','')   # strips quotes\n"
        "if any(k in idv.lower() for k in ('sqlite_master','information_schema','pragma')):\n"
        "    return BLOCKED_PAGE\n"
        'sql = f"SELECT id, name, role FROM employees WHERE id={idv}"'
    )

    def seed(self, db):
        db.execute("INSERT INTO secrets (label, value) VALUES (?,?)", ("sleight-of-hand", self.flag()))
        db.commit()   # backup_passphrase & co. are seeded company-wide in data.build now

    def handle(self, req: Request, db) -> Response:
        raw = req.query.get("id", "1")
        idv = raw.replace("'", "").replace('"', "")          # the filter: quotes stripped
        if any(k in idv.lower() for k in _BLOCKED):
            return Response(ui.shell("Sleight of Hand", '<h1>Staff Directory</h1>'
                                     '<p class="err">⛔ that query was blocked by the gate.</p>'
                                     '<p class="dim"><a href="/l/sleight-of-hand">&larr; briefing</a></p>'))
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
        <h1>Deadwood Trust — Staff Directory <span class="dim">(hardened)</span></h1>
        <form method="get" action="/l/sleight-of-hand/app">
          <input name="id" value="{html.escape(raw)}" size="48"> <button>look up</button>
        </form>
        {note}
        <table><tr><th>#</th><th>name</th><th>role</th></tr>{body_rows}</table>
        <p class="dim" style="margin-top:18px"><a href="/l/sleight-of-hand">&larr; back to the briefing</a></p>
        """
        return Response(ui.shell("Sleight of Hand — Staff Directory", body))
