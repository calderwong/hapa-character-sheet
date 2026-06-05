# Hapa Character Sheet Node

Status: design-ready Hapa happ proposal  
Review date: 2026-06-01  
Working title: Hapa Character Sheet  
Node id: `hapa-character-sheet`  
App id: `world.hapa.character-sheet`

## Source Review

I reviewed the local Hapa front door, protocol docs, Second Brain docs/schema, flow-card standards, Quest Keeper, and Overwatch Kanban patterns. The strongest fit is a Hapa-standard node that sits between Second Brain and the outside world: Second Brain remains the evidence engine; Character Sheet becomes the curated resume, portfolio, RPG-style stat sheet, agent dossier, media gallery, and lineage browser.

Verified local anchors:

| Layer | Local source | Role for Character Sheet |
| --- | --- | --- |
| Hapa front door | `/Users/calderwong/Desktop/hapa` | Node map, protocol standards, CLI/API shape, Node Space flow registry |
| Canon/wiki | `/Users/calderwong/Desktop/Hapa_Worldbuilding_Wiki` | Protocol/canon pages, flow explainers, public narrative language |
| Second Brain | `/Users/calderwong/Documents/Codex/2026-05-25/can-you-grab-my-1-amazon/hapa_second_brain` | Skills, turns, content, lineage, agents, node capabilities, media queue |
| Second Brain DB | `hapa_second_brain.db` | Main source tables and derived views |
| Quest Keeper | `/Users/calderwong/Desktop/hapa-quest-keeper` | Hapa-wide board status rollup |
| Overwatch Kanban | `/Users/calderwong/Documents/Codex/2026-05-27/can-you-generate-me-some-concept/hapa-overwatch-kanban` | Append-only project board model |

Observed Second Brain snapshot:

| Surface | Count |
| --- | ---: |
| Content items | 67,819 |
| Exposures | 75,566 |
| AI chat turns | 6,106 |
| Skill inventory records | 126 |
| Skill evidence records | 1,202,201 |
| Hapa nodes | 109 |
| Hapa node skills | 218 |
| Agent profiles | 7 |
| Harness profiles | 7 |
| Capability bridge connections | 11,658 |
| Turn learning links | 66,847 |
| Turn result links | 6,106 |
| Wiki articles | 64 |

The current Hapa standards imply this node should ship with README, AGENTS guide, docs, `/health`, `/capabilities`, JSON CLI parity, deterministic smoke output, a desktop wrapper, web UI, source provenance, and board writeback.

## Product Intent

Hapa Character Sheet answers four questions in one surface:

1. What can this person do professionally?
2. What are their game-sheet stats, classes, traits, and skill trees?
3. What evidence proves those skills, and where did the knowledge come from?
4. What media, outcomes, agents, nodes, and protocols show the work in motion?

It should feel like a serious resume/brochure site that has been pulled into a tactical RPG menu. The public layer gets clarity, outcomes, taste, and proof. The agent layer gets structured JSON, provenance links, capability routes, and redaction-safe evidence. The owner layer gets editing, refresh, privacy, and curation controls.

## Core Modes

| Mode | Audience | Purpose |
| --- | --- | --- |
| Public Resume | recruiters, collaborators, clients | Fast professional summary, selected outcomes, contact/export, redacted proof |
| Portfolio Brochure | people evaluating taste and quality | Featured projects, media, demos, case studies, before/after results |
| Character Sheet | Hapa/game layer | Stats, classes, traits, skill ranks, protocol cards, inventory, affinities |
| Skill Codex | humans and agents | Skills with explanations, evidence, source media, turns, node capabilities |
| Lineage Viewer | agents, collaborators, owner | Source exposure -> AI turn -> result -> Hapa node -> skill -> protocol route |
| Timeline View | humans, agents, owner | Historical lore/canon rail for knowledge acquired, turns, skills, capabilities, and node creation |
| Agent Dossier | AI collaborators | Machine-readable context pack, capability map, preferred protocols, open tasks |
| Backstage Admin | owner | Edit, pin, redact, merge, refresh, export, and publish |

## Information Architecture

The app should open directly to the usable sheet, not a marketing landing page.

Primary menus:

| Menu | Key sections |
| --- | --- |
| Sheet | identity header, class stack, stat block, highlighted titles, live status |
| Resume | summary, roles, projects, outcomes, tools, exports |
| Skills | skill tree, skill cards, evidence meter, examples, related protocols |
| Portfolio | featured work, Hapa nodes, media, case studies, build logs |
| Lineage | source graph, turn cards, result cards, derivation chains, confidence |
| Timeline | eras, level-up beats, knowledge intake, turn forge, node/capability unlocks, canon inspector |
| Media | hero art, videos, screenshots, songs, card art, avatar variants |
| Agents | agents used, harnesses, delegation context, skill bridges |
| Protocols | protocol cards, flow explainers, operating standards, smoke proofs |
| Backstage | profile editor, redaction rules, refresh jobs, board status |

