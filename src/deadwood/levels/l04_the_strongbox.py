"""Level 4 — The Strongbox. In-band UNION SQL injection in a **double-quoted** string
context (a different breakout from the single-quote rooms) — so a tool has to detect
the right quote, not assume one."""

from __future__ import annotations

import html

from deadwood import ui
from deadwood.level import Level, Request, Response, register


@register
class TheStrongbox(Level):
    num = 4
    slug = "the-strongbox"
    title = "The Strongbox"
    tier = "Medium"
    category = "SQL injection — UNION (double-quote context)"
    brief = "The safe-deposit desk quotes your box number — with double quotes."
    objective = ("The safe-deposit lookup at `/l/the-strongbox/app?box=DW-10000` drops your input "
                 "inside a **double-quoted** string. Break out with `\"`, UNION the three columns, "
                 "and read the flag from `secrets` (label `the-strongbox`).")
    hints = [
        "box=DW-10000 lists a box. A single quote does nothing here — the string is double-quoted. "
        "Try box=DW-10000\" — now the query breaks.",
        "Same UNION game, double-quote breakout: it returns three columns (number, kind, balance). "
        "Confirm with ORDER BY, then UNION SELECT three values, commenting off the trailing quote.",
        "box=zzz\" UNION SELECT label,value,1 FROM secrets-- -  (the flag is the row labelled the-strongbox).",
        "hickok detects the quote context on its own: "
        "`hickok sql -u 'http://127.0.0.1:8666/l/the-strongbox/app?box=DW-10000' -p box --dump secrets`",
    ]
    remediation = ("Parameterize. The quote style is irrelevant once the value is bound; concatenating "
                   "it — single or double — is the whole bug.")
    source = (
        "box = req.query.get('box', 'DW-10000')\n"
        'sql = f\'SELECT number, kind, balance FROM accounts WHERE number="{box}"\'   # double-quoted\n'
        "rows = db.execute(sql).fetchall()"
    )

    def seed(self, db):
        db.execute("INSERT INTO secrets (label, value) VALUES (?,?)", ("the-strongbox", self.flag()))
        db.commit()

    def handle(self, req: Request, db) -> Response:
        box = req.query.get("box", "DW-10000")
        sql = f'SELECT number, kind, balance FROM accounts WHERE number="{box}"'
        try:
            rows = db.execute(sql).fetchall()
            note = ""
        except Exception as exc:
            rows, note = [], f'<p class="err">query error: {html.escape(str(exc))}</p>'
        body_rows = "".join(
            f"<tr><td><b>{html.escape(str(r[0]))}</b></td><td>{html.escape(str(r[1]))}</td>"
            f"<td>{html.escape(str(r[2]))}</td></tr>" for r in rows
        ) or '<tr><td colspan="3" class="dim">no such box</td></tr>'
        body = f"""
        <h1>Deadwood Trust — Safe-Deposit Desk</h1>
        <p class="dim">Look up a box by its number.</p>
        <form method="get" action="/l/the-strongbox/app">
          <input name="box" value="{html.escape(box)}" size="44"> <button>look up</button>
        </form>
        {note}
        <table><tr><th>box</th><th>kind</th><th>balance</th></tr>{body_rows}</table>
        <p class="dim" style="margin-top:18px"><a href="/l/the-strongbox">&larr; back to the briefing</a></p>
        """
        return Response(ui.shell("The Strongbox — Safe-Deposit Desk", body))
