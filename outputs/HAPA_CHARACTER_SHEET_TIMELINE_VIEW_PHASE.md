# Hapa Character Sheet Timeline View Phase

Status: implemented prototype phase  
Reviewed: 2026-06-01  
Source anchor: Hapa Second Brain timeline feature

## Source Review

The Second Brain already has a strong timeline system. Character Sheet should reuse it as the source of truth and restyle it as character lore/canon.

Reviewed local anchors:

| Source | Role |
| --- | --- |
| `/Users/calderwong/Documents/Codex/2026-05-25/can-you-grab-my-1-amazon/hapa_second_brain/wiki_articles/content-lifecycle-timeline-protocol.md` | Canonical timeline protocol |
| `/Users/calderwong/Documents/Codex/2026-05-25/can-you-grab-my-1-amazon/hapa_second_brain/wiki_articles/hapa-nodes-capabilities-skills-protocol.md` | Node/capability timeline rules |
| `/Users/calderwong/Documents/Codex/2026-05-25/can-you-grab-my-1-amazon/hapa_second_brain/public/index.html` | Existing Timeline UI shell |
| `/Users/calderwong/Documents/Codex/2026-05-25/can-you-grab-my-1-amazon/hapa_second_brain/public/app.js` | Timeline renderer, filters, dashboard, series, event rows |
| `/Users/calderwong/Documents/Codex/2026-05-25/can-you-grab-my-1-amazon/hapa_second_brain/second_brain.py` | Tables, views, `/api/timeline`, refresh commands |
| `/Users/calderwong/Documents/Codex/2026-05-25/can-you-grab-my-1-amazon/hapa_second_brain/hapa_second_brain.db` | Live event and metric data |

## Existing Timeline Shape

Second Brain separates chronology into:

| Layer | Purpose |
| --- | --- |
| `information_timeline_events` | Canonical ledger of dated events |
| `timeline_event_overview` | Event ledger joined to items, actors, aliases, sources, and AI turns |
| `timeline_activity_metrics` | Precomputed productivity/thinking/learning metrics |
| `timeline_activity_overview` | Metric layer joined back to events, items, actors, turns, and source context |
| `GET /api/timeline` | Filtered agent/UI payload with events, counts, activity dashboard, series, coverage, and actor summaries |

Current live scope sampled from the DB:

| Measure | Count |
| --- | ---: |
| Timeline events | 132,784 |
| Activity metric rows | 41,857 |
| Content created events | 90,044 |
| Content viewed events | 29,318 |
| AI turn prompted events | 6,106 |
| AI turn responded events | 6,106 |
| Hapa node created events | 109 |
| Node capability added events | 218 |
| First event timestamp | 1515-01-01T00:00:00+00:00 |
| Latest event timestamp | 2026-05-31T21:07:30+00:00 |

## Character Sheet Goal

Timeline View should turn raw productivity chronology into playable professional canon:

- what Calder/CJ learned;
- what was practiced through AI turns;
- when skills consolidated;
- when Hapa nodes appeared;
- when node capabilities were added;
- which sources and media shaped each era;
- which proof chains turned into portfolio outcomes.

Second Brain's version is an analytical console. Character Sheet's version should feel like a high-production RPG chronicle: eras, unlocks, lore beats, badges, and proof-backed level-up moments.

## Implementation Checkpoint

The Character Sheet prototype now implements this phase at:

```text
outputs/hapa-character-sheet-prototype.html#presentation-timeline
```

Delivered payload:

| Projection | Current count |
| --- | ---: |
| Canon timeline events | 132,784 |
| Activity metric rows | 41,857 |
| Representative beats | 240 |
| Monthly activity series rows | 215 |
| Timeline layers | 5 |
| Era gates | 4 |

Implemented panels:

| Panel | Delivered behavior |
| --- | --- |
| Chronicle Rail | title card, scope, KPIs, era filters, and layer filters |
| Canon Beats | selectable beat cards covering knowledge, turns, skills, nodes, and capabilities |
| Historical Activity | month-scale layer series with animated bars |
| Canon Inspector | selected beat summary, event type, source system, confidence, target ID, examples, and linked context |
| Source Panels | layer source mix and representative lower-level examples |

Validation artifacts:

| Artifact | Role |
| --- | --- |
| `hapa-character-sheet-presentation-timeline-screenshot.png` | desktop render check |
| `hapa-character-sheet-data.json` | regenerated data projection with timeline payload |
| `hapa-character-sheet-data.js` | browser-loadable `file://` copy |

## Proposed Presentation Route

Add a new Character Mode route:

```text
#presentation-timeline
```

Suggested tab label:

```text
Timeline
```

The top-level tab set becomes:

```text
Hero Detail | Skill Codex | Proof Map | Loadout | Timeline | Passport
```

## Data Projection

Character Sheet should add a timeline projection that compresses the Second Brain payload for browser and export use.

Minimum projection keys:

