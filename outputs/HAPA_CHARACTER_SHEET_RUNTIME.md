# Hapa Character Sheet Runtime

Status: runnable local scaffold  
Updated: 2026-06-01

## Surfaces

| Surface | Entry |
| --- | --- |
| Web prototype | `outputs/hapa-character-sheet-prototype.html` |
| Presentation hero | `outputs/hapa-character-sheet-prototype.html#presentation-hero` |
| Presentation timeline | `outputs/hapa-character-sheet-prototype.html#presentation-timeline` |
| Presentation daily timeline | `outputs/hapa-character-sheet-prototype.html#presentation-timeline&scale=day` |
| Presentation profile | `outputs/hapa-character-sheet-prototype.html#presentation-profile` |
| Character model asset | `outputs/assets/calder-character-video-loop.mp4` |
| Skill loop assets | `outputs/assets/r-kick-skill.mp4`, `outputs/assets/r-run.mp4`, `outputs/assets/r-walk.mp4` |
| Profile background loops | `outputs/assets/calder-profile-dramatic-intro-01.mp4`, `outputs/assets/calder-profile-dramatic-intro-02.mp4` |
| CLI | `bin/hapa-character-sheet` |
| API | `python3 -m hapa_character_sheet.server` |
| Desktop shell | `desktop/main.js` |
| Desktop app bundle | `desktop/Hapa Character Sheet.app` |
| Workspace launcher | `desktop/Launch Hapa Character Sheet.command` |
| Desktop launcher | `/Users/calderwong/Desktop/Launch Hapa Character Sheet.command` |

## CLI Smoke

```bash
bin/hapa-character-sheet health --deep
bin/hapa-character-sheet capabilities
bin/hapa-character-sheet stats calder --compact
bin/hapa-character-sheet timeline calder --layer skills --limit 10 --lore
bin/hapa-character-sheet timeline calder --scale day --limit 10
bin/hapa-character-sheet skill-quality calder --limit 20
bin/hapa-character-sheet skill-quality calder --avatar Aruelia --limit 10
bin/hapa-character-sheet export calder --format markdown --visibility public
bin/hapa-character-sheet smoke --dry-run
```

The CLI prints JSON by default. Markdown resume export is available for human review.

The `sheet`, `portfolio`, and `agent-dossier` projections include `character_models`, currently seeded with the Calder looping MP4 and poster fallback. They also include `profile_background_videos`, currently seeded with two local dramatic-intro MP4 loops for the Persona Codex Profile hero, plus `skill_video_loops`, currently seeded with three local MP4 loops used by the Skill Codex preview stage. The `sheet`, `skill-quality`, and `agent-dossier` projections include Skill Quality and Avatar Experience ranking data with formula/version notes. The timeline projection includes `series_by_scale.day` and `daily_summary` for day-level canon inspection; the Presentation Timeline renders those buckets as both a compact rail and an x-axis-aligned stacked linechart.

## Desktop App

The desktop app uses Electron with the same generated `outputs/hapa-character-sheet-prototype.html` and starts the loopback API on `127.0.0.1:8794` only when `/health` is not already responding.

```bash
cd desktop
npm install
npm start
npm run start:profile
npm run smoke
```

Double-click launchers:

- `/Users/calderwong/Desktop/Hapa Character Sheet.app`
- `/Users/calderwong/Desktop/Launch Hapa Character Sheet.command`

The desktop shell keeps `nodeIntegration` off, `contextIsolation` on, and `sandbox` on. It includes a View menu for Presentation routes and an Outputs folder shortcut.

## Refresh Protocol

The refresh protocol is documented in `outputs/HAPA_CHARACTER_SHEET_REFRESH_PROTOCOL.md`.

```bash
bin/hapa-character-sheet refresh calder --dry-run
bin/hapa-character-sheet refresh calder --from-second-brain
bin/hapa-character-sheet health --deep | jq '.refresh.last_success'
```

Refresh events are appended to `outputs/hapa-character-sheet.refresh-log.ndjson`. The generated projection exposes the latest successful refresh at `refresh.last_success`, `summary.last_refresh_at`, and `projection_notes.last_refresh_at`.

## Character Profile Mining

The personality/lore mining protocol is documented in `outputs/HAPA_CHARACTER_PROFILE_MINING_PROTOCOL.md`, with the reusable agent prompt in `outputs/HAPA_CHARACTER_PROFILE_MINING_PROMPT.md`.

Seed artifacts:

| Artifact | Purpose |
| --- | --- |
| `outputs/HAPA_CHARACTER_PROFILE_CALDER_FOUNDATION.md` | Human-readable Calder/CJ/Hapa profile dossier. |
| `outputs/HAPA_CHARACTER_PROFILE_CALDER_SHARPENED.md` | Second-pass sharpened Calder/CJ/Hapa profile dossier. |
| `outputs/hapa-character-profile-calder-foundation.json` | Structured agent-readable profile. |
| `outputs/hapa-character-profile-calder-runs.json` | Two-run profile record: foundation fill plus sharpened pass. |
| `outputs/hapa-character-profile.observations.ndjson` | Append-only observation ledger. |
| `outputs/hapa-character-profile.schema.json` | JSON schema for generated dossiers. |
| `outputs/hapa-character-profile-mining-flow.json` | Node Space profile-mining sidecar. |

Validation:

```bash
jq empty outputs/hapa-character-profile.schema.json outputs/hapa-character-profile-calder-foundation.json outputs/hapa-character-profile-calder-runs.json outputs/hapa-character-profile-mining-flow.json
python3 - <<'PY'
import json, pathlib
for line in pathlib.Path('outputs/hapa-character-profile.observations.ndjson').read_text().splitlines():
    if line.strip():
        json.loads(line)
print('character profile observation ledger ok')
PY
```

## API Smoke

```bash
bin/hapa-character-sheet serve --host 127.0.0.1 --port 8794
curl http://127.0.0.1:8794/health
curl http://127.0.0.1:8794/v1/character-sheets/calder/timeline?layer=skills
curl http://127.0.0.1:8794/v1/character-sheets/calder/timeline?scale=day
curl http://127.0.0.1:8794/v1/character-sheets/calder/skill-quality?limit=10
curl -X POST 'http://127.0.0.1:8794/v1/character-sheets/calder/refresh?dry_run=true'
```

The API is a stdlib loopback server over the same projection functions as the CLI.

## Adapter Modes

| Mode | Behavior |
| --- | --- |
| `file` | Reads `outputs/hapa-character-sheet-data.json`. |
| `sqlite` | Runs `work/build_character_sheet_projection.py`, which reads the Second Brain SQLite database directly and regenerates projection artifacts. |
| `api` | Reads an already-running Character Sheet API endpoint. |

## Redaction

Visibility tiers:

| Tier | Behavior |
| --- | --- |
| `public` | Limits raw turn/topic/link arrays and redacts local absolute paths. |
| `trusted` | Keeps projection shape and attaches a redaction manifest. |
| `agent` | Keeps structured capability context while redacting local absolute paths. |
| `owner` | Preserves full local projection. |

Exports write a sidecar manifest with visibility, provenance, and redaction metadata.
