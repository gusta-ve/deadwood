"""Level 5 — The Bouncer. SQL injection authentication bypass."""

from __future__ import annotations

import hashlib
import html

from deadwood import ui
from deadwood.level import Level, Request, Response, register


@register
class TheBouncer(Level):
    num = 5
    slug = "the-bouncer"
    title = "The Bouncer"
    tier = "Medium"
    category = "SQL injection — authentication bypass"
    brief = "The vault door checks a password. Or does it."
    objective = ("Sign in as `admin` at `/l/the-bouncer/app` without knowing the password. "
                 "What's behind the door is the flag.")
    hints = [
        "It's a real login: username + password, both checked in one SQL query.",
        "The username is quoted and unsanitized. Comment the password check out: user=admin'-- -",
        "Or make the whole condition true: user=' OR '1'='1'-- - (you'll land as the first account).",
    ]
    remediation = ("Parameterize the lookup and verify the password hash in code (constant-time "
                   "compare). Building the auth query from input lets a comment or an always-true "
                   "clause walk straight past the password.")
    source = (
        "user = req.query.get('user', ''); pw = req.query.get('pass', '')\n"
        "h = md5(pw)\n"
        'sql = f"SELECT username,role FROM employees WHERE username=\'{user}\' AND pw_md5=\'{h}\'"\n'
        "row = db.execute(sql).fetchone()   # any row → you're in"
    )

    def seed(self, db):
        db.execute("INSERT INTO employees (name, role, town, username, pw_md5, email) "
                   "VALUES (?,?,?,?,?,?)",
                   ("Al Swearengen", "Vault Manager", "Deadwood", "admin",
                    hashlib.md5(b"a-very-long-unguessable-passphrase").hexdigest(),
                    "admin@deadwood-trust.example"))
        db.commit()

    def handle(self, req: Request, db) -> Response:
        user = req.query.get("user", "")
        pw = req.query.get("pass", "")
        h = hashlib.md5(pw.encode()).hexdigest()
        sql = f"SELECT username, role FROM employees WHERE username='{user}' AND pw_md5='{h}'"
        try:
            row = db.execute(sql).fetchone()
        except Exception:
            row = None
        if row:
            verdict = (f'<p class="ok">Signed in as <b>{html.escape(str(row[0]))}</b> '
                       f'({html.escape(str(row[1]))}).</p>'
                       f'<div class="panel">Behind the vault door, a sealed note reads: '
                       f'<span class="gold">{html.escape(self.flag())}</span></div>')
        else:
            verdict = '<p class="err">Access denied.</p>'
        body = f"""
        <h1>Deadwood Trust — Vault Sign-in</h1>
        <form method="get" action="/l/the-bouncer/app">
          <input name="user" value="{html.escape(user)}" placeholder="username" size="34"><br><br>
          <input name="pass" value="" placeholder="password" size="34" type="password"> <button>sign in</button>
        </form>
        {verdict}
        <p class="dim" style="margin-top:18px"><a href="/l/the-bouncer">&larr; back to the briefing</a></p>
        """
        return Response(ui.shell("The Bouncer — Vault Sign-in", body))
