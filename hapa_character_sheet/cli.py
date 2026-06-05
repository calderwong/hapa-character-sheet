from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from . import projection


def emit(value: Any, as_text: bool = False) -> None:
    if as_text:
        print(str(value))
    else:
        print(json.dumps(value, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hapa-character-sheet")
    sub = parser.add_subparsers(dest="command", required=True)

    health = sub.add_parser("health")
    health.add_argument("--deep", action="store_true")

    sub.add_parser("capabilities")

    serve = sub.add_parser("serve")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8794)

    sheet = sub.add_parser("sheet")
    sheet.add_argument("sheet_id", nargs="?", default="calder")
    sheet.add_argument("--visibility", default="owner", choices=sorted(projection.VISIBILITY_LEVELS))
    sheet.add_argument("--format", default="json", choices=["json"])

    resume = sub.add_parser("resume")
    resume.add_argument("sheet_id", nargs="?", default="calder")
    resume.add_argument("--visibility", default="public", choices=sorted(projection.VISIBILITY_LEVELS))
    resume.add_argument("--format", default="json", choices=["json", "markdown"])

    stats = sub.add_parser("stats")
    stats.add_argument("sheet_id", nargs="?", default="calder")
    stats.add_argument("--visibility", default="public", choices=sorted(projection.VISIBILITY_LEVELS))
    stats.add_argument("--explain", action="store_true", default=True)
    stats.add_argument("--compact", action="store_true")

    skills = sub.add_parser("skills")
    skills.add_argument("sheet_id", nargs="?", default="calder")
    skills.add_argument("--visibility", default="public", choices=sorted(projection.VISIBILITY_LEVELS))
    skills.add_argument("--family")
    skills.add_argument("--min-rank")
    skills.add_argument("--limit", type=int, default=50)

    skill = sub.add_parser("skill")
    skill.add_argument("sheet_id", nargs="?", default="calder")
    skill.add_argument("skill_id")
    skill.add_argument("--visibility", default="agent", choices=sorted(projection.VISIBILITY_LEVELS))
    skill.add_argument("--evidence", action="store_true")
    skill.add_argument("--limit", type=int, default=30)

    lineage = sub.add_parser("lineage")
    lineage.add_argument("sheet_id", nargs="?", default="calder")
    lineage.add_argument("--visibility", default="agent", choices=sorted(projection.VISIBILITY_LEVELS))
    lineage.add_argument("--skill")
    lineage.add_argument("--limit", type=int, default=50)

    timeline = sub.add_parser("timeline")
    timeline.add_argument("sheet_id", nargs="?", default="calder")
    timeline.add_argument("--visibility", default="public", choices=sorted(projection.VISIBILITY_LEVELS))
    timeline.add_argument("--scale", default="month")
    timeline.add_argument("--layer")
    timeline.add_argument("--since")
    timeline.add_argument("--limit", type=int, default=80)
    timeline.add_argument("--beat")
    timeline.add_argument("--lore", action="store_true")
    timeline.add_argument("--proof", action="store_true")

    skill_quality = sub.add_parser("skill-quality")
    skill_quality.add_argument("sheet_id", nargs="?", default="calder")
    skill_quality.add_argument("--visibility", default="public", choices=sorted(projection.VISIBILITY_LEVELS))
    skill_quality.add_argument("--avatar")
    skill_quality.add_argument("--skill")
    skill_quality.add_argument("--family")
    skill_quality.add_argument("--limit", type=int, default=80)

    portfolio = sub.add_parser("portfolio")
    portfolio.add_argument("sheet_id", nargs="?", default="calder")
    portfolio.add_argument("--visibility", default="public", choices=sorted(projection.VISIBILITY_LEVELS))
    portfolio.add_argument("--pinned", action="store_true")

    dossier = sub.add_parser("agent-dossier")
    dossier.add_argument("sheet_id", nargs="?", default="calder")
    dossier.add_argument("--visibility", default="agent", choices=sorted(projection.VISIBILITY_LEVELS))

    refresh = sub.add_parser("refresh")
    refresh.add_argument("sheet_id", nargs="?", default="calder")
    refresh.add_argument("--from-second-brain", action="store_true")
    refresh.add_argument("--dry-run", action="store_true")

    export = sub.add_parser("export")
    export.add_argument("sheet_id", nargs="?", default="calder")
    export.add_argument("--visibility", default="public", choices=sorted(projection.VISIBILITY_LEVELS))
    export.add_argument("--format", default="json", choices=["json", "markdown", "html"])
    export.add_argument("--out")

    kanban = sub.add_parser("kanban")
    kanban_sub = kanban.add_subparsers(dest="kanban_command", required=True)
    kanban_sub.add_parser("state")

    smoke = sub.add_parser("smoke")
    smoke.add_argument("--dry-run", action="store_true", default=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    command = args.command

    if command == "health":
        emit(projection.health(deep=args.deep))
    elif command == "capabilities":
        emit(projection.capabilities())
    elif command == "serve":
        from .server import serve

        serve(host=args.host, port=args.port)
    elif command == "sheet":
        emit(projection.sheet(visibility=args.visibility))
    elif command == "resume":
        if args.format == "markdown":
            emit(projection.resume_markdown(args.visibility), as_text=True)
        else:
            emit(projection.resume_projection(args.visibility))
    elif command == "stats":
        emit(projection.stats(explain=not args.compact, visibility=args.visibility))
    elif command == "skills":
        emit(projection.skills(args.family, args.min_rank, args.limit, args.visibility))
    elif command == "skill":
        emit(projection.skill_evidence(args.skill_id, args.limit, args.visibility))
    elif command == "lineage":
        emit(projection.lineage(args.skill, args.limit, args.visibility))
    elif command == "timeline":
        payload = projection.timeline(args.layer, args.since, args.limit, args.beat, args.scale, args.visibility)
        payload["mode"] = "proof" if args.proof else "lore" if args.lore else "json"
        emit(payload)
    elif command == "skill-quality":
        emit(projection.skill_quality(args.avatar, args.skill, args.family, args.limit, args.visibility))
    elif command == "portfolio":
        emit(projection.portfolio(args.pinned, args.visibility))
    elif command == "agent-dossier":
        emit(projection.agent_dossier(args.visibility))
    elif command == "refresh":
        emit(projection.refresh_projection(dry_run=args.dry_run or not args.from_second_brain))
    elif command == "export":
        emit(projection.write_export(args.format, args.visibility, args.out))
    elif command == "kanban":
        emit(projection.kanban_state())
    elif command == "smoke":
        emit(projection.smoke_report(dry_run=args.dry_run))
    else:
        raise SystemExit(f"unknown command: {command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
