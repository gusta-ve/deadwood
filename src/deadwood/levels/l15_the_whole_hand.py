"""Level 15 — The Whole Hand. The capstone: the **live Deadwood Trust web app**, with the
whole wraith surface in one crawlable target, and a heist you finish by chaining the
rooms together into one real conquest.

The surface a single `wraith` run lights up:
  /app                landing — an insecure tracking cookie, no security headers, dynamic copy
  /app/login          a real login (validates a password hash)
  /app/account        your area — links to your order
  /app/orders/<id>    no ownership check                         → access-control (IDOR)
  /app/admin          logged-in but no role check                → access-control (BAC)
  /app/admin-secure   proper role enforcement                    (control — must NOT flag)
  /app/directory?id=  UNION SQLi over the real (NULL/long/unicode) staff data
  /app/search?q=      reflects q unescaped                       → injection (XSS)
  /app/download?file= ../../etc/passwd traversal                 → injection (LFI)
  /app/go?url=        redirects to user input                    → injection (open redirect)
  /app/api/data       reflects Origin + credentials              → security-headers (CORS)
  /app/vault          opens only for an admin hand               → the conquest

The heist (the whole hand): recon it with wraith → SQLi the directory and dump the
**sessions** table with hickok → ride a live **admin** token as your cookie → the
vault swings open. SQLi → a live credential → access control → the house's deepest
secret. No real town had to bleed for it.
"""

from __future__ import annotations

import hashlib
import html
import time
from urllib.parse import parse_qs

from deadwood import ui
from deadwood.level import Level, Request, Response, register

# Fixed, role-tagged session tokens. Seeded into the `sessions` table so they're
# both (a) discoverable by SQLi — the heist pivot — and (b) handed to wraith for
# the access-control phase via examples/deadwood_sessions.json.
_FIXED_SESSIONS = [
    ("admin",   "dw-admin-7f3a9c1e", "admin"),     # the prize — strong password, so you must steal the token
    ("manager", "dw-mgr-2b8e1d4a",   "staff"),
    ("teller",  "dw-teller-44c0a1b9", "user"),
]
_ADMIN_PW = b"aces-and-eights-the-dead-mans-hand-1876"   # admin's password — not guessable, not crackable here

_WIRES = ["gold up a half-point", "stage from Cheyenne delayed", "vault audit Thursday",
          "new teller starts Monday", "wire from Tombstone confirmed"]