| Key | Description |
| --- | --- |
| `timeline.summary` | total events, active range, latest refresh, confidence notes |
| `timeline.eras` | grouped periods such as source era, AI turn era, node-building era, capability era |
| `timeline.series` | buckets by day/week/month/year with events per layer |
| `timeline.beats` | top canonical moments selected from timeline events and activity metrics |
| `timeline.layers` | turns, knowledge acquired, skills, capabilities, nodes, media, protocols |
| `timeline.unlocks` | skill/node/capability unlock moments with proof counts |
| `timeline.sources` | knowledge intake source mix over time |
| `timeline.examples` | representative event rows that can deep-link to Second Brain inspectors |

Preferred source query:

```text
GET /api/timeline?layer=&scale=month&limit=500
```

Character Sheet should also support direct SQLite read mode from:

```text
timeline_event_overview
timeline_activity_overview
```

## View Design

The Timeline View should have three abstraction levels:

| Level | Human meaning | UI shape |
| --- | --- | --- |
| Lore | readable character canon | cinematic era rail, level-up cards, source/combat-style chips |
| Proof | verifiable history | event list, metric table, layer filters, confidence/date precision |
| Raw | agent/debug mode | IDs, source systems, target IDs, event types, payload JSON links |

Primary panels:

| Panel | Content |
| --- | --- |
| Era Rail | horizontal or vertical historical rail from first known event to latest Hapa activity |
| Level-Up Track | skill creation, capability creation, node creation, and major AI turn bursts |
| Knowledge Intake | source systems and consumed content over time |
| Turn Forge | AI prompted/responded activity grouped by period and connected to outcomes |
| Node Foundry | Hapa nodes and capability additions as unlock cards |
| Canon Inspector | selected beat with description, exact date, confidence, linked turns, skills, nodes, and sources |

## Interaction Model

- Click an era to filter all panels.
- Click a beat to open a canon inspector.
- Toggle layers: knowledge acquired, turns, skills, capabilities, nodes, media, protocols.
- Toggle scale: year, month, week, day.
- Switch abstraction: Lore, Proof, Raw.
- Show weak dates as lower-confidence canon, not as hard claims.
- Deep-link selected state with hash parameters such as:

```text
#presentation-timeline&scale=day&era=codex-activation&layer=nodes&beat=hapa_node_created:...
```

## Daily View Addendum

Daily view is now implemented as `timeline.series_by_scale.day` plus `timeline.daily_summary`. It uses Second Brain `time_bucket_day` rows and synthesized skill unlock dates so the Character Sheet can answer day-level canon questions without abandoning the broader lore presentation.

Key surfaces:

- `outputs/hapa-character-sheet-prototype.html#presentation-timeline&scale=day`
- `bin/hapa-character-sheet timeline calder --scale day`
- `GET /v1/character-sheets/calder/timeline?scale=day`
- `outputs/HAPA_CHARACTER_SHEET_DAILY_TIMELINE_PROTOCOL.md`

Visualization addendum:

- The Activity panel now renders an x-axis-aligned stacked linechart above the compact rail.
- The chart uses the same filtered bucket model as the rail, so Daily/Weekly/Monthly/Yearly, era, and layer filters remain in sync.
- Layer colors match the rest of the timeline: knowledge green, turns cyan, skills fuchsia, nodes gold, capabilities violet.

## Visual Direction

Use the existing Hapa/Astros plus game-character aesthetic:

- star-map or campaign-map timeline rail;
- glowing era gates;
- node/capability unlock cards with generated thumbnails;
- skill level-up badges;
- AI-turn bursts as signal pulses;
- knowledge-acquired events as source crystals/books/cards;
- animated scan sweep over the active period;
- restrained SFX for era select, unlock select, and filter changes.

Avoid turning it into a generic dashboard. The dense Second Brain metric tables should exist behind Proof/Raw modes, while the default Character Sheet view should tell the character's growth story.

## API And CLI Additions

API:

```text
GET /v1/character-sheets/{id}/timeline
GET /v1/character-sheets/{id}/timeline/eras
GET /v1/character-sheets/{id}/timeline/beats
GET /v1/character-sheets/{id}/timeline/{beat_id}
```

CLI:

```bash
hapa-character-sheet timeline calder --scale month --format json
hapa-character-sheet timeline calder --scale day --limit 40
hapa-character-sheet timeline calder --layer nodes --since 2026-01
hapa-character-sheet timeline calder --lore --limit 40
hapa-character-sheet timeline calder --beat <beat_id> --proof
```

## Acceptance Criteria

- Timeline projection imports Second Brain `information_timeline_events` and `timeline_activity_metrics`.
- View can show turns, skill creation/consolidation, capability creation, node creation, and knowledge acquired over time.
- Default Presentation route reads as lore/canon, not a raw analytics dashboard.
- Proof mode exposes event type, exact date, source system, confidence, date precision, and target IDs.
- Timeline beats link back to skills, capabilities, nodes, turns, media, and source systems where available.
- Filters support event type, layer, vector, source system, date scale, and text query.
- Route state can be deep-linked through the URL hash.
- Browser checks verify no overlap, scrollability, click selection, and reduced-motion compatibility.
