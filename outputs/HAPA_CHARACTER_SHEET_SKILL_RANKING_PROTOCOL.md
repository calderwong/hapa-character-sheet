# Hapa Character Sheet Skill Ranking Protocol

Status: active local protocol  
Protocol id: `hapa-character-sheet-skill-ranking-protocol`  
Owner: Calder/CJ local Hapa workspace  
Last updated: 2026-06-03

## Purpose

Continuously rank two related ideas inside the Hapa Character Sheet:

1. **Skill Quality**: how useful, powerful, and proof-backed a skill is relative to the rest of the skill inventory.
2. **Avatar Experience With Skill**: how much an avatar appears to have used, represented, or embodied a skill relative to its own dossier and the rest of the avatar roster.

The first version is deliberately projection-based. It is good enough to make the Character Sheet explorable now, while leaving a clear protocol for replacing weak proxy signals with direct use logs as they arrive.

## Source Truth

| Layer | Owner | Current signal |
| --- | --- | --- |
| Skills | Hapa Second Brain | `skill_inventory`, evidence counts, source counts, artifact counts, raw score, family, summary, related bodies |
| Capabilities | Hapa Second Brain | `hapa_node_skill_overview`, connected general skills, skill family, node links |
| Nodes | Hapa Second Brain | Hapa node ids, node types, proof cards, topic counts |
| Avatars | Hapa Avatar Dashboard | `avatar-index.json`, dossier OCR, profile text, image titles, image kinds, model/video counts |
| Direct use telemetry | Future Hapa runtime logs | Not yet available in this projection; when available it should override or heavily weight avatar experience |

## Current Formula

### Skill Quality

`quality_score` is normalized against the current skill inventory and combines:

- evidence power
- source diversity
- artifact output
- existing skill raw score
- capability reach
- node reach

Current weight set:

```text
30% evidence power
13% source diversity
12% artifact output
12% raw skill score
21% capability reach
12% node reach
```

The score is mapped to `SS/S/A/B/C/D` bands. The score is relative, so new skills, new evidence, and new capability bridges can change ranks even if a specific skill did not change.

### Avatar Experience

Until direct avatar-use logs exist, `experience_score` is a proxy:

- match avatar dossier OCR/profile text against skill labels, families, summaries, and related bodies
- weight full label phrase hits higher than token hits
- compare each avatar against its own strongest skill match
- compare each avatar-skill pair against the global roster
- blend in a small amount of skill quality so high-value skills surface when experience evidence is close

Current weight set:

```text
58% avatar-relative observed use
27% global-relative observed use
15% skill quality score
```

## Refresh Rule

The ranking is recomputed every time the Character Sheet projection is rebuilt:

```bash
bin/hapa-character-sheet refresh calder --from-second-brain
bin/hapa-character-sheet skill-quality calder --limit 20
```

The generated projection records:

```text
skill_quality.summary.last_reassessed_at
skill_quality.formula_version
skill_quality.method
summary.skill_quality_ranked
summary.avatar_skill_pairs
summary.avatars_ranked
```

If avatar-use telemetry is added later, future agents must update this protocol, bump the formula version, and keep the old proxy method described as a fallback.

## Surfaces

| Surface | Contract |
| --- | --- |
| UI | Hero rank preview and Skill Codex quality/experience matrix |
| CLI | `bin/hapa-character-sheet skill-quality calder --avatar <name> --skill <name> --family <family>` |
| API | `GET /v1/character-sheets/calder/skill-quality?avatar=&skill=&family=&limit=` |
| Agent dossier | Includes summary, top skills, top avatar-skill pairs, and method notes |
| Data | `outputs/hapa-character-sheet-data.json.skill_quality` |
| Flow | `outputs/hapa-character-sheet.skill-ranking-flow.json` |

## Record Rule

Character Sheet owns the ranking projection. Second Brain and Avatar Dashboard own the raw source records. Do not hand-edit generated ranks in `hapa-character-sheet-data.json`; change the source data or the formula, then refresh.

Board events should be written when the formula, source inputs, UI graph, API/CLI contract, or protocol changes. Ordinary refreshes only need refresh-log events unless the result needs review.

## Known Limitations

- Avatar experience is a proxy until direct avatar action/use logs exist.
- OCR-heavy avatars may rank higher because they have more text.
- A skill can score high quality because it has broad node/capability reach even if it is not the most resume-readable label.
- Relative ranks move when the roster changes; this is expected.

## Future Upgrade Path

1. Add avatar-use events with `avatar_id`, `skill_id`, `node_id`, `run_id`, `ts`, `outcome`, and `confidence`.
2. Add decay/freshness so recent use can be separated from lifetime mastery.
3. Add owner pinning for public resume claims without overriding raw ranking truth.
4. Add chart history so rank movement becomes part of the character's canon timeline.
5. Add QA checks that flag suspicious rank jumps after refresh.
