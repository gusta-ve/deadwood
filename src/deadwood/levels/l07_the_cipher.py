"""Level 7 — The Cipher. Server-side template injection that evaluates user
expressions → arbitrary code execution."""

from __future__ import annotations

import builtins
import html
import os
import re

from deadwood import ui
from deadwood.level import Level, Request, Response, register

_EXPR = re.compile(r"\{\{(.+?)\}\}")


@register
class TheCipher(Level):
    num = 7
    slug = "the-cipher"
    title = "The Cipher"
    tier = "Hard"
    category = "Server-side template injection → RCE"
    brief = "The greeting-card press renders whatever you write. Including code."
    objective = ("The card press at `/l/the-cipher/app?name=…` renders `{{ … }}` in your message "
                 "as a Python expression. Get code execution and read the flag from the "
                 "environment variable `DEADWOOD_CIPHER`.")
    hints = [
        "Type a name — it prints 'Hello, <name>'. Now try name={{7*7}}. It renders 49: template injection.",
        "Inside {{ }} is real Python eval. Reach the stdlib: {{__import__('os').getpid()}} returns a number.",
        "The flag is an environment variable. Read it: {{__import__('os').environ['DEADWOOD_CIPHER']}}",
    ]
    remediation = ("Never eval or f-string untrusted input as a template. Use a real template engine "
                   "with autoescaping and no expression evaluation, and pass user data as context — "
                   "data, never code.")
    source = (
        "name = req.query.get('name', 'friend')\n"
        'tpl = f"Hello, {name}!"\n'
        "out = re.sub(r'\\{\\{(.+?)\\}\\}', lambda m: str(eval(m.group(1))), tpl)   # evals user code"
    )

    def seed(self, db):
        os.environ["DEADWOOD_CIPHER"] = self.flag()       # the prize, in the server's environment

    def _render(self, tpl: str) -> str:
        def ev(m):
            try:
                return str(eval(m.group(1), {"__builtins__": builtins}))   # noqa: S307 (the vuln)
            except Exception as exc:
                return f"[render error: {exc}]"
        return _EXPR.sub(ev, tpl)

    def handle(self, req: Request, db) -> Response:
        name = req.query.get("name", "friend")
        rendered = self._render(f"Hello, {name}! Welcome to the Deadwood print shop.")
        body = f"""
        <h1>Deadwood Print Shop — Greeting Cards</h1>
        <p class="dim">Write a name and we'll set it in type.</p>
        <form method="get" action="/l/the-cipher/app">
          <input name="name" value="{html.escape(name)}" size="48"> <button>print</button>
        </form>
        <div class="panel">{html.escape(rendered)}</div>
        <p class="dim" style="margin-top:18px"><a href="/l/the-cipher">&larr; back to the briefing</a></p>
        """
        return Response(ui.shell("The Cipher — Print Shop", body))