## Visual Direction

Target aesthetic: modern 2.5 anime meets early-2000s brushed pixel RPG UI, blended with Hapa/Astros operator density.

Rules:

- Deep neutral base with cyan system lights, fuchsia creative paths, green validation, gold provenance, and rose danger states.
- Brushed-metal pixel bands, inset scanlines, restrained glow, square-ish 6-8px card radius, and compact stat chips.
- The character portrait is a professional identity object, not a decorative hero. It should show a 2.5D operator/avatar frame with media and capability trails around it.
- Menus should feel like a game equipment/status screen, while the resume content remains readable and exportable.
- Public mode is polished and focused. Owner mode can be dense.
- No unsupported claims. Every badge, skill, and result should reveal evidence status.

## Data Model

Character Sheet should not replace Second Brain. It should materialize curated projections.

| Character Sheet concept | Source tables/views |
| --- | --- |
| Person profile | `information_actors`, `actor_aliases`, `avatar_profiles`, curated profile records |
| Professional summary | pinned `wiki_articles`, owner-authored resume entries, selected skill summaries |
| Skill cards | `skill_inventory`, `skill_evidence`, `turn_skill_examples`, `turn_skill_clusters` |
| Stat block | computed from skills, evidence diversity, result links, recency, review confidence |
| Source media | `content_items`, `exposures`, `content_texts`, `chunk_summaries`, `knowledge_claims` |
| AI turns | `ai_chat_turns`, `hapa_turn_cards`, `turn_wisdom_cards` |
| Learning lineage | `turn_learning_links`, `turn_result_links`, `information_derivations` |
| Timeline canon | `information_timeline_events`, `timeline_event_overview`, `timeline_activity_metrics`, `timeline_activity_overview` |
| Hapa outcomes | `hapa_nodes`, `hapa_node_skills`, `ecosystem_connections`, `hapa_artifacts`, `hapa_cards` |
| Agents and harnesses | `agent_profiles`, `harness_profiles`, `agent_harness_links`, `capability_bridge_connections` |
| Media | `hapa_visual_assets`, `content_media_assets`, `media_generation_queue` |
| Board state | Overwatch Kanban event log and Quest Keeper rollup |

Minimum app-owned tables:

| Table | Purpose |
| --- | --- |
| `character_profiles` | owner-curated identity, public title, bio, visibility defaults |
| `character_profile_sections` | resume sections, custom copy, pinned order |
| `character_stat_snapshots` | cached computed stats with source counts and formula version |
| `character_skill_pins` | pinned skills, labels, visibility, brochure priority |
| `character_portfolio_pins` | pinned projects/media/results and display copy |
| `character_privacy_rules` | field-level redaction and audience gates |
| `character_exports` | generated PDF/Markdown/JSON packets and provenance manifest |

## Stat System

Stats should be professional enough for a resume and playful enough for a character sheet.

Suggested stats:

| Stat | Professional meaning | Evidence route |
| --- | --- | --- |
| Systems | Architecture, schemas, cross-node design | schema, node, API, protocol evidence |
| Craft | Execution quality and implementation depth | result links, artifacts, verification |
| Signal | Retrieval, summarization, context quality | search, context, lineage, source distillation |
| Forge | Creation of apps, cards, media, and workflows | artifacts, Hapa nodes, media runs |
| Lore | Worldbuilding, narrative, taxonomy, canon sense | wiki, card, lore, source mapping |
| Stewardship | Provenance, privacy, safety, maintenance | attribution, data hygiene, redaction |
| Tempo | Shipping cadence and iteration velocity | turn recency, board events, result runs |
| Communion | Agent orchestration, collaboration, delegation | agent/harness bridges, protocols |

Score formula draft:

```text
base = 20
evidence = log10(evidence_count + 1) * 11
diversity = distinct_source_systems * 3
execution = result_count * 1.5
freshness = recent_verified_events * 0.8
confidence = reviewed_bonus - stale_penalty - weak_overlap_penalty
score = clamp(1, 99, base + evidence + diversity + execution + freshness + confidence)
rank = D/C/B/A/S/SS by score band
```

Every stat should show: value, rank, top evidence, freshness, confidence, and "why this score exists."

## Skill Card Shape

