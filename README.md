# Hapa Character Sheet

Hapa Character Sheet is a local-first portfolio and character-sheet app over Hapa Second Brain. It turns skills, node work, timelines, media, profile dossiers, board state, and evidence lineage into a game-style UI, CLI, loopback API, export packet, and Electron desktop shell.

This repository is private because the checked-in snapshot contains derived personal Character Sheet projection data. Raw Second Brain databases, local vaults, dependency folders, and app bundles are not part of the repo.

## What is included

- `hapa_character_sheet/`: Python runtime shared by the CLI and loopback API.
- `bin/hapa-character-sheet`: local CLI entrypoint.
- `outputs/hapa-character-sheet-prototype.html`: data-driven browser UI.
- `outputs/hapa-character-sheet-data.json` and `outputs/hapa-character-sheet-data.js`: current private projection snapshot for local opening.
- `outputs/HAPA_CHARACTER_SHEET_*.md`: protocol, runtime, refresh, timeline, ranking, and profile-mining runbooks.
- `outputs/hapa-character-sheet.manifest.json`: Hapa node manifest.
- `outputs/hapa-character-sheet.openapi.json`: API contract draft.
- `desktop/`: Electron shell source and launch script.
- `schema/`: app-owned SQLite schema draft.
- `fixtures/`: visibility/redaction fixture.
- `work/build_character_sheet_projection.py`: projection builder for refreshing from local sources.

## Quick start

```bash
./bin/hapa-character-sheet health --deep
./bin/hapa-character-sheet capabilities
./bin/hapa-character-sheet smoke
./bin/hapa-character-sheet serve --host 127.0.0.1 --port 8794
```

Open `outputs/hapa-character-sheet-prototype.html#presentation-hero` directly in a browser, or run the Electron shell:

```bash
cd desktop
npm install
npm start
```

## Refreshing data

The current snapshot is checked in for private reproducibility. To rebuild it from a local Second Brain database:

```bash
export HAPA_SECOND_BRAIN_DB=/path/to/hapa_second_brain.db
./bin/hapa-character-sheet refresh --from-second-brain
```

Optional local source paths used by the builder:

- `HAPA_AVATAR_INDEX`
- `HAPA_AVATAR_DASHBOARD_LINK`
- `HAPA_ASSET_VIEWER_REGISTRY`
- `HAPA_ASSET_VIEWER_APP`
- `HAPA_SECOND_BRAIN_MEDIA_REGISTRY`

If an optional source is missing, the builder skips that enrichment and keeps the rest of the projection moving.

## Privacy boundary

- `owner` visibility may expose local paths and full private projection details.
- `public` and `agent` visibility redact local paths and limit raw history.
- Raw `.db` files, Electron `node_modules`, generated `.app` bundles, and local launchers stay out of git.
- Before making this repository public, regenerate/export a public-only projection and remove owner-tier data snapshots.

## GitHub/doc registration

The app is registered as `hapa-character-sheet` in the Hapa docs/catalog layer. Its Kanban project id is `hapa-app-hapa-character-sheet`, and its local API defaults to `http://127.0.0.1:8794`.
