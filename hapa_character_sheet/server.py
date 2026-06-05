from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

from . import projection


def _first(query: dict[str, list[str]], name: str, default: str | None = None) -> str | None:
    return query.get(name, [default])[0]


class CharacterSheetHandler(BaseHTTPRequestHandler):
    server_version = "HapaCharacterSheet/0.1"

    def _json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1:8794")
        self.end_headers()
        self.wfile.write(body)

    def _text(self, body: str, content_type: str = "text/plain", status: int = 200) -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)
        visibility = _first(query, "visibility", "public") or "public"
        limit = int(_first(query, "limit", "80") or "80")

        try:
            if path == "/health":
                self._json(projection.health(deep=(_first(query, "deep", "false") == "true")))
            elif path == "/capabilities":
                self._json(projection.capabilities())
            elif path == "/v1/character-sheets":
                self._json(projection.list_sheets(visibility))
            elif path == "/v1/character-sheets/calder":
                self._json(projection.sheet(visibility))
            elif path == "/v1/character-sheets/calder/resume":
                fmt = _first(query, "format", "json")
                if fmt == "markdown":
                    self._text(projection.resume_markdown(visibility), "text/markdown")
                else:
                    self._json(projection.resume_projection(visibility))
            elif path == "/v1/character-sheets/calder/stats":
                self._json(projection.stats(visibility=visibility))
            elif path == "/v1/character-sheets/calder/skills":
                self._json(
                    projection.skills(
                        family=_first(query, "family"),
                        min_rank=_first(query, "min_rank"),
                        limit=limit,
                        visibility=visibility,
                    )
                )
            elif path.startswith("/v1/character-sheets/calder/skills/") and path.endswith("/evidence"):
                skill_id = unquote(path.split("/")[-2])
                self._json(projection.skill_evidence(skill_id, limit=limit, visibility=visibility))
            elif path == "/v1/character-sheets/calder/portfolio":
                self._json(projection.portfolio(pinned=_first(query, "pinned", "false") == "true", visibility=visibility))
            elif path == "/v1/character-sheets/calder/lineage":
                self._json(projection.lineage(skill=_first(query, "skill"), limit=limit, visibility=visibility))
            elif path == "/v1/character-sheets/calder/timeline":
                self._json(
                    projection.timeline(
                        layer=_first(query, "layer"),
                        since=_first(query, "since"),
                        limit=limit,
                        beat_id=_first(query, "beat"),
                        scale=_first(query, "scale", "month") or "month",
                        visibility=visibility,
                    )
                )
            elif path == "/v1/character-sheets/calder/skill-quality":
                self._json(
                    projection.skill_quality(
                        avatar=_first(query, "avatar"),
                        skill=_first(query, "skill"),
                        family=_first(query, "family"),
                        limit=limit,
                        visibility=visibility,
                    )
                )
            elif path == "/v1/character-sheets/calder/agent-dossier":
                self._json(projection.agent_dossier(visibility=visibility))
            elif path == "/v1/character-sheets/calder/exports":
                content_type, body = projection.export_payload(_first(query, "format", "json") or "json", visibility)
                self._text(body, content_type)
            elif path == "/kanban/state":
                self._json(projection.kanban_state())
            else:
                self._json({"ok": False, "error": "not_found", "path": path}, status=404)
        except Exception as exc:  # pragma: no cover - local diagnostic path
            self._json({"ok": False, "error": type(exc).__name__, "message": str(exc)}, status=500)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)
        try:
            if path == "/v1/character-sheets/calder/refresh":
                dry_run = _first(query, "dry_run", "false") == "true"
                self._json(projection.refresh_projection(dry_run=dry_run))
            else:
                self._json({"ok": False, "error": "not_found", "path": path}, status=404)
        except Exception as exc:  # pragma: no cover - local diagnostic path
            self._json({"ok": False, "error": type(exc).__name__, "message": str(exc)}, status=500)


def serve(host: str = "127.0.0.1", port: int = 8794) -> None:
    server = ThreadingHTTPServer((host, port), CharacterSheetHandler)
    print(f"Hapa Character Sheet API listening on http://{host}:{port}")
    print(f"Prototype: file://{projection.PROTOTYPE_HTML}#presentation-hero")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Hapa Character Sheet API")
    finally:
        server.server_close()


if __name__ == "__main__":
    serve()