Each skill card should include:

| Field | Meaning |
| --- | --- |
| `skill_id` | Stable Second Brain skill id |
| `title` | Human-readable skill |
| `family` | skill family or class |
| `rank` | computed D through SS |
| `resume_claim` | short professional claim |
| `game_text` | RPG-style trait/effect |
| `explanation` | what the skill means in practice |
| `source_mix` | where the knowledge came from |
| `turn_examples` | applied AI turns that demonstrate execution |
| `result_links` | artifacts, nodes, docs, media, card outputs |
| `node_capabilities` | Hapa node skills that use or enhance the skill |
| `agent_routes` | agents/harnesses that can act on it |
| `privacy_level` | public, trusted, local, owner-only |
| `evidence_status` | verified, inferred, weak, stale, needs review |

## Public Resume Utility

The resume view should generate four outputs from the same source spine:

| Export | Purpose |
| --- | --- |
| `resume.md` | readable professional profile with source-backed claims |
| `resume.pdf` | human share packet |
| `agent-dossier.json` | machine-readable capability and evidence pack |
| `portfolio-brochure.html` | rich media public page |

The public copy must be manually curatable. The system can recommend phrasing, but the owner decides what becomes an external claim.

## API Contract

Base endpoints:

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | loopback health, DB reachability, source freshness |
| `GET /capabilities` | Hapa protocol parity and feature list |
| `GET /v1/character-sheets` | list available sheets/profiles |
| `GET /v1/character-sheets/{id}` | complete sheet projection |
| `GET /v1/character-sheets/{id}/resume` | resume projection |
| `GET /v1/character-sheets/{id}/stats` | computed RPG/professional stats |
| `GET /v1/character-sheets/{id}/skills` | skill cards with filters |
| `GET /v1/character-sheets/{id}/skills/{skill_id}/evidence` | skill evidence and examples |
| `GET /v1/character-sheets/{id}/portfolio` | pinned projects and media |
| `GET /v1/character-sheets/{id}/lineage` | source -> turn -> result chains |
| `GET /v1/character-sheets/{id}/timeline` | historical canon timeline with eras, beats, layers, and proof links |
| `GET /v1/character-sheets/{id}/agent-dossier` | redaction-safe agent context pack |
| `POST /v1/character-sheets/{id}/refresh` | rebuild projections |
| `POST /v1/character-sheets/{id}/exports` | create PDF/Markdown/HTML/JSON export |

All responses should include `contract_version`, `truth_status`, `generated_at`, `source_counts`, and `redaction_mode`.

Runtime checkpoint:

| Surface | Implemented entry |
| --- | --- |
| Shared projection runtime | `hapa_character_sheet/projection.py` |
| CLI | `bin/hapa-character-sheet` |
| API server | `python3 -m hapa_character_sheet.server` |
| Schema migration | `schema/hapa_character_sheet_schema.sql` |
| Visibility fixture | `fixtures/hapa_character_sheet_visibility_fixture.json` |
| Desktop shell | `desktop/main.js` |
| Runtime docs | `outputs/HAPA_CHARACTER_SHEET_RUNTIME.md` |

## CLI Contract

```bash
hapa-character-sheet health --deep
hapa-character-sheet capabilities
hapa-character-sheet serve --host 127.0.0.1 --port 8794
hapa-character-sheet sheet calder --visibility public --format json
hapa-character-sheet resume calder --format markdown
hapa-character-sheet stats calder --explain
hapa-character-sheet skills calder --family data_engineering --min-rank A
hapa-character-sheet skill calder skill:6c53f8440aaf1249 --evidence --limit 20
hapa-character-sheet lineage calder --skill "Schema / Data Modeling" --limit 20
hapa-character-sheet timeline calder --scale month --lore
hapa-character-sheet timeline calder --layer nodes --since 2026-01 --proof
hapa-character-sheet portfolio calder --pinned
hapa-character-sheet agent-dossier calder --visibility trusted
hapa-character-sheet refresh calder --from-second-brain --dry-run
hapa-character-sheet export calder --format html --visibility public
hapa-character-sheet kanban state
hapa-character-sheet smoke --dry-run
```

CLI writes must support `--dry-run` where practical, print JSON by default, and exit non-zero with a machine-readable error on failure.

## Web And Desktop

Web:

- Local server at `127.0.0.1`.
- Static web UI backed by API projections.
- Public export mode can produce a static brochure site.
- Main screen is the sheet, with docked menus and fast filters.

Desktop:

