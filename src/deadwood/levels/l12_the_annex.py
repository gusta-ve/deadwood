"""Level 12 — The Annex. UNION SQL injection where the prize lives in a **second,
ATTACHed database** (`archive`). The injectable query reads the main database; the
flag isn't there. You have to enumerate the other database and qualify it
(`archive.secrets`) — the cross-database reach a single-database walk misses."""

from __future__ import annotations

import html

from deadwood import ui
from deadwood.level import Level, Request, Response, register


@register
class TheAnnex(Level):
    num = 12
    slug = "the-annex"
    title = "The Annex"
    tier = "Brutal"
    category = "SQL injection — cross-database (ATTACH)"
    brief = "The flag isn't in this book. The company keeps an older one next door."
    objective = ("UNION-injectable staff directory at `/l/the-annex/app?id=1`. The flag is **not** in "
                 "the main database — it's in a second one the connection has ATTACHed (`archive`). "
                 "List the databases, then dump `archive.secrets` (label `the-annex`).")
    hints = [
        "It's a 3-column UNION over employees, like First Blood — but dumping the main database's "
        "`secrets` won't find this flag. It isn't there.",
        "SQLite can see every ATTACHed database on the connection: SELECT name FROM "
        "pragma_database_list shows `main` and `archive`. The flag is in the other one.",
        "Qualify the table with the database name: id=0 UNION SELECT 1,label,value FROM archive.secrets-- -",
        "A walker that only dumps the current database will miss it — point hickok here and watch "
        "whether it crosses into `archive`: "
        "`hickok sql -u 'http://127.0.0.1:8666/l/the-annex/app?id=1' -p id --dump secrets`",
    ]
    remediation = ("Parameterize. And scope database privileges: an injection should never be able to "
                   "reach an ATTACHed/linked database the app doesn't use.")
    source = (
        "idv = req.query.get('id', '1')\n"
        'sql = f"SELECT id, name, role FROM employees WHERE id={idv}"   # reads main…\n'
        "# …but the connection also has: ATTACH DATABASE ‘archive’ — and the flag is in\n"
        "# archive.secrets, reachable by a qualified UNION the injection allows."
    )

    def seed(self, db):
        # the prize lives next door — in the ATTACHed database, not main.secrets
        db.execute("INSERT INTO archive.secrets (label, value) VALUES (?,?)", ("the-annex", self.flag()))
        db.commit()

    def handle(self, req: Request, db) -> Response:
        idv = req.query.get("id", "1")
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
        <h1>Deadwood Trust — Staff Directory <span class="dim">(branch annex)</span></h1>
        <p class="dim">The current book only. Older paper is kept in the annex.</p>
        <form method="get" action="/l/the-annex/app">
          <input name="id" value="{html.escape(idv)}" size="52"> <button>look up</button>
        </form>
        {note}
        <table><tr><th>#</th><th>name</th><th>role</th></tr>{body_rows}</table>
        <p class="dim" style="margin-top:18px"><a href="/l/the-annex">&larr; back to the briefing</a></p>
        """
        return Response(ui.shell("The Annex — Staff Directory", body))
