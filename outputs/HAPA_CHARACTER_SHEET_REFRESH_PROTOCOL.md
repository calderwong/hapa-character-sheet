# Hapa Character Sheet Refresh Protocol

Status: active local protocol  
Protocol id: `hapa-character-sheet-refresh-protocol`  
Owner: Calder/CJ local Hapa workspace  
Last updated: 2026-06-03

## Purpose

Refresh the Hapa Character Sheet from Hapa Second Brain source truth, rebuild the professional/RPG projection, and record when the refresh happened so future humans and agents can trust the displayed skills, metrics, nodes, media, timeline, and portfolio counts.

This protocol keeps Second Brain as the source of memory and Character Sheet as a read-only, presentation-ready projection.

## Source Truth

| Layer | Owner | Refresh behavior |
| --- | --- | --- |
| Hapa Second Brain DB | Second Brain | Read only. Supplies content items, exposures, skills, evidence, turns, nodes, capabilities, media, agents, timeline, and protocols. |
| Character Sheet projection | Character Sheet | Rebuilt from `work/build_character_sheet_projection.py`. Writes `hapa-character-sheet-data.json`, `hapa-character-sheet-data.js`, and the static prototype. |
| Refresh ledger | Character Sheet | Append only. Writes `outputs/hapa-character-sheet.refresh-log.ndjson`. |
| Board events | Overwatch Kanban | Append only. Record protocol or implementation changes, not every ordinary data refresh unless review-worthy. |
| Public exports | Character Sheet | Regenerate only after owner visibility review. |

## Fast Path

From the Character Sheet workspace:

```bash
bin/hapa-character-sheet refresh calder --dry-run
bin/hapa-character-sheet refresh calder --from-second-brain
bin/hapa-character-sheet health --deep
bin/hapa-character-sheet skill-quality calder --limit 20
bin/hapa-character-sheet smoke --dry-run
```

The real refresh appends `refresh_started` and `refresh_completed` or `refresh_failed` events to:

```text
outputs/hapa-character-sheet.refresh-log.ndjson
```

The generated projection exposes the latest successful refresh at:

```text
refresh.last_success
summary.last_refresh_at
projection_notes.last_refresh_at
```

## Refresh Procedure

1. Confirm the source database exists:

```bash
test -f /Users/calderwong/Documents/Codex/2026-05-25/can-you-grab-my-1-amazon/hapa_second_brain/hapa_second_brain.db
```

2. Run a dry run:

```bash
bin/hapa-character-sheet refresh calder --dry-run
```

3. Run the real refresh:

```bash
bin/hapa-character-sheet refresh calder --from-second-brain
```

4. Validate the projection:

```bash
python3 -m py_compile work/build_character_sheet_projection.py hapa_character_sheet/projection.py hapa_character_sheet/cli.py hapa_character_sheet/server.py
jq empty outputs/hapa-character-sheet-data.json outputs/hapa-character-sheet.manifest.json
bin/hapa-character-sheet timeline calder --scale day --limit 5
bin/hapa-character-sheet skill-quality calder --limit 5
bin/hapa-character-sheet smoke --dry-run
bin/hapa-character-sheet health --deep
```

5. Inspect freshness:

```bash
bin/hapa-character-sheet health --deep | jq '.refresh.last_success'
jq '.summary.last_refresh_at, .refresh.last_success' outputs/hapa-character-sheet-data.json
```

6. If public material will be shared, regenerate exports only after owner review:

```bash
bin/hapa-character-sheet export calder --format markdown --visibility public
```

## What Gets Refreshed

| Character field | Refresh source |
| --- | --- |
| Source/read counts | `content_items`, `exposures`, source-system summaries |
| Skills and families | `skill_inventory`, `skill_evidence`, skill-topic links |
| Stats and ranks | Computed from skill evidence, source diversity, and result/node proof |
| Practice counts | `ai_chat_turns`, turn learning/result links, wisdom cards |
| Hapa nodes and capabilities | `hapa_nodes`, `hapa_node_skills`, capability bridge records |
| Media and image sources | media queue/assets, Avatar Dashboard, Asset Viewer registry |
| Timeline canon | timeline events, activity metrics, skill/node/capability creation |
| Daily timeline canon | `timeline_activity_metrics.time_bucket_day`, synthesized skill unlock dates, `timeline.series_by_scale.day`, `timeline.daily_summary` |
| Skill quality ranking | skill inventory, evidence, source diversity, artifacts, node/capability reach |
| Avatar skill experience | Avatar Dashboard dossier OCR/profile text now; direct avatar-use telemetry when available |
| Agent dossier | agent profiles, harnesses, bridges, protocols, board state |
| Last refresh | `hapa-character-sheet.refresh-log.ndjson` |

## Record Rule

Refresh events are append-only. Do not edit or reorder the refresh log.

Use refresh events for data freshness. Use board events for work history, protocol changes, UI changes, failures that require follow-up, or owner-review decisions.

Minimum refresh event shape:

```json
{
  "id": "hcs-refresh-YYYYMMDDTHHMMSSZ:completed",
  "ts": "2026-06-03T19:52:00+00:00",
  "actor": "hapa-character-sheet-cli",
  "type": "refresh_completed",
  "run_id": "hcs-refresh-YYYYMMDDTHHMMSSZ",
  "payload": {
    "status": "success",
    "trigger": "cli refresh --from-second-brain",
    "source": "work/build_character_sheet_projection.py",
    "summary": {
      "skills": 126,
      "nodes": 109,
      "capabilities": 218,
      "turns": 6106
    },
    "validation": ["builder_returncode_0"]
  }
}
```

## Failure Handling

If refresh fails:

1. Leave the failed refresh event in the log.
2. Run `bin/hapa-character-sheet health --deep`.
3. Check builder stderr from the refresh response.
4. Fix the source issue without mutating unrelated data.
5. Re-run the refresh.
6. Add a board event only if the failure changed protocol, code, source mappings, or required human decision.

## Agent Handoff

Future agents should begin with:

```bash
bin/hapa-character-sheet health --deep | jq '.summary.generated_label, .summary.last_refresh_at, .refresh.last_success'
```

If `summary.last_refresh_at` is empty or stale relative to newly imported Second Brain material, run this protocol. If the projection is current, do not refresh just to churn timestamps.
