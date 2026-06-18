"""Level — The Ledger. Error-based SQL injection: a verbose MySQL error is the read
channel, and (like the real thing) `extractvalue`/`updatexml` truncate the leak at
~32 characters — so a value longer than that has to be read in windows and
reassembled. Models MySQL on a SQLite backend (the range is self-contained)."""

from __future__ import annotations

import html
import re

from deadwood import ui
from deadwood.level import Level, Request, Response, register

# The MySQL XPATH error functions truncate the embedded text around here. A read
# wider than this comes back clipped; the extractor must window past the cut.
_ERR_WINDOW = 32
_ERR_FN = re.compile(r"(?:extractvalue|updatexml)\s*\(", re.I)


def _leak_expr(param: str) -> str | None:
    """The expression a payload asked to leak: whatever sits after the `0x7e` (~)
    marker inside the error function, captured balanced up to the function's own
    closing paren. Mirrors `extractvalue(1,concat(0x7e,<expr>))` /
    `updatexml(1,concat(0x7e,<expr>),1)`."""
    if not _ERR_FN.search(param):
        return None
    i = param.lower().find("0x7e")
    if i < 0:
        return None
    j = param.find(",", i)
    if j < 0:
        return None
    depth, out = 0, []
    for ch in param[j + 1:]:
        if ch == "(":
            depth += 1
        elif ch == ")":
            if depth == 0:        # the ) that closes concat( — stop here
                break
            depth -= 1
        out.append(ch)
    expr = "".join(out).strip()
    return expr or None


def _hex_to_char(m) -> str:
    """A MySQL hex string literal (`0x68656c6c6f`) as a SQLite char() expression, so
    the markers/separators/table-names a tool encodes hex (to dodge quote filters)
    still render to the right text here."""
    h = m.group(1)
    if len(h) % 2:                       # not a whole-byte literal — leave it (it's a number)
        return m.group(0)
    return "char(" + ",".join(str(b) for b in bytes.fromhex(h)) + ")"


def _to_sqlite(expr: str) -> str:
    """Translate the MySQL dialect a tool emits into the SQLite the range runs:
    `substring`→`substr`, the `SEPARATOR` keyword→a comma arg, and `0x..` hex string
    literals→char(). Enough that an error-channel dump (group_concat of a whole
    table) actually executes — and so meets the same 1024-byte cap and 32-char
    windowing as the real thing."""
    sql = re.sub(r"\bsubstring\s*\(", "substr(", expr, flags=re.I)
    sql = re.sub(r"\s+SEPARATOR\s+", ", ", sql, flags=re.I)
    sql = re.sub(r"0x([0-9a-fA-F]+)", _hex_to_char, sql)
    return sql


def _eval_leak(expr: str, db) -> str:
    """Evaluate the leak expression against the world and return its text. Anything
    that doesn't evaluate (e.g. a MySQL `information_schema` probe with no SQLite
    equivalent) leaks empty — the channel fired, there was just nothing to read."""
    try:
        row = db.execute("SELECT " + _to_sqlite(expr)).fetchone()
    except Exception:
        return ""
    return "" if row is None or row[0] is None else str(row[0])


def xpath_leak(param: str, db) -> str | None:
    """The text an `extractvalue`/`updatexml` payload pulls out — truncated to the
    real ~32-char window, so a longer value comes back clipped (the bug to window
    around). None when the param carries no error-function payload."""
    expr = _leak_expr(param)
    if expr is None:
        return None
    return _eval_leak(expr, db)[:_ERR_WINDOW]


@register
class TheLedger(Level):
    num = 3
    slug = "the-ledger"
    title = "The Ledger"
    tier = "Easy"
    category = "SQL injection — error-based (extractvalue, 32-char windows)"
    brief = "The wire-reference desk spills the database's own error. Read it."
    objective = ("The reference lookup at `/l/the-ledger/app?ref=DW-1042` builds a query in a "
                 "string context and **echoes the database error verbatim**. Force the value of "
                 "`secrets` (label `the-ledger`) out through an `extractvalue`/`updatexml` error — "
                 "and mind the ~32-char truncation: the flag is longer, so read it in windows.")
    hints = [
        "A single quote breaks it: ref=DW-1042' returns a MySQL syntax error. Balanced (ref=DW-1042'') "
        "is fine — classic error-based.",
        "The error echoes back, so put data in it: "
        "ref=DW-1042' AND extractvalue(1,concat(0x7e,(SELECT value FROM secrets WHERE label='the-ledger')))-- -",
        "You'll only get the first ~32 characters — extractvalue truncates. The flag is longer. "
        "Window it: wrap the value in substring((…),1,32), then substring((…),33,32), and stitch the pieces.",
        "hickok reads error channels in 32-char windows and reassembles automatically: "
        "`hickok sql -u 'http://127.0.0.1:8666/l/the-ledger/app?ref=DW-1042' -p ref --technique error --dump secrets`",
    ]
    remediation = ("Parameterize, and never echo the raw database error to the client. Error-based "
                   "exfil needs a verbose error reflected back; a generic 500 and a bound parameter "
                   "both close it.")
    source = (
        "ref = req.query.get('ref', 'DW-1042')\n"
        'sql = f"SELECT amount FROM ledger WHERE ref=\'{ref}\'"   # string context, unsanitized\n'
        "try:\n"
        "    db.execute(sql)\n"
        "except Exception as exc:\n"
        '    return f"<pre>{exc}</pre>"   # the raw DB error is echoed — the read channel'
    )

    def seed(self, db):
        db.execute("INSERT INTO secrets (label, value) VALUES (?,?)", ("the-ledger", self.flag()))
        db.commit()

    def _error(self, message: str, ref: str) -> Response:
        body = f"""
        <h1>Deadwood Trust — Wire Reference Desk</h1>
        <form method="get" action="/l/the-ledger/app">
          <input name="ref" value="{html.escape(ref)}" size="60"> <button>look up</button>
        </form>
        <p class="dim">Database said:</p>
        <pre class="err">{html.escape(message, quote=False)}</pre>
        <p class="dim" style="margin-top:18px"><a href="/l/the-ledger">&larr; back to the briefing</a></p>
        """
        return Response(ui.shell("The Ledger — Wire Reference Desk", body), status=500)

    def handle(self, req: Request, db) -> Response:
        ref = req.query.get("ref", "DW-1042")
        # (1) the error read-channel: an extractvalue/updatexml payload leaks a value,
        #     truncated to ~32 chars exactly like MySQL — so the long flag needs windows.
        leak = xpath_leak(ref, db)
        if leak is not None:
            return self._error(f"XPATH syntax error in '~{leak}'", ref)
        # (2) an unbalanced quote raises the verbose MySQL syntax error (the in-band tell).
        if ref.count("'") % 2:
            return self._error(
                "You have an error in your SQL syntax; check the manual that corresponds to your "
                "MySQL server version for the right syntax to use near \"''\" at line 1", ref)
        # (3) otherwise the reference resolves normally.
        body = f"""
        <h1>Deadwood Trust — Wire Reference Desk</h1>
        <p class="dim">Look up a wire by its ledger reference.</p>
        <form method="get" action="/l/the-ledger/app">
          <input name="ref" value="{html.escape(ref)}" size="60"> <button>look up</button>
        </form>
        <div class="panel"><b>{html.escape(ref)}</b> — settled, posted to the day book.</div>
        <p class="dim" style="margin-top:18px"><a href="/l/the-ledger">&larr; back to the briefing</a></p>
        """
        return Response(ui.shell("The Ledger — Wire Reference Desk", body))
