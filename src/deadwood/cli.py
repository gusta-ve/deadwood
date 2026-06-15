"""deadwood command line — run the range, browse and learn the levels, grade flags."""

from __future__ import annotations

import argparse
import sys

import deadwood.levels  # noqa: F401  (importing registers every level)
from deadwood import __version__, flags, progress, server
from deadwood.level import all_levels, by_slug

_BANNER = r"""
   ___              _                 _
  / _ \___ __ _  __| |_      _____   (_)__/ /
 / // / -_) _` |/ _` \ \ /\ / / _ \ / / _  /
/____/\__/\__,_|\__,_/\_\/\_/\___//_/\_,_/   a vulnerable range · tutorial → impossible
"""


def _print_banner():
    print(_BANNER.rstrip("\n"))
    print(f"  v{__version__} · the practice town for wraith & hickok\n")


def cmd_serve(args):
    _print_banner()
    sv = progress.solved()
    print(f"  map      http://{args.host}:{args.port}/")
    print(f"  levels   {len(all_levels())} loaded · {len(sv)} taken")
    print(f"  warning  intentionally vulnerable — keep it on localhost, never expose it")
    print("\n  Ctrl-C to stop the range.\n")
    try:
        server.serve(args.host, args.port, allow_unsafe=args.unsafe)
    except PermissionError as exc:
        print(f"  [-] {exc}", file=sys.stderr)
        raise SystemExit(2)
    except OSError as exc:
        print(f"  [-] cannot bind {args.host}:{args.port} — {exc}", file=sys.stderr)
        raise SystemExit(2)
    except KeyboardInterrupt:
        print("\n  range closed.")


def cmd_levels(args):
    sv = progress.solved()
    print()
    for lv in all_levels():
        mark = "✓" if lv.slug in sv else " "
        print(f"  [{mark}] {lv.num:02d}  {lv.title:<18} {lv.tier:<11} {lv.category}")
        print(f"         {lv.slug:<18} {lv.brief}")
    print(f"\n  {len(sv)}/{len(all_levels())} taken · learn a level with `deadwood learn <slug>`\n")


def cmd_learn(args):
    lv = by_slug(args.slug)
    if lv is None:
        print(f"  no level '{args.slug}'. see `deadwood levels`.", file=sys.stderr)
        raise SystemExit(2)
    bar = "─" * 60
    print(f"\n  {lv.num:02d} · {lv.title}   [{lv.tier}]  {lv.category}\n  {bar}")
    print(f"  objective\n    {lv.objective}\n")
    print("  hints")
    for i, h in enumerate(lv.hints, 1):
        print(f"    {i}. {h}")
    print(f"\n  the vulnerable source\n{_indent(lv.source)}")
    print(f"\n  how to fix it\n    {lv.remediation}")
    print(f"\n  capture the flag, then:  deadwood flag {lv.slug} 'DEADWOOD{{...}}'\n")


def _indent(text, pad="    | "):
    return "\n".join(pad + ln for ln in text.splitlines())


def cmd_flag(args):
    lv = by_slug(args.slug)
    if lv is None:
        print(f"  no level '{args.slug}'.", file=sys.stderr)
        raise SystemExit(2)
    if flags.check(lv.slug, args.value):
        progress.mark(lv.slug)
        print(f"  ✓ {lv.title} — taken. that's the hand.")
    else:
        print("  ✗ not it. keep working the room.")
        raise SystemExit(1)


def cmd_reset(args):
    progress.reset()
    print("  progress reset — every room is open again.")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="deadwood",
                                description="A self-hosted, leveled web-security range "
                                            "(tutorial → impossible). Intentionally vulnerable; "
                                            "runs on localhost only.")
    p.add_argument("--version", action="version", version=f"deadwood {__version__}")
    sub = p.add_subparsers(dest="command", metavar="<command>")

    s = sub.add_parser("serve", help="run the range")
    s.add_argument("-H", "--host", default="127.0.0.1", help="bind host (default: 127.0.0.1)")
    s.add_argument("-p", "--port", type=int, default=8666, help="bind port (default: 8666)")
    s.add_argument("--unsafe", action="store_true",
                   help="allow binding a non-loopback host (dangerous — it's vulnerable)")
    s.set_defaults(func=cmd_serve)

    ls = sub.add_parser("levels", help="list the levels and your progress")
    ls.set_defaults(func=cmd_levels)

    lr = sub.add_parser("learn", help="the briefing for a level (objective, hints, source, fix)")
    lr.add_argument("slug")
    lr.set_defaults(func=cmd_learn)

    fl = sub.add_parser("flag", help="submit a captured flag")
    fl.add_argument("slug")
    fl.add_argument("value")
    fl.set_defaults(func=cmd_flag)

    rs = sub.add_parser("reset", help="clear your captured-flag progress")
    rs.set_defaults(func=cmd_reset)
    return p


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    args = build_parser().parse_args(argv)
    if not getattr(args, "func", None):
        _print_banner()
        print("  deadwood serve            run the range (http://127.0.0.1:8666)")
        print("  deadwood levels           list the levels")
        print("  deadwood learn <slug>     a level's briefing + how to fix it")
        print("  deadwood flag <slug> ...  submit a captured flag\n")
        return
    args.func(args)


if __name__ == "__main__":
    main()
