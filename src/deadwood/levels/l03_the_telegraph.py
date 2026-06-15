"""Level 3 — The Telegraph. Time-based blind SQL injection: the page never changes,
only the clock does."""

from __future__ import annotations

import html

from deadwood import ui
from deadwood.level import Level, Request, Response, register


@register
class TheTelegraph(Level):
    num = 3
    slug = "the-telegraph"
    title = "The Telegraph"
    tier = "Medium"
    category = "SQL injection — time-based blind"
    brief = "The wire always says 'message logged'. Listen to how long it takes."
    objective = ("The telegraph desk acknowledges every request identically — no data, no "
                 "yes/no. Injectable at `/l/the-telegraph/app?id=1`; the only oracle is the "
                 "response time. Read the flag from `secrets` (label `the-telegraph`).")
    hints = [
        "The page is byte-for-byte the same whatever you send — no UNION, no boolean tell.",
        "But the id goes into SQL. Make a true condition sleep: id=1 AND sleep(2) — the response stalls.",
        "Time *is* the oracle: gate the sleep on a comparison, e.g. "
        "1 AND (CASE WHEN (unicode(substr((SELECT value FROM secrets WHERE label='the-telegraph'),1,1))>64) THEN sleep(2) ELSE 0 END)=0",
        "hickok picks this automatically when nothing else leaks: "
        "`hickok sql -u 'http://127.0.0.1:8666/l/the-telegraph/app?id=1' -p id --technique time --dump secrets` "
        "(slow by nature — a request per bit).",
    ]
    remediation = ("Parameterize, and validate `id` as an integer. Time-based blind survives even "
                   "when nothing is echoed and the page never changes — only binding kills it.")
    source = (
        "idv = req.query.get('id', '1')\n"
        'sql = f"SELECT count(*) FROM telegrams WHERE id={idv}"   # injectable; result ignored\n'
        "db.execute(sql).fetchone()\n"
        "return 'message logged'   # identical response every time — no in-band signal"
    )

    def seed(self, db):
        db.execute("INSERT INTO secrets (label, value) VALUES (?,?)", ("the-telegraph", self.flag()))
        db.commit()

    def handle(self, req: Request, db) -> Response:
        idv = req.query.get("id", "1")
        sql = f"SELECT count(*) FROM telegrams WHERE id={idv}"
        try:
            db.execute(sql).fetchone()       # the result is deliberately thrown away
        except Exception:
            pass
        body = f"""
        <h1>Deadwood Telegraph — Message Desk</h1>
        <p class="dim">Submit a record id to confirm a telegram.</p>
        <form method="get" action="/l/the-telegraph/app">
          <input name="id" value="{html.escape(idv)}" size="40"> <button>confirm</button>
        </form>
        <p class="ok">message logged.</p>
        <p class="dim" style="margin-top:18px"><a href="/l/the-telegraph">&larr; back to the briefing</a></p>
        """
        return Response(ui.shell("The Telegraph — Message Desk", body))
