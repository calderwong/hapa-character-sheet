# Hapa Character Sheet Daily Timeline Protocol

## Purpose

The Daily Timeline view is the day-scale abstraction for Character Sheet lore/canon. It lets humans and agents inspect which exact days produced knowledge intake, AI turns, skill unlocks, Hapa node creation, and capability canon.

## Source Of Truth

- Second Brain canonical ledger: `information_timeline_events`
- Second Brain activity buckets: `timeline_activity_metrics.time_bucket_day`
- Character Sheet projection: `timeline.series_by_scale.day`
- Character Sheet summary: `timeline.daily_summary`
- Presentation route: `outputs/hapa-character-sheet-prototype.html#presentation-timeline&scale=day`

## Refresh Rule

After new turns, imports, cards, nodes, capabilities, skills, avatar usage, or media records are added:

1. Run the Second Brain timeline refresh if raw events changed: `python3 second_brain.py refresh-timeline`.
2. Run `python3 second_brain.py refresh-timeline-activity` if events already exist but metrics or activity buckets changed.
3. Run `bin/hapa-character-sheet refresh calder --from-second-brain`.
4. Verify `timeline.daily_summary.latest_day`, `timeline.daily_summary.peak_day`, and `timeline.series_by_scale.day`.
5. Record board/refresh events so future agents can see when daily canon was last rebuilt.

## UI Behavior

- `Daily` shows exact day buckets and a Daily Recon Layer.
- `Weekly`, `Monthly`, and `Yearly` keep broader campaign-scale abstractions.
- Era and layer filters must continue to work after scale changes.
- The stacked linechart must keep all buckets on a shared x-axis, stack layers by event volume, and reuse the same filtered series as the compact rail.
- The selected beat remains a proof-backed timeline record, not a purely decorative animation.

## Agent Contract

Agents may answer day-level questions from `GET /v1/character-sheets/calder/timeline?scale=day`, but should cite the projection timestamp and request a refresh when new source data exists after `summary.last_refresh_at`.
