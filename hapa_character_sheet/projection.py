from __future__ import annotations

import copy
import html
import json
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
DATA_JSON = OUTPUTS / "hapa-character-sheet-data.json"
PROTOTYPE_HTML = OUTPUTS / "hapa-character-sheet-prototype.html"
REFRESH_LOG = OUTPUTS / "hapa-character-sheet.refresh-log.ndjson"
REFRESH_PROTOCOL = OUTPUTS / "HAPA_CHARACTER_SHEET_REFRESH_PROTOCOL.md"
EXPORTS = OUTPUTS / "exports"
BUILDER = ROOT / "work" / "build_character_sheet_projection.py"
SCHEMA_VERSION = "hapa-character-sheet-runtime/0.1.0"
VISIBILITY_LEVELS = {"public", "trusted", "agent", "owner"}
RANK_ORDER = {"D": 0, "C": 1, "B": 2, "A": 3, "S": 4, "SS": 5}
BACKTICK_LOCAL_PATH_RE = re.compile(r"`[^`]*?/Users/[^`]*`")
LOCAL_PATH_RE = re.compile(r"(?:file://)?/Users/[^\s`\"'<>),]+")


def load_projection(path: Path = DATA_JSON) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_from_api(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def load_from_sqlite(_: str | None = None) -> dict[str, Any]:
    """Direct SQLite mode is materialized by the checked-in projection builder."""
    refresh_projection(dry_run=False)
    return load_projection()


def load_character_sheet(mode: str = "file", source: str | None = None) -> dict[str, Any]:
    if mode == "file":
        return load_projection(Path(source) if source else DATA_JSON)
    if mode == "api":
        return load_from_api(source or "http://127.0.0.1:8794/v1/character-sheets/calder")
    if mode == "sqlite":
        return load_from_sqlite(source)
    raise ValueError(f"unsupported adapter mode: {mode}")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _refresh_run_id() -> str:
    return "hcs-refresh-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def append_refresh_event(event: dict[str, Any]) -> None:
    REFRESH_LOG.parent.mkdir(parents=True, exist_ok=True)
    with REFRESH_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=True, separators=(",", ":")) + "\n")


def refresh_summary() -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    if REFRESH_LOG.exists():
        for line in REFRESH_LOG.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
            except ValueError:
                continue
            payload = raw.get("payload") or {}
            events.append(
                {
                    "id": raw.get("id"),
                    "ts": raw.get("ts"),
                    "actor": raw.get("actor"),
                    "type": raw.get("type"),
                    "run_id": raw.get("run_id") or payload.get("run_id"),
                    "status": payload.get("status") or raw.get("status"),
                    "trigger": payload.get("trigger"),
                    "source": payload.get("source"),
                    "summary": payload.get("summary") or {},
                    "validation": payload.get("validation") or [],
                }
            )
    last_event = events[-1] if events else {}
    last_success = next((event for event in reversed(events) if event.get("status") == "success" or event.get("type") == "refresh_completed"), {})
    return {
        "protocol_id": "hapa-character-sheet-refresh-protocol",
        "protocol_doc": str(REFRESH_PROTOCOL),
        "log_path": str(REFRESH_LOG),
        "last_event": last_event,
        "last_success": last_success,
        "event_count": len(events),
        "events": events[-20:],
    }


