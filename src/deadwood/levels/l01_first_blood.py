"""Level 1 — First Blood. In-band UNION SQL injection in the staff directory."""

from __future__ import annotations

import html

from deadwood import ui
from deadwood.level import Level, Request, Response, register


@register
class FirstBlood(Level):
    num = 1
    slug = "first-blood"
    title = "First Blood"
    tier = "Tutorial"
    category = "SQL injection — UNION (in-band)"
    brief = "The staff directory trusts a number. It shouldn't."
    objective = ("Read the flag out of the hidden `secrets` table through the staff-directory "
                 "lookup at `/l/first-blood/app?id=1`.")
    hints = [
        "Open /l/first-blood/app?id=1, then change the number. Your input lands inside the SQL.",
        "Compare id=1 with id=1 AND 1=2 — the row disappears, so the condition is yours to control.",
        "The query returns three columns (id, name, role). Confirm with ORDER BY 3 / ORDER BY 4, then UNION SELECT three values.",
        "The prize is in a table named secrets(label, value). Try: id=0 UNION SELECT 1,label,value FROM secrets",
        "With hickok: `hickok sql -u 'http://127.0.0.1:8666/l/first-blood/app?id=1' -p id --dump secrets`",
    ]
    remediation = ("Use a parameterized query — `WHERE id = ?` with the value bound, never "
                   "f-stringed in — and validate that id is an integer. Then UNION/boolean "
                   "payloads have nowhere to land.")
    source = (
        "idv = req.query.get('id', '1')\n"
        'sql = f"SELECT id, name, role FROM employees WHERE id={idv}"   # user input → SQL\n'
        "rows = db.execute(sql).fetchall()"
    )

    def seed(self, db):
        db.execute("INSERT INTO secrets (label, value) VALUES (?,?)", ("first-blood", self.flag()))
        db.execute("INSERT INTO secrets (label, value) VALUES (?,?)",
                   ("smtp_relay", "telegraph:hunter2@relay.deadwood-trust.example"))
        db.commit()

    def handle(self, req: Request, db) -> Response:
        idv = req.query.get("id", "1")
        sql = f"SELECT id, name, role FROM employees WHERE id={idv}"
        try:
            rows = db.execute(sql).fetchall()
            note = ""
        except Exception as exc:                       # leak the error — classic in-band tell
            rows, note = [], f'<p class="err">query error: {html.escape(str(exc))}</p>'
        body_rows = "".join(
            f"<tr><td>{html.escape(str(r[0]))}</td><td><b>{html.escape(str(r[1]))}</b></td>"
            f"<td>{html.escape(str(r[2]))}</td></tr>" for r in rows
        ) or '<tr><td colspan="3" class="dim">no matching employee</td></tr>'
        body = f"""
        <h1>Deadwood Telegraph &amp; Trust — Staff Directory</h1>
        <p class="dim">Look up an employee by record number.</p>
        <form method="get" action="/l/first-blood/app">
          <input name="id" value="{html.escape(idv)}" size="40"> <button>look up</button>
        </form>
        {note}
        <table><tr><th>#</th><th>name</th><th>role</th></tr>{body_rows}</table>
        <p class="dim" style="margin-top:18px"><a href="/l/first-blood">&larr; back to the briefing</a></p>
        """
        return Response(ui.shell("First Blood — Staff Directory", body))
