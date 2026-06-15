"""Level 2 — Whispers. Boolean-blind SQL injection in a username check."""

from __future__ import annotations

import html

from deadwood import ui
from deadwood.level import Level, Request, Response, register


@register
class Whispers(Level):
    num = 2
    slug = "whispers"
    title = "Whispers"
    tier = "Easy"
    category = "SQL injection — boolean-blind"
    brief = "The staff sign-in only whispers yes or no. That's enough."
    objective = ("The sign-in check leaks nothing but a yes/no. Read the flag out of "
                 "`secrets` one bit at a time through `/l/whispers/app?user=admin`.")
    hints = [
        "There's a known account: username `admin`. user=admin says welcome; user=ghost says invalid.",
        "Inject into the quoted username: admin' AND '1'='1  vs  admin' AND '1'='2 — the answer flips.",
        "No data is echoed, only the yes/no. That's a boolean oracle — extract a character at a time "
        "with substr()/unicode() comparisons.",
        "The prize is secrets(label,value) where label='whispers'. e.g. "
        "admin' AND unicode(substr((SELECT value FROM secrets WHERE label='whispers'),1,1))>64-- -",
        "Let hickok do the bit-banging: "
        "`hickok sql -u 'http://127.0.0.1:8666/l/whispers/app?user=admin' -p user --dump secrets`",
    ]
    remediation = ("Parameterize (`WHERE username = ?`). A boolean oracle needs your input to change "
                   "the query's truth value — binding removes that. Don't branch the response on a "
                   "raw query either.")
    source = (
        "user = req.query.get('user', '')\n"
        'sql = f"SELECT id, name FROM employees WHERE username=\'{user}\'"   # quoted, unsanitized\n'
        "row = db.execute(sql).fetchone()\n"
        "return 'Welcome back' if row else 'Invalid login'   # no data echoed — only yes/no"
    )

    def seed(self, db):
        # a stable, well-known account so a boolean oracle has a TRUE base to calibrate on
        db.execute("INSERT INTO employees (name, role, town, username, pw_md5, email) "
                   "VALUES (?,?,?,?,?,?)",
                   ("Al Swearengen", "Branch Manager", "Deadwood", "admin",
                    "5f4dcc3b5aa765d61d8327deb882cf99", "admin@deadwood-trust.example"))
        db.execute("INSERT INTO secrets (label, value) VALUES (?,?)", ("whispers", self.flag()))
        db.commit()

    def handle(self, req: Request, db) -> Response:
        user = req.query.get("user", "")
        sql = f"SELECT id, name FROM employees WHERE username='{user}'"
        try:
            row = db.execute(sql).fetchone()
            ok = row is not None
            note = ""
        except Exception:
            ok, note = False, ""          # a broken query is just "invalid" — still a boolean tell
        verdict = ('<p class="ok">Welcome back.</p>' if ok
                   else '<p class="err">Invalid login.</p>')
        body = f"""
        <h1>Deadwood Telegraph &amp; Trust — Staff Sign-in</h1>
        <p class="dim">Enter your username to check your record.</p>
        <form method="get" action="/l/whispers/app">
          <input name="user" value="{html.escape(user)}" size="40" placeholder="username"> <button>check</button>
        </form>
        {note}{verdict}
        <p class="dim" style="margin-top:18px"><a href="/l/whispers">&larr; back to the briefing</a></p>
        """
        return Response(ui.shell("Whispers — Staff Sign-in", body))
