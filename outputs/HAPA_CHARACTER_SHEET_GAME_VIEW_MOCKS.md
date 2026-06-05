# Hapa Character Sheet Game View Mocks

This pack keeps the current data-backed prototype as the proof/operator view and explores a second, more human-facing game character view.

## Generated Mocks

- `hapa-character-sheet-game-mock-01-hero-detail.png`
  - Direction: Hero character detail / professional RPG resume.
  - Best use: Default public showpiece view.
  - Strong ideas: Avatar frame, class plate, stat grid, proof chips, lineage path, readable high-production RPG menu.

- `hapa-character-sheet-game-mock-02-proof-constellation.png`
  - Direction: Tactical proof dossier / evidence constellation.
  - Best use: Lineage and proof-map mode.
  - Strong ideas: Central evidence graph, left identity card, right selected-skill inspector, bottom read-learn-practice-build-prove-publish chain.

- `hapa-character-sheet-game-mock-03-skill-codex.png`
  - Direction: Skill codex / job class tree.
  - Best use: Skills, capabilities, nodes, agents, media, and protocols as a game build/loadout screen.
  - Strong ideas: Radial skill tree, capability inspector, node equipment belt, agent companions, protocol runes, media gallery slots.

- `hapa-character-sheet-game-mock-04-mobile-passport.png`
  - Direction: Handheld character passport.
  - Best use: Mobile and quick-share version.
  - Strong ideas: Large rank/nameplate, touch tabs, stat wheel, featured skills, proof trail, portfolio cards, bottom navigation.

## Recommended Synthesis

Create a second route called `Game View` or `Character Mode` while preserving the current prototype as `Proof View`.

Current prototype routing now uses:

- Normal URL: Backend/Admin/Data view.
- `#presentation-hero`: Hero Detail.
- `#presentation-codex`: Skill Codex.
- `#presentation-proof`: Proof Map.
- `#presentation-loadout`: Loadout.
- `#presentation-timeline`: Timeline.
- `#presentation-passport`: Passport.
- `#presentation-passport&focus=metric%3Askills`: Passport with a selected inspector focus. Passport focus keys support `metric:*`, `stat:*`, `skill:*`, `proof:*`, and `node:*`.

Primary screens:

1. `Hero Detail`
   - Avatar, class, rank, profile tags, primary stats, featured skills, proof chips, and an image-source picker linked to Hapa Avatar Dashboard and Hapa Asset Viewer.
2. `Skill Codex`
   - Radial/branching skill tree, rank bands, XP/evidence, selected capability inspector, GPT Image family thumbnails, and grouped all-skills/all-Hapa-nodes inventories.
3. `Proof Map`
   - Sources, turns, skills, nodes, capabilities, media, agents, and protocols as a graph/constellation.
4. `Loadout`
   - Nodes as equipment, agents as companions, protocols as runes, media as gallery artifacts.
5. `Timeline`
   - Knowledge acquired, AI turns, skill consolidation, capability additions, node creation, and media/protocol canon as an era rail.
6. `Passport`
   - Mobile-first condensed version for quick sharing.

## Interaction Notes

- Treat every stat as clickable and reveal proof: summary -> evidence -> raw source.
- Add animated-feeling polish: stat bar fill, graph pulse, tab glows, card lift, subtle scanlines, hover shimmer, and rank badge pulse.
- Current implementation includes panel wake-in, sweep lines, portrait drift, stat charge bars, rank glint, proof-chain stagger, graph pulses, skill-tree pulses, inventory glow, hover lift, focus rings, and opt-in persisted WebAudio SFX.
- Hero Detail stats use distinct animated HUD glyphs, and Skill Highlights reuse animated Skill Codex family thumbnails so the public hero and Codex screens feel visually connected.
- Hero image selection is live and local-first. Indexed Hapa Avatar Dashboard images, Hapa Asset Viewer previews, Media Registry previews, Character Sheet defaults, custom URLs, and local image files can swap the character art used by the hero portrait, passport hero, and resume/avatar panel.
- Skill Codex branches, capability rows, skill inventory rows, and Hapa node inventory rows are inspectable. Selection updates the right-side capability details while keeping the current skill family context.
- Skill Codex success-signal tags use a bounded wrap/scroll container so long green proof tags stay inside the inspector.
- Proof Map layers, graph nodes, and proof-flow steps are inspectable. Selection highlights the constellation, updates the layer inspector, shows the next aggregation lower, and surfaces representative examples from sources, turns, skills, nodes, capabilities, media, agents, and protocols.
- Loadout now treats every known Hapa node as equipment. All 109 indexed nodes are selectable, type-filterable, and represented with generated animated thumbnails/icons, score meters, topic/card stats, linked capabilities, related media, and source-path proof.
- Timeline adapts the Second Brain timeline console into character lore/canon. The implemented route shows eras, level-up beats, knowledge intake, AI-turn bursts, skill/capability unlocks, and node creation as a campaign history, with event dates, source systems, confidence, target IDs, and representative examples exposed in the canon inspector and source panels.
- Passport items are inspectable. Clicking a metric, core attribute, featured skill, proof-trail step, or portfolio node selects it and shows a description, the next aggregation lower, and examples from the live projection.
- Keep text short in Game View. Use the current Proof View for dense explanations and AI-readable raw structure.
- Use the same `hapa-character-sheet-data.json` projection for both routes.
- Replace generated placeholder portraits with real Hapa avatar assets when choosing the final direction.

## Image Generation Prompts

The mocks were generated with built-in GPT image generation using the current desktop and mobile screenshots as visual/structural references.

Prompt themes:

- Hero character detail / professional RPG resume.
- Tactical proof dossier / evidence constellation.
- Skill codex / job class tree.
- Mobile handheld character passport.