@register
class TheWholeHand(Level):
    num = 15
    slug = "the-whole-hand"
    title = "The Whole Hand"
    tier = "Endgame"
    category = "Full chain — recon → SQLi → session pivot → broken access control → the vault"
    brief = "The live company, whole. Aces and eights — play the whole hand."
    objective = ("The real Deadwood Trust web app at `/l/the-whole-hand/app` — the entire wraith "
                 "surface in one target. Recon it, then take it: SQLi the staff **directory**, dump "
                 "the **sessions** table, ride a live **admin** token as your cookie, and open the "
                 "**vault**. The flag is what's inside.")
    hints = [
        "Scout the whole app first: wraith lights the chain — an IDOR on /orders, broken access "
        "control on /admin, reflected XSS, an open redirect, reflective CORS, missing security "
        "headers — and the SQL injection on /directory that starts the heist.",
        "/admin opens for ANY logged-in hand (that's the broken access control) — but the vault reads "
        "your rank, and you don't have an admin cookie yet. You need a live admin session.",
        "The directory is UNION-injectable (3 columns) over the staff table. It shares the database "
        "with the live sessions: id=0 UNION SELECT username,token,role FROM sessions-- - lists every "
        "live token and its role. Take the one marked admin.",
        "Set it as your cookie — Cookie: session=<admin token> — and open /l/the-whole-hand/app/vault. "
        "That's SQLi → a live credential → access control → the whole hand.",
        "End to end with the tools: wraith for the map (`wraith 127.0.0.1:8666 --sessions "
        "examples/deadwood_sessions.json`), then hickok to dump sessions "
        "(`hickok sql -u 'http://127.0.0.1:8666/l/the-whole-hand/app/directory?id=1' -p id --dump sessions`).",
    ]
    remediation = ("Every layer here is one real control: parameterize the directory query, check "
                   "object ownership on /orders, enforce role (not just login) on /admin and the "
                   "vault, bind session tokens to integrity-protected cookies, scope CORS to known "
                   "origins, encode output, validate redirect targets, and send the security headers. "
                   "The chain only exists because each link was left open.")
    source = (
        "# directory (vulnerable): f\"SELECT id,name,role FROM employees WHERE id={id}\"\n"
        "# admin (BAC): if session: render(admin)        # checks login, not role\n"
        "# orders (IDOR): SELECT * FROM orders WHERE id=<id>   # no ownership check\n"
        "# vault: if session.role == 'admin': reveal(flag)     # the only real gate left"
    )

    # --------------------------------------------------------------- seeding
    def seed(self, db):
        db.execute("INSERT INTO employees (name, role, town, username, pw_md5, email) "
                   "VALUES (?,?,?,?,?,?)",
                   ("Al Swearengen", "Vault Manager", "Deadwood", "admin",
                    hashlib.md5(_ADMIN_PW).hexdigest(), "admin@deadwood-trust.example"))
        for user, token, role in _FIXED_SESSIONS:
            db.execute("INSERT INTO sessions (username, token, role, created) VALUES (?,?,?,?)",
                       (user, token, role, "1876-06-28T09:00"))
        db.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, owner TEXT, item TEXT)")
        db.executemany("INSERT INTO orders (id, owner, item) VALUES (?,?,?)", [
            (1, "teller", "Stagecoach freight — $80"),
            (2, "manager", "Vault lease, quarter — $300"),
            (3, "admin", "Gold shipment, bullion — $5,000"),
            (4, "teller", "Telegraph line repair — $45"),
            (5, "manager", "Payroll, June — $1,240"),
        ])
        db.execute("INSERT INTO secrets (label, value) VALUES (?,?)", ("the-whole-hand", self.flag()))
        db.commit()

    # --------------------------------------------------------------- session
    def _session(self, req: Request, db):
        """(username, role) for the `session` cookie, or None. Parameterized — the
        cookie check itself is not the injectable surface (the directory is)."""
        cookie = ""
        if req.headers is not None:
            cookie = req.headers.get("Cookie", "") or ""
        token = None
        for part in cookie.split(";"):
            p = part.strip()
            if p.startswith("session="):
                token = p[len("session="):]
        if not token:
            return None
        return db.execute("SELECT username, role FROM sessions WHERE token=?", (token,)).fetchone()

    def _page(self, title, body, headers=None, status=200):
        return Response(ui.shell(title, body), status=status, headers=headers or {})

    def _need_login(self):
        return self._page("Sign in", '<h1>Deadwood Trust</h1>'
                          '<p class="err">Please sign in to continue.</p>'
                          '<p><a href="/l/the-whole-hand/app/login">sign in &rarr;</a></p>')

    # ---------------------------------------------------------------- router
    def handle(self, req: Request, db) -> Response:
        sub = req.subpath.rstrip("/") or "/"
        if sub == "/":
            return self._landing()
        if sub == "/login":
            return self._login(req, db)
        if sub == "/account":
            return self._account(req, db)
        if sub.startswith("/orders/"):
            return self._order(req, db, sub[len("/orders/"):])
        if sub == "/admin":
            return self._admin(req, db)
        if sub == "/admin-secure":
            return self._admin_secure(req, db)
        if sub == "/directory":
            return self._directory(req, db)
        if sub == "/search":
            return self._search(req)
        if sub == "/download":
            return self._download(req)
        if sub == "/go":
            return self._go(req)
        if sub == "/api/data":
            return self._api(req)
        if sub == "/vault":
            return self._vault(req, db)
        # soft-404: a 200 "page not found" (calibration noise for a content scanner)
        return self._page("Not found", '<h1>Deadwood Trust</h1>'
                          '<p class="dim">That page isn\'t here. Try the <a href="/l/the-whole-hand/app">'
                          'lobby</a>.</p>')

    # ---------------------------------------------------------------- pages
    def _landing(self):
        wire = _WIRES[int(time.time()) % len(_WIRES)]            # rotates — dynamic page noise
        body = f"""
        <h1>Deadwood Telegraph &amp; Trust Co.</h1>
        <p class="dim">Today on the wire: {html.escape(wire)}.</p>
        <div class="panel">
          <a href="/l/the-whole-hand/app/login">Sign in</a> ·
          <a href="/l/the-whole-hand/app/account">My account</a> ·
          <a href="/l/the-whole-hand/app/admin">Admin</a> ·
          <a href="/l/the-whole-hand/app/admin-secure">Admin (secure)</a><br>
          <a href="/l/the-whole-hand/app/directory?id=1">Staff directory</a> ·
          <a href="/l/the-whole-hand/app/search?q=deadwood">Search</a> ·
          <a href="/l/the-whole-hand/app/download?file=readme.txt">Download</a> ·
          <a href="/l/the-whole-hand/app/go?url=/l/the-whole-hand/app">Go</a> ·
          <a href="/l/the-whole-hand/app/vault">Vault</a>
        </div>
        <p class="dim" style="margin-top:18px"><a href="/l/the-whole-hand">&larr; back to the briefing</a></p>
        """
        # insecure tracking cookie: no HttpOnly / Secure / SameSite (a security-headers tell)
        return self._page("Deadwood Trust", body, headers={"Set-Cookie": "tracking=1; Path=/"})

    def _login(self, req: Request, db):
        if req.method == "POST":
            form = parse_qs(req.body.decode("utf-8", "replace"))
            user = (form.get("user") or form.get("username") or [""])[0]
            pw = (form.get("password") or form.get("pass") or [""])[0]
            row = db.execute("SELECT pw_md5 FROM employees WHERE username=?", (user,)).fetchone()
            if row and row[0] == hashlib.md5(pw.encode()).hexdigest():
                tok = db.execute("SELECT token FROM sessions WHERE username=?", (user,)).fetchone()
                token = tok[0] if tok else f"sess-{user}"
                return self._page("Signed in", f'<h1>Welcome back, {html.escape(user)}.</h1>'
                                  '<p><a href="/l/the-whole-hand/app/account">my account &rarr;</a></p>',
                                  headers={"Set-Cookie": f"session={token}; Path=/"})
            return self._page("Sign in", '<h1>Sign in</h1><p class="err">Invalid credentials.</p>'
                              + self._login_form())
        return self._page("Sign in", "<h1>Sign in</h1>" + self._login_form())

    def _login_form(self):
        return ('<form method="post" action="/l/the-whole-hand/app/login">'
                '<input name="user" placeholder="username" size="28"><br><br>'
                '<input name="password" type="password" placeholder="password" size="28"> '
                '<button>sign in</button></form>')

    def _account(self, req: Request, db):
        sess = self._session(req, db)
        if not sess:
            return self._need_login()
        user, role = sess
        own = db.execute("SELECT id FROM orders WHERE owner=? LIMIT 1", (user,)).fetchone()
        oid = own[0] if own else 1
        body = (f'<h1>Account — {html.escape(user)}</h1>'
                f'<p class="dim">role: {html.escape(role)}</p>'
                f'<p><a href="/l/the-whole-hand/app/orders/{oid}">View my order #{oid} &rarr;</a></p>')
        return self._page("Account", body)

    def _order(self, req: Request, db, raw_id):
        sess = self._session(req, db)
        if not sess:
            return self._need_login()
        try:
            oid = int(raw_id)
        except ValueError:
            return self._page("Order", '<h1>Order</h1><p class="dim">no such order.</p>')
        row = db.execute("SELECT id, owner, item FROM orders WHERE id=?", (oid,)).fetchone()
        if not row:
            return self._page("Order", '<h1>Order</h1><p class="dim">no such order.</p>')
        # VULNERABLE: no ownership check — any logged-in user reads any order (IDOR)
        body = (f'<h1>Order #{row[0]}</h1><p>Owner: <b>{html.escape(row[1])}</b></p>'
                f'<p>{html.escape(row[2])}</p>')
        return self._page("Order", body)

    def _admin(self, req: Request, db):
        sess = self._session(req, db)
        if not sess:
            return self._need_login()
        # VULNERABLE: checks login, not role — broken access control
        body = ('<h1>Admin — Daily Position</h1>'
                '<p>Vault balance: <b>$1,204,553</b> in gold and notes.</p>'
                '<p class="dim">The vault door is down the hall — but it reads the rank of your hand.</p>'
                '<p><a href="/l/the-whole-hand/app/vault">the vault &rarr;</a></p>')
        return self._page("Admin", body)

    def _admin_secure(self, req: Request, db):
        sess = self._session(req, db)
        if not sess:
            return self._need_login()
        if sess[1] != "admin":
            return self._page("Forbidden", '<h1>403 Forbidden</h1>'
                              '<p class="dim">This office is for the manager only.</p>', status=403)
        return self._page("Admin (secure)", '<h1>Admin — Daily Position (secure)</h1>'
                          '<p>Vault balance: <b>$1,204,553</b>.</p>')

    def _directory(self, req: Request, db):
        idv = req.query.get("id", "1")
        sql = f"SELECT id, name, role FROM employees WHERE id={idv}"   # VULNERABLE: UNION SQLi
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
        <h1>Deadwood Trust — Staff Directory</h1>
        <form method="get" action="/l/the-whole-hand/app/directory">
          <input name="id" value="{html.escape(idv)}" size="52"> <button>look up</button>
        </form>
        {note}
        <table><tr><th>#</th><th>name</th><th>role</th></tr>{body_rows}</table>
        """
        return self._page("Staff Directory", body)

    def _search(self, req: Request):
        q = req.query.get("q", "")
        # VULNERABLE: reflects input unescaped — reflected XSS
        return self._page("Search", f"<h1>Results for {q}</h1><p class='dim'>nothing found.</p>")

    def _download(self, req: Request):
        f = req.query.get("file", "readme.txt")
        low = f.replace("\\", "/").lower()
        if "etc/passwd" in low:                # VULNERABLE: path traversal / LFI
            return Response("root:x:0:0:root:/root:/bin/bash\n"
                            "daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\n"
                            "www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin\n",
                            content_type="text/plain; charset=utf-8")
        return self._page("Download", f"<h1>{html.escape(f)}</h1><pre>(file contents)</pre>")

    def _go(self, req: Request):
        # VULNERABLE: open redirect — destination is user-controlled, unvalidated
        return Response("", status=302, headers={"Location": req.query.get("url", "/")})

    def _api(self, req: Request):
        # VULNERABLE: reflects any Origin and allows credentials (CORS misconfig)
        origin = "*"
        if req.headers is not None:
            origin = req.headers.get("Origin", "*") or "*"
        return Response('{"ok":true,"balance":1204553}',
                        content_type="application/json; charset=utf-8",
                        headers={"Access-Control-Allow-Origin": origin,
                                 "Access-Control-Allow-Credentials": "true"})

    def _vault(self, req: Request, db):
        sess = self._session(req, db)
        if not sess:
            return self._need_login()
        user, role = sess
        if role != "admin":
            return self._page("The Vault", '<h1>The Vault</h1>'
                              f'<p class="err">The door won\'t open for a {html.escape(role)} hand.</p>'
                              '<p class="dim">It wants an admin. You\'ll need a live admin session.</p>',
                              status=403)
        body = (f'<h1>The Vault — open</h1>'
                f'<div class="panel ok"><p>You walked in off the recon, cracked a number in the '
                f'directory, lifted a live hand off the wire, and rode it straight through the door. '
                f'Aces and eights — the dead man\'s hand — and the house\'s deepest secret sitting in '
                f'your palm:</p><h2 class="gold">{html.escape(self.flag())}</h2>'
                f'<p class="dim">That\'s the whole hand. No real town had to bleed for it — '
                f'just this one, the one that\'s yours. Submit it: '
                f'<code>deadwood flag the-whole-hand \'{html.escape(self.flag())}\'</code></p></div>')
        return self._page("The Vault", body)
