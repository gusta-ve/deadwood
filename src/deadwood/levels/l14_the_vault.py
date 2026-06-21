"""Level 14 — The Vault. Second-order SQL injection: input stored safely, then used
unsafely somewhere else entirely."""

from __future__ import annotations

import html

from deadwood import ui
from deadwood.level import Level, Request, Response, register


@register
class TheVault(Level):
    num = 14
    slug = "the-vault"
    title = "The Vault"
    tier = "Impossible"
    category = "SQL injection — second-order (stored)"
    brief = "Sign the guestbook. It's read back, later, by something that trusts it."
    objective = ("Two doors. `/l/the-vault/app/register?nickname=…` stores your guest name "
                 "**safely** (parameterized). But `/l/the-vault/app/board` looks each stored name "
                 "up in a *second* query, unescaped. Make the flag from `secrets` appear on the "
                 "board.")
    hints = [
        "Register a name, then open the board. The board says where each guest is from — it runs "
        "SELECT town FROM employees WHERE name='<your stored name>'.",
        "The register form is parameterized — you can't inject there. But the board trusts what was "
        "stored. That's second-order: the payload lands later, on a different query.",
        "Your stored name is put into the board query between quotes, one column (town). UNION it.",
        "Register the nickname:  nobody' UNION SELECT value FROM secrets-- -  then open the board.",
    ]
    remediation = ("Parameterize *every* query, including the ones that read data back out of your "
                   "own database. Trusting stored data because it 'came from us' is exactly the "
                   "second-order trap — treat it as untrusted at every use.")
    source = (
        "# register (safe): db.execute('INSERT INTO guests(nick) VALUES (?)', (nickname,))\n"
        "# board (vulnerable): for nick in stored_nicks:\n"
        "#     db.execute(f\"SELECT town FROM employees WHERE name='{nick}'\")   # nick trusted here"
    )

    def seed(self, db):
        db.execute("CREATE TABLE IF NOT EXISTS guests (id INTEGER PRIMARY KEY, nick TEXT)")
        db.execute("INSERT INTO secrets (label, value) VALUES (?,?)", ("the-vault", self.flag()))
        db.commit()

    def handle(self, req: Request, db) -> Response:
        sub = req.subpath.rstrip("/")
        if sub == "/register":
            nick = req.query.get("nickname", "")
            db.execute("INSERT INTO guests (nick) VALUES (?)", (nick,))    # stored SAFELY
            db.commit()
            body = (f'<h1>Guestbook</h1><p class="ok">Signed in as '
                    f'<b>{html.escape(nick)}</b>.</p>'
                    f'<p><a href="/l/the-vault/app/board">open the guestbook board &rarr;</a></p>'
                    f'<p class="dim"><a href="/l/the-vault/app">&larr; back</a></p>')
            return Response(ui.shell("The Vault — Guestbook", body))
        if sub == "/board":
            rows = db.execute("SELECT nick FROM guests").fetchall()
            lines = []
            for (nick,) in rows:
                try:                                                       # nick TRUSTED here (vuln)
                    res = db.execute(f"SELECT town FROM employees WHERE name='{nick}'").fetchall()
                    towns = ", ".join(str(r[0]) for r in res) or "parts unknown"
                except Exception as exc:
                    towns = f"(error: {exc})"
                lines.append(f"<tr><td>{html.escape(str(nick))}</td><td>{html.escape(towns)}</td></tr>")
            rows_html = "".join(lines) or '<tr><td colspan="2" class="dim">no guests yet</td></tr>'
            body = (f'<h1>Guestbook Board</h1><table><tr><th>guest</th><th>hails from</th></tr>'
                    f'{rows_html}</table>'
                    f'<p class="dim" style="margin-top:18px"><a href="/l/the-vault/app">&larr; back</a></p>')
            return Response(ui.shell("The Vault — Board", body))
        body = """
        <h1>Deadwood Trust — Guestbook</h1>
        <p class="dim">Sign the book; the board shows where every guest hails from.</p>
        <form method="get" action="/l/the-vault/app/register">
          <input name="nickname" placeholder="your name" size="48"> <button>sign in</button>
        </form>
        <p><a href="/l/the-vault/app/board">open the guestbook board &rarr;</a></p>
        <p class="dim" style="margin-top:18px"><a href="/l/the-vault">&larr; back to the briefing</a></p>
        """
        return Response(ui.shell("The Vault — Guestbook", body))