- Electron wrapper similar to Second Brain.
- Starts local server, opens the same UI, and uses a preload bridge only for safe local open/show actions.
- Desktop-only conveniences: Finder reveal, local export folder, media previews, board deep links, Node Space handoff.

## Privacy And Redaction

Visibility tiers:

| Tier | Use |
| --- | --- |
| Public | external resume, public brochure, redacted portfolio |
| Trusted | collaborators, hiring loops, client diligence |
| Agent | local AI collaborator context with structured evidence and constraints |
| Owner | full local view with raw paths, private source detail, draft notes |

Rules:

- Raw personal histories stay local unless explicitly pinned public.
- Source consumption proves learning exposure, not endorsement or mastery by itself.
- Turn/result links are evidence-weighted hypotheses unless directly verified.
- Public claims must come from pinned skills, reviewed outcomes, or owner-authored sections.
- Agent dossier should expose enough to route work without dumping private raw media history.

## Protocol Flow

Route script:

1. `Second Brain -> Character Sheet [DATA|API]`: load skills, evidence, turns, nodes, agents, media, and lineage.
2. `Character Sheet -> Stat Engine [DATA]`: compute professional/RPG stats with formula version and evidence counts.
3. `Character Sheet -> Resume Surface [UI|DATA]`: render public summary, roles, selected outcomes, and exports.
4. `Character Sheet -> Skill Codex [UI|API]`: expose skill cards, explanations, examples, and evidence trails.
5. `Character Sheet -> Agent Dossier [API|CLI]`: emit redaction-safe machine context and capability routes.
6. `Character Sheet -> Overwatch Kanban [DATA|API|CLI]`: append progress, blockers, review notes, and verification.
7. `Character Sheet -> Node Space [DATA]`: publish flow sidecar and card mechanics for ecosystem visualization.

Record rule:

- Second Brain owns raw/derived memory.
- Character Sheet owns curated presentation, redaction, stat snapshots, and export manifests.
- Wiki owns durable protocol explanation after review.
- Overwatch owns append-only build coordination.
- Node Space owns flow visualization and teachable process card sidecar.

## Implementation Plan

Phase 0: product contract

- Create README, AGENTS guide, Hapa node manifest, docs/API.md, docs/CLI.md, docs/HAPA_PROTOCOL_PARITY.md.
- Create seed fixtures from current Second Brain projection.
- Create Overwatch board project and seed events.

Phase 1: read-only spine

- Build projection service over Second Brain SQLite and API.
- Add `health`, `capabilities`, `stats`, `sheet`, `skills`, `lineage`, and `agent-dossier` CLI.
- Add deterministic `smoke --dry-run`.

Phase 2: web/desktop UI

- Build dense multi-menu UI.
- Add public/trusted/agent/owner visibility switch.
- Add resume, skills, portfolio, lineage, media, agents, protocols, and backstage menus.
- Wrap with Electron and local launcher.

Phase 3: curation and exports

- Add pinning, owner edits, redaction rules, manual claim review, export manifests.
- Add Markdown/JSON/HTML exports first; PDF second.

Phase 4: Hapa ecosystem integration

- Publish flow explainer and protocol-flow JSON.
- Register board in Quest Keeper/Overwatch.
- Add Node Space deep link and Second Brain refresh hooks.
- Add visual asset generation queue for sheet portraits, skill cards, and portfolio cards.

## Acceptance

The node is ready when:

- `health`, `capabilities`, and `smoke --dry-run` pass.
- UI/API/CLI all use the same projection functions.
- Public view can show a polished resume without exposing private raw data.
- Skill card evidence can trace from source media to turns to results to Hapa nodes.
- Agent dossier returns structured JSON with visibility-aware redaction.
- Overwatch board contains tracked tasks, blockers, review gates, and verification notes.
- Docs state verified facts separately from inferred roadmap ideas.

## Design Risk Register

| Risk | Mitigation |
| --- | --- |
| Resume claims overstate inferred evidence | Require pinned/reviewed claims for public mode |
| Public export leaks private source detail | Visibility gates and export manifests |
| UI becomes too game-like for professional use | Separate Resume mode from Character Sheet mode while sharing evidence |
| Evidence graph overwhelms casual viewers | Progressive depth: summary, proof, full lineage |
| Data freshness is unclear | Show generated time, source counts, and refresh status |
| Second Brain schema changes | Projection adapter with contract version and smoke fixtures |

## Immediate Next Cards

The seed Kanban board in `hapa-character-sheet.board.events.ndjson` starts the work with P0 cards for schema, read adapter, privacy, UI, API, CLI, smoke, and protocol registration. It also includes review and backlog cards for public export, media, desktop wrapper, and Node Space integration.
