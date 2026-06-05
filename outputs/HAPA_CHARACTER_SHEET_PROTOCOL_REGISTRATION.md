# Hapa Character Sheet Protocol Registration

Status: registered locally for review  
Updated: 2026-06-01

## Registered Artifacts

| Artifact | Role |
| --- | --- |
| `hapa-character-sheet.manifest.json` | Hapa node manifest and surface declaration |
| `hapa-character-sheet.openapi.json` | API contract |
| `hapa-character-sheet.protocol-flow.json` | Node Space / process-flow sidecar |
| `hapa-character-sheet.board.config.json` | Overwatch Kanban config |
| `hapa-character-sheet.board.events.ndjson` | Append-only board event log |
| `HAPA_CHARACTER_SHEET_NODE_SPEC.md` | Product and protocol spec |
| `HAPA_CHARACTER_SHEET_RUNTIME.md` | CLI/API/export/desktop runtime docs |
| `HAPA_CHARACTER_SHEET_REFRESH_PROTOCOL.md` | Character data refresh runbook and record rule |
| `hapa-character-sheet.refresh-flow.json` | Node Space refresh flow sidecar |
| `hapa-character-sheet.refresh-log.ndjson` | Append-only last-refresh ledger |
| `HAPA_CHARACTER_SHEET_SKILL_RANKING_PROTOCOL.md` | Skill Quality and Avatar Experience reassessment protocol |
| `hapa-character-sheet.skill-ranking-flow.json` | Node Space ranking flow sidecar |

## Quest Keeper Discovery

Project id:

```text
hapa-app-hapa-character-sheet
```

Node id:

```text
hapa-character-sheet
```

Local board:

```text
outputs/hapa-character-sheet.board.events.ndjson
```

Refresh ledger:

```text
outputs/hapa-character-sheet.refresh-log.ndjson
outputs/hapa-character-sheet.skill-ranking-flow.json
```

## Review Gate

Human acceptance is represented by the current thread direction: build the Timeline View and drain the board. Public publishing still requires an owner visibility review before external distribution.