def _builder_result() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(BUILDER)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def refresh_projection(dry_run: bool = True) -> dict[str, Any]:
    run_id = _refresh_run_id()
    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "run_id": run_id,
            "would_run": [sys.executable, str(BUILDER)],
            "source": str(BUILDER),
            "would_record": str(REFRESH_LOG),
            "protocol_doc": str(REFRESH_PROTOCOL),
            "current_refresh": refresh_summary(),
        }
    started_at = _utc_now()
    append_refresh_event(
        {
            "id": f"{run_id}:started",
            "ts": started_at,
            "actor": "hapa-character-sheet-cli",
            "type": "refresh_started",
            "run_id": run_id,
            "payload": {
                "run_id": run_id,
                "status": "started",
                "trigger": "cli refresh --from-second-brain",
                "source": str(BUILDER),
                "protocol_doc": str(REFRESH_PROTOCOL),
            },
        }
    )
    result = _builder_result()
    completed_at = _utc_now()
    try:
        summary = json.loads(result.stdout or "{}")
    except ValueError:
        summary = {}
    ok = result.returncode == 0
    append_refresh_event(
        {
            "id": f"{run_id}:{'completed' if ok else 'failed'}",
            "ts": completed_at,
            "actor": "hapa-character-sheet-cli",
            "type": "refresh_completed" if ok else "refresh_failed",
            "run_id": run_id,
            "payload": {
                "run_id": run_id,
                "status": "success" if ok else "failed",
                "trigger": "cli refresh --from-second-brain",
                "source": str(BUILDER),
                "summary": summary,
                "validation": ["builder_returncode_0"] if ok else ["builder_failed"],
                "stderr": result.stderr.strip()[:2000],
            },
        }
    )
    reproject_result = _builder_result() if ok else None
    return {
        "ok": ok and (reproject_result is None or reproject_result.returncode == 0),
        "run_id": run_id,
        "started_at": started_at,
        "last_refresh_at": completed_at if ok else "",
        "returncode": result.returncode,
        "reproject_returncode": reproject_result.returncode if reproject_result else None,
        "summary": summary,
        "refresh": refresh_summary(),
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def _redact_value(key: str, value: Any, visibility: str) -> Any:
    if visibility == "owner":
        return value
    if isinstance(value, str):
        if visibility in {"public", "agent"} and "/Users/" in value:
            value = BACKTICK_LOCAL_PATH_RE.sub("`[redacted-local-path]`", value)
            value = LOCAL_PATH_RE.sub("[redacted-local-path]", value)
        localish = value.startswith("/Users/") or "file:///Users/" in value
        path_key = key.endswith("_path") or key in {"source_path", "preview_path", "output_local_path", "href"}
        if localish and (visibility in {"public", "agent"} or path_key):
            return "[redacted-local-path]"
    return value


def _walk_redact(value: Any, visibility: str, key: str = "") -> Any:
    if isinstance(value, dict):
        return {k: _walk_redact(v, visibility, k) for k, v in value.items()}
    if isinstance(value, list):
        return [_walk_redact(item, visibility, key) for item in value]
    return _redact_value(key, value, visibility)


def apply_visibility(data: dict[str, Any], visibility: str = "owner") -> dict[str, Any]:
    if visibility not in VISIBILITY_LEVELS:
        raise ValueError(f"visibility must be one of {sorted(VISIBILITY_LEVELS)}")
    projected = copy.deepcopy(data)
    if visibility == "public":
        for key, limit in {"turns": 120, "learning_links": 240, "topics": 240}.items():
            if isinstance(projected.get(key), list) and len(projected[key]) > limit:
                projected[key] = projected[key][:limit]
        projected.pop("source_database", None)
    elif visibility == "agent":
        projected.pop("source_database", None)
    projected = _walk_redact(projected, visibility)
    projected["redaction_manifest"] = {
        "schema_version": SCHEMA_VERSION,
        "visibility": visibility,
        "public_raw_history_limited": visibility == "public",
        "local_paths_redacted": visibility in {"public", "agent"},
        "owner_mode_available": True,
    }
    return projected


def health(deep: bool = False) -> dict[str, Any]:
    data_exists = DATA_JSON.exists()
    html_exists = PROTOTYPE_HTML.exists()
    response: dict[str, Any] = {
        "ok": data_exists and html_exists,
        "schema_version": SCHEMA_VERSION,
        "data_path": str(DATA_JSON),
        "prototype_path": str(PROTOTYPE_HTML),
        "data_exists": data_exists,
        "prototype_exists": html_exists,
    }
    if deep and data_exists:
        data = load_projection()
        response["summary"] = data.get("summary", {})
        response["projection_notes"] = data.get("projection_notes", [])
        response["board_counts"] = data.get("board", {}).get("counts", {})
        response["refresh"] = data.get("refresh", refresh_summary())
    return response


def capabilities() -> dict[str, Any]:
    data = load_projection()
    return {
        "ok": True,
        "schema_version": SCHEMA_VERSION,
        "source_counts": data.get("summary", {}),
        "surfaces": {
            "ui": [
                "data-view",
                "presentation-hero",
                "presentation-character-model",
                "presentation-codex",
                "presentation-skill-loop-preview",
                "presentation-skill-quality-matrix",
                "presentation-proof",
                "presentation-loadout",
                "presentation-timeline",
                "presentation-passport",
                "refresh-protocol",
            ],
            "api": [
                "/health",
                "/capabilities",
                "/v1/character-sheets/{id}",
                "/v1/character-sheets/{id}/resume",
                "/v1/character-sheets/{id}/stats",
                "/v1/character-sheets/{id}/skills",
                "/v1/character-sheets/{id}/skills/{skill_id}/evidence",
                "/v1/character-sheets/{id}/portfolio",
                "/v1/character-sheets/{id}/lineage",
                "/v1/character-sheets/{id}/timeline",
                "/v1/character-sheets/{id}/skill-quality",
                "/v1/character-sheets/{id}/agent-dossier",
                "/v1/character-sheets/{id}/refresh",
            ],
            "cli": [
                "health",
                "capabilities",
                "sheet",
                "resume",
                "stats",
                "skills",
                "skill",
                "lineage",
                "timeline",
                "skill-quality",
                "portfolio",
                "agent-dossier",
                "refresh",
                "export",
                "kanban",
                "smoke",
                "serve",
            ],
        },
    }


def list_sheets(visibility: str = "public") -> dict[str, Any]:
    data = apply_visibility(load_projection(), visibility)
    profile = data.get("profile", {})
    return {
        "ok": True,
        "sheets": [
            {
                "id": "calder",
                "name": profile.get("name"),
                "title": profile.get("title"),
                "summary": profile.get("resume_summary") or profile.get("summary"),
                "visibility": visibility,
            }
        ],
    }


def sheet(visibility: str = "owner") -> dict[str, Any]:
    return apply_visibility(load_projection(), visibility)


def resume_projection(visibility: str = "public") -> dict[str, Any]:
    data = apply_visibility(load_projection(), visibility)
    return {
        "ok": True,
        "profile": data.get("profile", {}),
        "resume": data.get("resume", {}),
        "stats": data.get("stats", []),
        "top_skills": data.get("skills", [])[:16],
        "featured_nodes": data.get("nodes", [])[:12],
        "redaction_manifest": data.get("redaction_manifest", {}),
    }


def resume_markdown(visibility: str = "public") -> str:
    payload = resume_projection(visibility)
    profile = payload["profile"]
    lines = [
        f"# {profile.get('name', 'Hapa Character Sheet')}",
        "",
        f"**{profile.get('title', '')}**",
        "",
        profile.get("resume_summary") or profile.get("summary", ""),
        "",
        "## Outcomes",
    ]
    for outcome in payload["resume"].get("outcomes", []):
        lines.extend([f"- **{outcome.get('title')}** ({outcome.get('meta')}): {outcome.get('body')}"])
    lines.extend(["", "## Skills"])
    for skill in payload["top_skills"][:12]:
        lines.append(f"- {skill.get('label')} - {skill.get('rank')} {skill.get('level')} ({skill.get('evidence_count')} evidence)")
    lines.extend(["", "## Proof Lanes"])
    for lane in payload["resume"].get("proof_lanes", []):
        lines.append(f"- **{lane.get('label')}**: {lane.get('body')} {'; '.join(lane.get('metrics', []))}")
    lines.extend(["", f"_Visibility: {visibility}. Generated from Hapa Character Sheet projection._"])
    return "\n".join(lines)


def stats(explain: bool = True, visibility: str = "public") -> dict[str, Any]:
    data = apply_visibility(load_projection(), visibility)
    return {
        "ok": True,
        "formula_version": "hcs-stat-engine/2026-06-01",
        "formula": "Evidence volume + source diversity + linked result/node proof + confidence mapped to 0-99 and D/C/B/A/S/SS bands.",
        "stats": data.get("stats", []) if explain else [{k: v for k, v in stat.items() if k in {"label", "value"}} for stat in data.get("stats", [])],
    }


def skills(family: str | None = None, min_rank: str | None = None, limit: int = 50, visibility: str = "public") -> dict[str, Any]:
    data = apply_visibility(load_projection(), visibility)
    rows = data.get("skills", [])
    if family:
        rows = [item for item in rows if item.get("skill_family") == family or family.lower() in item.get("label", "").lower()]
    if min_rank:
        floor = RANK_ORDER.get(min_rank.upper(), 0)
        rows = [item for item in rows if RANK_ORDER.get(item.get("rank"), 0) >= floor]
    return {"ok": True, "skills": rows[:limit], "count": len(rows), "visibility": visibility}


def skill_evidence(skill_id: str, limit: int = 30, visibility: str = "agent") -> dict[str, Any]:
    data = apply_visibility(load_projection(), visibility)
    needle = skill_id.lower()
    skill = next(
        (
            item
            for item in data.get("skills", [])
            if item.get("skill_id") == skill_id or needle in item.get("label", "").lower()
        ),
        {},
    )
    label = skill.get("label", skill_id)
    learning = [item for item in data.get("learning_links", []) if item.get("skill_label") == label][:limit]
    caps = [item for item in data.get("capabilities", []) if label in item.get("connected_skills", [])][:limit]
    nodes = [item for item in data.get("nodes", []) if label.lower() in item.get("description", "").lower()][:limit]
    return {"ok": True, "skill": skill, "learning_links": learning, "capabilities": caps, "nodes": nodes, "visibility": visibility}


def portfolio(pinned: bool = False, visibility: str = "public") -> dict[str, Any]:
    data = apply_visibility(load_projection(), visibility)
    nodes = data.get("nodes", [])[:24 if pinned else 80]
    media = data.get("media", [])[:24 if pinned else 80]
    return {
        "ok": True,
        "outcomes": data.get("resume", {}).get("outcomes", []),
        "nodes": nodes,
        "media": media,
        "character_models": data.get("character_models", {}),
        "skill_video_loops": data.get("skill_video_loops", {}),
        "refresh": data.get("refresh", {}),
        "image_sources": (data.get("image_sources", {}).get("items") or [])[:24],
        "visibility": visibility,
    }


def lineage(skill: str | None = None, limit: int = 50, visibility: str = "agent") -> dict[str, Any]:
    data = apply_visibility(load_projection(), visibility)
    rows = data.get("learning_links", [])
    if skill:
        skill_lower = skill.lower()
        rows = [
            item
            for item in rows
            if skill_lower in item.get("skill_label", "").lower()
            or skill_lower in item.get("evidence_text", "").lower()
        ]
    return {
        "ok": True,
        "lineage": rows[:limit],
        "turns": data.get("turns", [])[: min(limit, 50)],
        "capabilities": data.get("capabilities", [])[: min(limit, 50)],
        "visibility": visibility,
    }


def timeline(
    layer: str | None = None,
    since: str | None = None,
    limit: int = 80,
    beat_id: str | None = None,
    scale: str = "month",
    visibility: str = "public",
) -> dict[str, Any]:
    data = apply_visibility(load_projection(), visibility)
    timeline_data = data.get("timeline", {})
    scale = "day" if scale == "daily" else scale
    if scale not in {"day", "week", "month", "year"}:
        scale = "month"
    beats = timeline_data.get("beats", [])
    if layer and layer != "all":
        beats = [item for item in beats if item.get("layer") == layer]
    if since:
        beats = [item for item in beats if str(item.get("date", "")) >= since]
    selected = None
    if beat_id:
        selected = next((item for item in timeline_data.get("beats", []) if item.get("id") == beat_id), None)
    series_limit = min(max(limit, 24), 160)
    series = (timeline_data.get("series_by_scale") or {}).get(scale) or timeline_data.get("series", [])
    if layer and layer != "all":
        series = [item for item in series if item.get("layer") == layer]
    if since:
        series = [item for item in series if str(item.get("bucket", "")) >= since[: len(str(item.get("bucket", "")))]]
    return {
        "ok": True,
        "scale": scale,
        "summary": timeline_data.get("summary", {}),
        "daily_summary": timeline_data.get("daily_summary", {}),
        "eras": timeline_data.get("eras", []),
        "layers": timeline_data.get("layers", []),
        "series": series[-series_limit:],
        "beats": beats[:limit],
        "selected": selected,
        "source_mix": timeline_data.get("source_mix", [])[:24],
        "visibility": visibility,
    }


def skill_quality(
    avatar: str | None = None,
    skill: str | None = None,
    family: str | None = None,
    limit: int = 80,
    visibility: str = "public",
) -> dict[str, Any]:
    data = apply_visibility(load_projection(), visibility)
    quality = data.get("skill_quality", {})
    skill_rows = quality.get("skill_quality", [])
    pair_rows = quality.get("avatar_skill_experience", [])

    if family:
        family_lower = family.lower()
        skill_rows = [
            item
            for item in skill_rows
            if family_lower in item.get("skill_family", "").lower()
            or family_lower in item.get("label", "").lower()
        ]
        pair_rows = [
            item
            for item in pair_rows
            if family_lower in item.get("skill_family", "").lower()
            or family_lower in item.get("skill_label", "").lower()
        ]
    if skill:
        skill_lower = skill.lower()
        skill_rows = [
            item
            for item in skill_rows
            if skill_lower == item.get("skill_id", "").lower()
            or skill_lower in item.get("label", "").lower()
        ]
        pair_rows = [
            item
            for item in pair_rows
            if skill_lower == item.get("skill_id", "").lower()
            or skill_lower in item.get("skill_label", "").lower()
        ]
    if avatar:
        avatar_lower = avatar.lower()
        pair_rows = [
            item
            for item in pair_rows
            if avatar_lower == item.get("avatar_id", "").lower()
            or avatar_lower in item.get("avatar_label", "").lower()
        ]
    limit = max(1, min(int(limit or 80), 600))
    return {
        "ok": True,
        "summary": quality.get("summary", {}),
        "formula_version": quality.get("formula_version", ""),
        "method": quality.get("method", {}),
        "family_summary": quality.get("family_summary", [])[: min(limit, 80)],
        "avatars": quality.get("avatar_profiles", [])[: min(limit, 80)],
        "skill_quality": skill_rows[:limit],
        "avatar_skill_experience": pair_rows[:limit],
        "visibility": visibility,
    }


def agent_dossier(visibility: str = "agent") -> dict[str, Any]:
    data = apply_visibility(load_projection(), visibility)
    quality = data.get("skill_quality", {})
    return {
        "ok": True,
        "profile": data.get("profile", {}),
        "capabilities": data.get("capabilities", [])[:60],
        "skills": data.get("skills", [])[:60],
        "agents": data.get("agents", []),
        "harnesses": data.get("harnesses", []),
        "character_models": data.get("character_models", {}),
        "skill_video_loops": data.get("skill_video_loops", {}),
        "skill_quality": {
            "summary": quality.get("summary", {}),
            "top_skills": quality.get("skill_quality", [])[:20],
            "top_avatar_skill_pairs": quality.get("top_pairs", [])[:20],
            "method": quality.get("method", {}),
        },
        "refresh": data.get("refresh", {}),
        "protocols": data.get("protocols", [])[:30],
        "board": data.get("board", {}),
        "redaction_manifest": data.get("redaction_manifest", {}),
    }


def kanban_state() -> dict[str, Any]:
    data = load_projection()
    return {"ok": True, "board": data.get("board", {})}


def export_payload(format_name: str = "json", visibility: str = "public") -> tuple[str, str]:
    if format_name == "markdown":
        return "text/markdown", resume_markdown(visibility)
    if format_name == "html":
        resume = resume_projection(visibility)
        body = html.escape(resume["profile"].get("resume_summary") or "")
        items = "".join(f"<li><strong>{html.escape(s.get('label',''))}</strong> {html.escape(str(s.get('rank','')))}</li>" for s in resume["top_skills"][:16])
        output = f"<!doctype html><html><head><meta charset='utf-8'><title>Hapa Character Sheet Resume</title></head><body><h1>{html.escape(resume['profile'].get('name',''))}</h1><p>{body}</p><h2>Skills</h2><ul>{items}</ul></body></html>"
        return "text/html", output
    return "application/json", json.dumps(resume_projection(visibility), indent=2)


def write_export(format_name: str = "json", visibility: str = "public", out: str | None = None) -> dict[str, Any]:
    EXPORTS.mkdir(parents=True, exist_ok=True)
    _, content = export_payload(format_name, visibility)
    suffix = {"markdown": "md", "html": "html", "json": "json"}.get(format_name, "json")
    path = Path(out) if out else EXPORTS / f"hapa-character-sheet-resume-{visibility}.{suffix}"
    path.write_text(content, encoding="utf-8")

    def manifest_path_value(item: Path) -> str:
        if visibility == "owner":
            return str(item)
        try:
            return str(item.relative_to(ROOT))
        except ValueError:
            return item.name

    manifest = {
        "ok": True,
        "path": manifest_path_value(path),
        "format": format_name,
        "visibility": visibility,
        "provenance": manifest_path_value(DATA_JSON),
        "redaction": apply_visibility(load_projection(), visibility).get("redaction_manifest", {}),
    }
    manifest_path = path.with_suffix(path.suffix + ".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    manifest["manifest_path"] = manifest_path_value(manifest_path)
    return manifest


def smoke_report(dry_run: bool = True) -> dict[str, Any]:
    steps = [
        ("health", health(deep=True).get("ok")),
        ("capabilities", capabilities().get("ok")),
        ("resume", bool(resume_projection("public").get("resume"))),
        ("stats", bool(stats().get("stats"))),
        ("timeline", bool(timeline(limit=5).get("beats"))),
        ("skill_quality", bool(skill_quality(limit=5).get("skill_quality"))),
        ("kanban", bool(kanban_state().get("board", {}).get("tasks"))),
        ("refresh_dry_run", refresh_projection(dry_run=True).get("ok")),
    ]
    return {
        "ok": all(result for _, result in steps),
        "dry_run": dry_run,
        "schema_version": SCHEMA_VERSION,
        "step_results": [{"step": step, "ok": bool(result)} for step, result in steps],
    }
