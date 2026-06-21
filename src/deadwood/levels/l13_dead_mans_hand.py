"""Level 8 — Dead Man's Hand. Boolean-blind SQL injection behind a WAF denylist:
a quote filter, a blocked catalog, and a block page that is neither true nor false."""

from __future__ import annotations

import html

from deadwood import ui
from deadwood.level import Level, Request, Response, register

# The WAF: any of these in the input returns the block page (a third state).
_DENY = ("union", "sqlite_master", "information_schema", "pragma")


@register
class DeadMansHand(Level):
    num = 13
    slug = "dead-mans-hand"
    title = "Dead Man's Hand"
    tier = "Brutal"
    category = "SQL injection — blind behind a WAF"
    brief = "Aces and eights. The wire answers yes or no, and a guard eats the rest."
    objective = ("A record check at `/l/dead-mans-hand/app?id=1` that only tells you exists / "
                 "doesn't — and a WAF that strips quotes, blocks the catalog, and **blocks UNION** "
                 "with a page that's neither yes nor no. Read the flag from `secrets` anyway.")
    hints = [
        "It's numeric and blind: id=1 says 'record found', id=999 says 'no such record'. No data, no UNION.",
        "UNION, sqlite_master, pragma and information_schema all hit a block page ('Some things are "
        "disabled!!!') — that page is a third state, not a 'false'. Don't read it as a bit.",
        "So: boolean-blind, by name. substr()/unicode() still work, and count(*) FROM secrets confirms "
        "the table exists without the catalog. Quotes are stripped, so use no string literals.",
        "id=1 AND (unicode(substr((SELECT value FROM secrets),1,1)))>64 — flip the comparison to read each char.",
        "hickok handles the block page (it flags the anomaly), bypasses the catalog by name, and grinds "
        "it out: `hickok sql -u 'http://127.0.0.1:8666/l/dead-mans-hand/app?id=1' -p id --dump secrets` "
        "(slow — a request per bit).",
    ]
    remediation = ("Parameterize. A denylist WAF is a speed bump — it blocks keywords, not the bug. "
                   "Boolean/by-name extraction walks around it; only binding the parameter removes it.")
    source = (
        "raw = req.query.get('id','1')\n"
        "if any(k in raw.lower() for k in ('union','sqlite_master','information_schema','pragma')):\n"
        "    return BLOCK_PAGE          # a third state — neither found nor not-found\n"
        "idv = raw.replace(\"'\",'').replace('\"','')   # quotes stripped\n"
        'sql = f"SELECT id FROM employees WHERE id={idv}"\n'
        "return 'record found' if db.execute(sql).fetchone() else 'no such record'  # blind"
    )

    def seed(self, db):
        db.execute("INSERT INTO secrets (label, value) VALUES (?,?)", ("dead-mans-hand", self.flag()))
        db.commit()

    def handle(self, req: Request, db) -> Response:
        raw = req.query.get("id", "1")
        if any(k in raw.lower() for k in _DENY):
            return Response(ui.shell("Dead Man's Hand", '<h1>Records Desk</h1>'
                                     '<p class="err">⛔ Some things are disabled!!!</p>'
                                     '<p class="dim"><a href="/l/dead-mans-hand">&larr; briefing</a></p>'))
        idv = raw.replace("'", "").replace('"', "")
        try:
            row = db.execute(f"SELECT id FROM employees WHERE id={idv}").fetchone()
            verdict = ('<p class="ok">record found.</p>' if row
                       else '<p class="err">no such record.</p>')
        except Exception:
            verdict = '<p class="err">no such record.</p>'      # errors read as not-found (blind)
        body = f"""
        <h1>Deadwood Trust — Records Desk</h1>
        <p class="dim">Confirm an employee record by number. (We only confirm; we don't show.)</p>
        <form method="get" action="/l/dead-mans-hand/app">
          <input name="id" value="{html.escape(raw)}" size="48"> <button>confirm</button>
        </form>
        {verdict}
        <p class="dim" style="margin-top:18px"><a href="/l/dead-mans-hand">&larr; back to the briefing</a></p>
        """
        return Response(ui.shell("Dead Man's Hand — Records Desk", body))
