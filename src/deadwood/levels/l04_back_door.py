"""Level 4 — Back Door. OS command injection in a diagnostics tool: the road to a
shell (and the flag lives in the process environment)."""

from __future__ import annotations

import html
import os
import subprocess

from deadwood import ui
from deadwood.level import Level, Request, Response, register


@register
class BackDoor(Level):
    num = 4
    slug = "back-door"
    title = "Back Door"
    tier = "Medium"
    category = "OS command injection → shell"
    brief = "The diagnostics page pings a host you give it. Through a shell."
    objective = ("The network-diagnostics tool runs your host straight through a shell. Get "
                 "command execution at `/l/back-door/app?host=127.0.0.1` and read the flag from "
                 "the process environment (`DEADWOOD_FLAG`).")
    hints = [
        "It runs `ping -c1 -W1 <host>` in a shell. What you put in `host` rides along.",
        "Chain a command: host=127.0.0.1; id — the `id` output shows up under the ping.",
        "The flag is an environment variable: host=127.0.0.1; echo $DEADWOOD_FLAG",
        "Want a real foothold? Catch a shell with hickok: `hickok -l 9001` in one terminal, then "
        "inject one of `hickok payloads 127.0.0.1 9001` (the python3 one is sh-safe). Then `env`.",
    ]
    remediation = ("Never build a shell string from user input. Call the binary directly with an "
                   "argument list (`subprocess.run(['ping','-c1','-W1', host])`, no `shell=True`) "
                   "and validate `host` as a hostname/IP.")
    source = (
        "host = req.query.get('host', '127.0.0.1')\n"
        'cmd = f"ping -c1 -W1 {host}"          # user input → shell string\n'
        "out = subprocess.run(cmd, shell=True, capture_output=True, timeout=15).stdout"
    )

    def handle(self, req: Request, db) -> Response:
        host = req.query.get("host", "127.0.0.1")
        # Hand the shell a clean env: keep the OS environment but drop any other
        # level's DEADWOOD_* flag (The Cipher seeds DEADWOOD_CIPHER into os.environ),
        # so command injection here can't shortcut a sibling room. This level's own
        # flag is the only DEADWOOD_* the shell should ever see.
        env = {k: v for k, v in os.environ.items() if not k.startswith("DEADWOOD_")}
        env["DEADWOOD_FLAG"] = self.flag()
        try:
            out = subprocess.run(f"ping -c1 -W1 {host}", shell=True, capture_output=True,
                                 timeout=15, env=env).stdout.decode("utf-8", "replace")
        except Exception as exc:
            out = f"error: {exc}"
        body = f"""
        <h1>Deadwood Trust — Network Diagnostics</h1>
        <p class="dim">Ping a host to check the line.</p>
        <form method="get" action="/l/back-door/app">
          <input name="host" value="{html.escape(host)}" size="44"> <button>ping</button>
        </form>
        <pre>{html.escape(out)}</pre>
        <p class="dim" style="margin-top:18px"><a href="/l/back-door">&larr; back to the briefing</a></p>
        """
        return Response(ui.shell("Back Door — Network Diagnostics", body))
