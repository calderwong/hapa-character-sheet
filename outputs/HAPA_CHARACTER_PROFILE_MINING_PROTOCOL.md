# Hapa Character Profile Mining Protocol

Protocol id: `hapa-character-profile-mining-protocol`  
Owner node: `hapa-character-sheet`  
Source truth: Hapa Second Brain turn cards, Character Sheet projection, skills, nodes, timeline, protocols, media, agents, and board state.

## Purpose

Create an appendable personality and lore dossier for a character. The dossier should help humans understand the character as a person/operator and help agentic systems personify, simulate, or collaborate in the character's style without inventing unsupported biography.

The profile is not a static personality test. It is a living evidence projection built from:

- what the character asks for in turns;
- how they phrase intent, feedback, taste, and constraints;
- which skills and protocols recur;
- what outputs they choose to build;
- which relationships, agents, nodes, and lore objects are maintained;
- what the character treats as proof, progress, risk, or beauty.

## Record Rule

- Second Brain owns raw turns, messages, cards, attribution, lineage, and timeline events.
- Character Sheet owns the curated dossier, public/agent redaction, and persona-ready projections.
- The profile observation ledger is append-only. Do not rewrite prior observations; supersede them with a later observation when better evidence appears.
- Protocol docs explain how to mine and refresh. Generated dossiers must cite the refresh timestamp and evidence windows used.

## Core Outputs

| Output | Purpose |
| --- | --- |
| `HAPA_CHARACTER_PROFILE_CALDER_FOUNDATION.md` | Human-readable seed dossier using Calder as the example character. |
| `HAPA_CHARACTER_PROFILE_CALDER_SHARPENED.md` | Second-pass sharpened dossier from focused Second Brain turn queries. |
| `hapa-character-profile-calder-foundation.json` | Agent-readable structured profile. |
| `hapa-character-profile-calder-runs.json` | Run ledger describing the foundation fill pass and sharpened pass. |
| `hapa-character-profile.observations.ndjson` | Append-only observation ledger. |
| `HAPA_CHARACTER_PROFILE_MINING_PROMPT.md` | Prompt pack for future mining agents. |
| `hapa-character-profile.schema.json` | Shape contract for generated dossiers. |
| `hapa-character-profile-mining-flow.json` | Node Space / protocol flow sidecar. |

## Dossier Sections

1. **Identity**: names, handles, public title, roles, operating labels, timeline range.
2. **Personality Core**: durable traits, each with evidence type, confidence, support count, and counter-signals.
3. **Intentions And Motives**: what the character appears to be trying to make true.
4. **Voice And Sayings**: repeated phrasing, command shapes, feedback language, taste words, ritual phrases, and style constraints.
5. **Background / Lore Canon**: history of projects, eras, source roots, learning arcs, and meaningful symbols.
6. **Relationships**: agents, avatars, protocols, nodes, people/aliases when safe, and how the character relates to them.
7. **Skills And Operating Modes**: not just ranked skills, but how the character tends to deploy them.
8. **Values And Decision Rules**: proof standards, local-first preferences, privacy, polish, speed, play, care, and failure boundaries.
9. **Persona Adapter**: compact instructions for agents that need to think, write, plan, or act in the character's style.
10. **Open Questions**: things the system does not yet know or should avoid asserting.

## Mining Pipeline

### 1. Select Evidence Window

Choose a repeatable input window:

- `full`: all available turns and projection summaries.
- `recent`: turns and outputs since the last profile refresh.
- `focused`: a query such as `media`, `Hapa protocol`, `agent`, `timeline`, or a node name.
- `era`: a timeline era such as `codex-activation`.

Record the window in the dossier metadata.

### 2. Gather Source Bundles

Use the lightest bundle that can answer the profile question:

- Character Sheet JSON for profile, stats, skill families, top turns, agents, nodes, timeline, board.
- Second Brain `turns`, `turn-lineage`, `turn-wisdom-cards`, and `timeline` for deeper evidence.
- Raw full turns only when a quote, voice sample, or subtle interpretation requires it.

### 3. Extract Observation Cards

For each evidence cluster, write small cards:

- `observation`: one claim about the character.
- `category`: trait, motive, voice, lore, relationship, skill, decision rule, risk, or agent instruction.
- `evidence_type`: direct_quote, repeated_phrase, turn_pattern, skill_weight, output_pattern, timeline_pattern, board_pattern, relationship_pattern, or inference.
- `support`: turn IDs, skill IDs, node IDs, docs, counts, or summaries.
- `confidence`: 0.0-1.0.
- `public_safe`: true/false.
- `agent_use`: how an agent should apply the observation.

### 4. Cluster And Weigh

Group observation cards into trait clusters. Prefer clusters that appear across multiple source types. A trait supported by turns, skills, outputs, and board state is stronger than a trait inferred from one prompt.

### 5. Write Dossier

Write a dense human dossier and a structured JSON profile. Every interpretive statement should be one of:

- **Observed**: directly visible in source text or counts.
- **Inferred**: likely pattern from multiple signals.
- **Hypothesis**: plausible but needs more direct evidence.
- **Do not assert**: private, unsupported, or too sensitive.

### 6. Append, Do Not Mutate

Append new observations to `hapa-character-profile.observations.ndjson`. If an older observation is wrong or stale, append a new record with `supersedes`.

### 7. Refresh Triggers

Rerun this protocol after:

- a major turn import;
- a skill refresh or rank shift;
- new agents/avatars are added;
- major node or protocol additions;
- a new Character Sheet public/presentation surface changes how the character is shown;
- a user asks for a more accurate persona adapter.

## Agent Safety Rules

- Do not fabricate personal history, family relationships, diagnosis, legal identity, or private intent.
- Keep Calder/CJ/Hapa naming exactly as the source projection provides unless the owner changes it.
- Short quotes are allowed only when needed to capture voice. Prefer paraphrase and cite the source turn ID.
- Separate "act like the character" from "claim to be the character." Agent outputs should emulate style and priorities while preserving their own identity unless explicitly instructed otherwise by the owner.
- Public profiles must redact local paths, raw private turns, sensitive aliases, and unreviewed speculative claims.

## Validation

```bash
python3 -m py_compile work/build_character_sheet_projection.py
jq empty outputs/hapa-character-profile.schema.json outputs/hapa-character-profile-calder-foundation.json outputs/hapa-character-profile-mining-flow.json
python3 - <<'PY'
import json, pathlib
for line in pathlib.Path('outputs/hapa-character-profile.observations.ndjson').read_text().splitlines():
    if line.strip():
        json.loads(line)
print('observation ledger ok')
PY
bin/hapa-character-sheet refresh calder --from-second-brain
bin/hapa-character-sheet smoke --dry-run
```
