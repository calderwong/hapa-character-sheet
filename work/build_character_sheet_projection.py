#!/usr/bin/env python3
"""Build a data-driven Hapa Character Sheet prototype.

This script reads the Hapa Second Brain SQLite projection and the local
Character Sheet board seed, then writes a static browser prototype plus a
separate JSON/JS data payload into outputs/.
"""

from __future__ import annotations

import json
import math
import os
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(os.environ.get("HAPA_CHARACTER_SHEET_ROOT", Path(__file__).resolve().parents[1])).resolve()
OUT = ROOT / "outputs"
WORK = ROOT / "work"
DB = Path(os.environ.get("HAPA_SECOND_BRAIN_DB", ROOT / "local" / "hapa_second_brain.db")).expanduser()
BOARD_EVENTS = OUT / "hapa-character-sheet.board.events.ndjson"
REFRESH_LOG = OUT / "hapa-character-sheet.refresh-log.ndjson"
REFRESH_PROTOCOL = OUT / "HAPA_CHARACTER_SHEET_REFRESH_PROTOCOL.md"
SKILL_RANKING_PROTOCOL = OUT / "HAPA_CHARACTER_SHEET_SKILL_RANKING_PROTOCOL.md"
TIMELINE_DAILY_PROTOCOL = OUT / "HAPA_CHARACTER_SHEET_DAILY_TIMELINE_PROTOCOL.md"
CHARACTER_PROFILE_PROTOCOL = OUT / "HAPA_CHARACTER_PROFILE_MINING_PROTOCOL.md"
CHARACTER_PROFILE_PROMPT = OUT / "HAPA_CHARACTER_PROFILE_MINING_PROMPT.md"
CHARACTER_PROFILE_DOSSIER = OUT / "HAPA_CHARACTER_PROFILE_CALDER_FOUNDATION.md"
CHARACTER_PROFILE_STRUCTURED = OUT / "hapa-character-profile-calder-foundation.json"
CHARACTER_PROFILE_SHARPENED = OUT / "HAPA_CHARACTER_PROFILE_CALDER_SHARPENED.md"
CHARACTER_PROFILE_RUNS = OUT / "hapa-character-profile-calder-runs.json"
CHARACTER_PROFILE_LEDGER = OUT / "hapa-character-profile.observations.ndjson"
CHARACTER_PROFILE_FLOW = OUT / "hapa-character-profile-mining-flow.json"
AVATAR_INDEX = Path(os.environ.get("HAPA_AVATAR_INDEX", ROOT / "local" / "avatar-index.json")).expanduser()
AVATAR_DASHBOARD_LINK = Path(os.environ.get("HAPA_AVATAR_DASHBOARD_LINK", ROOT / "local" / "Launch Hapa Avatar Dashboard.command")).expanduser()
ASSET_VIEWER_REGISTRY = Path(os.environ.get("HAPA_ASSET_VIEWER_REGISTRY", ROOT / "local" / "hapa_asset_registry.json")).expanduser()
ASSET_VIEWER_APP = Path(os.environ.get("HAPA_ASSET_VIEWER_APP", ROOT / "local" / "Hapa Asset Viewer.app")).expanduser()
MEDIA_REGISTRY_INDEX = Path(os.environ.get("HAPA_SECOND_BRAIN_MEDIA_REGISTRY", ROOT / "local" / "second-brain-public" / "index.html")).expanduser()
CHARACTER_MODEL_VIDEO = OUT / "assets" / "calder-character-video-loop.mp4"
CHARACTER_MODEL_POSTER = OUT / "assets" / "calder-character-model-poster.jpg"
PROFILE_BACKGROUND_VIDEO_ASSETS = [
    {
        "id": "profile-bg:calder-dramatic-intro-01",
        "label": "Calder Dramatic Intro 01",
        "url": "assets/calder-profile-dramatic-intro-01.mp4",
        "poster": "assets/calder-profile-dramatic-intro-01-poster.jpg",
        "source": OUT / "assets" / "calder-profile-dramatic-intro-01.mp4",
        "poster_source": OUT / "assets" / "calder-profile-dramatic-intro-01-poster.jpg",
        "meta": "10s 16:9 MP4 / Persona Codex background loop",
    },
    {
        "id": "profile-bg:calder-dramatic-intro-02",
        "label": "Calder Dramatic Intro 02",
        "url": "assets/calder-profile-dramatic-intro-02.mp4",
        "poster": "assets/calder-profile-dramatic-intro-02-poster.jpg",
        "source": OUT / "assets" / "calder-profile-dramatic-intro-02.mp4",
        "poster_source": OUT / "assets" / "calder-profile-dramatic-intro-02-poster.jpg",
        "meta": "10s 16:9 MP4 / Persona Codex alternate background loop",
    },
]
SKILL_VIDEO_LOOP_ASSETS = [
    {
        "id": "skill-loop:r-kick",
        "label": "Round Kick Skill Loop",
        "verb": "Kick",
        "url": "assets/r-kick-skill.mp4",
        "poster": "assets/r-kick-skill-poster.jpg",
        "source": OUT / "assets" / "r-kick-skill.mp4",
        "poster_source": OUT / "assets" / "r-kick-skill-poster.jpg",
        "meta": "8s vertical MP4 / high-impact skill execution loop",
    },
    {
        "id": "skill-loop:r-run",
        "label": "Run Skill Loop",
        "verb": "Run",
        "url": "assets/r-run.mp4",
        "poster": "assets/r-run-poster.jpg",
        "source": OUT / "assets" / "r-run.mp4",
        "poster_source": OUT / "assets" / "r-run-poster.jpg",
        "meta": "8s vertical MP4 / traversal and tempo skill loop",
    },
    {
        "id": "skill-loop:r-walk",
        "label": "Walk Skill Loop",
        "verb": "Walk",
        "url": "assets/r-walk.mp4",
        "poster": "assets/r-walk-poster.jpg",
        "source": OUT / "assets" / "r-walk.mp4",
        "poster_source": OUT / "assets" / "r-walk-poster.jpg",
        "meta": "8s vertical MP4 / steady-state mastery loop",
    },
]


DOC_PATHS = [
    "/Users/calderwong/Desktop/hapa/docs/NODE_MAP.md",
    "/Users/calderwong/Desktop/hapa/docs/HAPA_PROTOCOL_STANDARDS.md",
    "/Users/calderwong/Desktop/hapa/docs/OPERATING_MODEL.md",
    "/Users/calderwong/Desktop/hapa/docs/API.md",
    "/Users/calderwong/Desktop/hapa/docs/CLI.md",
    "/Users/calderwong/Desktop/hapa/docs/HAPA_PROTOCOL_CARDS.md",
    "/Users/calderwong/Desktop/hapa/docs/PROCESS_FLOW_CARDS.md",
    "/Users/calderwong/Desktop/hapa/docs/NODE_SPACE_DESKTOP.md",
    "/Users/calderwong/Documents/Codex/2026-05-25/can-you-grab-my-1-amazon/hapa_second_brain/README.md",
    "/Users/calderwong/Documents/Codex/2026-05-25/can-you-grab-my-1-amazon/hapa_second_brain/docs/API.md",
    "/Users/calderwong/Documents/Codex/2026-05-25/can-you-grab-my-1-amazon/hapa_second_brain/docs/CLI.md",
    "/Users/calderwong/Documents/Codex/2026-05-25/can-you-grab-my-1-amazon/hapa_second_brain/wiki_articles/turns-to-results-lineage-protocol.md",
    "/Users/calderwong/Documents/Codex/2026-05-27/can-you-generate-me-some-concept/hapa-overwatch-kanban/README.md",
    "/Users/calderwong/Desktop/hapa-quest-keeper/README.md",
    str(REFRESH_PROTOCOL),
    str(SKILL_RANKING_PROTOCOL),
    str(TIMELINE_DAILY_PROTOCOL),
    str(CHARACTER_PROFILE_PROTOCOL),
    str(CHARACTER_PROFILE_PROMPT),
    str(CHARACTER_PROFILE_DOSSIER),
    str(CHARACTER_PROFILE_SHARPENED),
]


HTML_STATIC = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Hapa Character Sheet</title>
  <style>
    :root {
      --bg: #020617;
      --bg-2: #060b16;
      --panel: rgba(8, 16, 32, 0.82);
      --panel-2: rgba(14, 23, 42, 0.76);
      --line: rgba(148, 163, 184, 0.24);
      --line-strong: rgba(34, 211, 238, 0.38);
      --text: #e5eefc;
      --muted: #93a4ba;
      --soft: #bac7da;
      --cyan: #22d3ee;
      --fuchsia: #e879f9;
      --gold: #fbbf24;
      --green: #34d399;
      --rose: #fb7185;
      --violet: #a78bfa;
      --ink: #0b1222;
      --shadow: 0 24px 80px rgba(0, 0, 0, 0.42);
      color-scheme: dark;
    }
    * { box-sizing: border-box; }
    html { min-height: 100%; background: var(--bg); }
    body {
      min-height: 100%;
      margin: 0;
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background:
        linear-gradient(90deg, rgba(34, 211, 238, 0.05) 1px, transparent 1px),
        linear-gradient(0deg, rgba(232, 121, 249, 0.035) 1px, transparent 1px),
        radial-gradient(circle at 18% 0%, rgba(34, 211, 238, 0.16), transparent 31rem),
        radial-gradient(circle at 88% 8%, rgba(251, 191, 36, 0.12), transparent 28rem),
        linear-gradient(135deg, #020617 0%, #07111f 46%, #110b1d 100%);
      background-size: 46px 46px, 46px 46px, auto, auto, auto;
      overflow-x: hidden;
    }
    body:before {
      content: "";
      position: fixed;
      inset: 0;
      z-index: -1;
      pointer-events: none;
      background: repeating-linear-gradient(0deg, rgba(255, 255, 255, 0.035) 0, rgba(255, 255, 255, 0.035) 1px, transparent 1px, transparent 4px);
      opacity: 0.23;
    }
    button, input, select {
      font: inherit;
    }
    button, select, input {
      color: var(--text);
      background: rgba(2, 6, 23, 0.76);
      border: 1px solid var(--line);
      border-radius: 8px;
    }
    button { cursor: pointer; }
    a { color: var(--cyan); text-decoration: none; }
    a:hover { color: #a5f3fc; }
    .app {
      min-height: 100vh;
      width: 100%;
      max-width: 100%;
      display: grid;
      grid-template-columns: 292px minmax(0, 1fr);
      overflow-x: hidden;
    }
    .sidebar {
      position: sticky;
      top: 0;
      height: 100vh;
      min-width: 0;
      padding: 18px 14px;
      border-right: 1px solid var(--line);
      background: rgba(2, 6, 23, 0.86);
      backdrop-filter: blur(18px);
      overflow: auto;
      scrollbar-color: var(--cyan) rgba(2, 6, 23, 0.8);
    }
    .brand {
      border: 1px solid rgba(34, 211, 238, 0.33);
      background:
        linear-gradient(135deg, rgba(34, 211, 238, 0.13), rgba(232, 121, 249, 0.08)),
        rgba(8, 16, 32, 0.7);
      padding: 14px;
      border-radius: 10px;
      box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.03), inset 0 0 26px rgba(34, 211, 238, 0.06);
    }
    .brand-kicker, .micro, .label, .chip, .badge, .nav-meta, .record-meta, .meter-label, .section-kicker {
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
      letter-spacing: 0;
      text-transform: uppercase;
    }
    .brand-kicker, .section-kicker {
      color: var(--cyan);
      font-size: 11px;
      margin-bottom: 6px;
    }
    .brand h1 {
      margin: 0;
      font-size: 23px;
      line-height: 1.05;
      font-weight: 800;
    }
    .brand p {
      margin: 8px 0 0;
      color: var(--soft);
      font-size: 13px;
      line-height: 1.45;
      overflow-wrap: anywhere;
    }
    .nav {
      display: grid;
      gap: 7px;
      margin-top: 14px;
    }
    .nav-button {
      min-height: 42px;
      display: grid;
      grid-template-columns: 28px 1fr auto;
      gap: 9px;
      align-items: center;
      width: 100%;
      padding: 8px 9px;
      text-align: left;
      border-color: rgba(148, 163, 184, 0.18);
      background: rgba(15, 23, 42, 0.5);
      transition: border-color 160ms ease, transform 160ms ease, background 160ms ease, box-shadow 160ms ease;
    }
    .nav-button:hover,
    .nav-button.active {
      border-color: rgba(34, 211, 238, 0.55);
      background: linear-gradient(90deg, rgba(34, 211, 238, 0.13), rgba(232, 121, 249, 0.07));
      box-shadow: inset 3px 0 0 var(--cyan), 0 0 24px rgba(34, 211, 238, 0.08);
    }
    .nav-button:hover { transform: translateX(2px); }
    .nav-icon {
      display: grid;
      place-items: center;
      width: 28px;
      height: 28px;
      border-radius: 8px;
      background: rgba(34, 211, 238, 0.08);
      color: var(--cyan);
      border: 1px solid rgba(34, 211, 238, 0.18);
    }
    .nav-title {
      font-size: 13px;
      font-weight: 700;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .nav-meta {
      color: var(--muted);
      font-size: 10px;
    }
    .side-stats {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
      margin-top: 14px;
    }
    .mini-stat {
      padding: 9px;
      border-radius: 8px;
      border: 1px solid var(--line);
      background: rgba(15, 23, 42, 0.58);
      min-width: 0;
    }
    .mini-stat strong {
      display: block;
      font-size: 17px;
      color: #fff;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .mini-stat span {
      display: block;
      color: var(--muted);
      font-size: 10px;
      margin-top: 2px;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .main {
      min-width: 0;
      max-width: 100%;
      display: grid;
      grid-template-rows: auto auto minmax(0, 1fr);
    }
    .topbar {
      position: sticky;
      top: 0;
      z-index: 10;
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 16px;
      align-items: center;
      padding: 16px 22px;
      border-bottom: 1px solid var(--line);
      background: rgba(2, 6, 23, 0.78);
      backdrop-filter: blur(18px);
    }
    .route {
      min-width: 0;
    }
    .route h2 {
      margin: 0;
      font-size: clamp(24px, 4vw, 42px);
      line-height: 1.03;
      font-weight: 850;
    }
    .route p {
      margin: 7px 0 0;
      color: var(--soft);
      font-size: 14px;
      max-width: 980px;
      line-height: 1.45;
      overflow-wrap: anywhere;
    }
    .status-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      justify-content: flex-end;
      min-width: 0;
    }
    .chip, .badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      min-height: 26px;
      padding: 5px 8px;
      border-radius: 999px;
      border: 1px solid rgba(148, 163, 184, 0.24);
      background: rgba(15, 23, 42, 0.66);
      color: var(--soft);
      font-size: 10px;
      white-space: nowrap;
      overflow-wrap: anywhere;
    }
    .chip.cyan, .badge.cyan { color: #a5f3fc; border-color: rgba(34, 211, 238, 0.33); }
    .chip.gold, .badge.gold { color: #fde68a; border-color: rgba(251, 191, 36, 0.35); }
    .chip.green, .badge.green { color: #bbf7d0; border-color: rgba(52, 211, 153, 0.35); }
    .chip.pink, .badge.pink { color: #f5d0fe; border-color: rgba(232, 121, 249, 0.35); }
    .chip.rose, .badge.rose { color: #fecdd3; border-color: rgba(251, 113, 133, 0.35); }
    .dot {
      width: 8px;
      height: 8px;
      border-radius: 999px;
      background: var(--green);
      box-shadow: 0 0 12px var(--green);
    }
    .controls {
      display: grid;
      grid-template-columns: minmax(220px, 1.2fr) repeat(5, minmax(126px, 0.5fr)) auto;
      gap: 10px;
      align-items: end;
      padding: 14px 22px;
      border-bottom: 1px solid var(--line);
      background: rgba(3, 7, 18, 0.52);
    }
    .field {
      min-width: 0;
      display: grid;
      gap: 5px;
    }
    .label {
      font-size: 10px;
      color: var(--muted);
    }
    .field input, .field select {
      min-height: 40px;
      width: 100%;
      padding: 0 10px;
      outline: none;
    }
    .field input:focus, .field select:focus {
      border-color: var(--cyan);
      box-shadow: 0 0 0 3px rgba(34, 211, 238, 0.1);
    }
    .segmented {
      min-height: 40px;
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 4px;
      padding: 4px;
      border-radius: 8px;
      border: 1px solid var(--line);
      background: rgba(2, 6, 23, 0.72);
    }
    .segmented button {
      border: 0;
      min-height: 30px;
      border-radius: 6px;
      padding: 0 8px;
      background: transparent;
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
    }
    .segmented button.active {
      color: #06111f;
      background: linear-gradient(135deg, var(--cyan), var(--gold));
    }
    .content {
      min-width: 0;
      padding: 22px;
    }
    .hero {
      position: relative;
      min-height: 300px;
      overflow: hidden;
      border: 1px solid rgba(34, 211, 238, 0.28);
      border-radius: 12px;
      background:
        linear-gradient(90deg, rgba(2, 6, 23, 0.92) 0%, rgba(2, 6, 23, 0.72) 50%, rgba(2, 6, 23, 0.38) 100%),
        url("assets/second-brain-enrichment-hero.png") center right / cover no-repeat;
      box-shadow: var(--shadow);
      padding: clamp(18px, 4vw, 34px);
      display: grid;
      align-content: end;
    }
    .hero h3 {
      max-width: 900px;
      margin: 0;
      font-size: clamp(32px, 7vw, 78px);
      line-height: 0.93;
      font-weight: 900;
    }
    .hero p {
      max-width: 780px;
      margin: 14px 0 0;
      color: var(--soft);
      font-size: clamp(14px, 1.8vw, 18px);
      line-height: 1.5;
    }
    .hero-strip {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 18px;
    }
    .grid {
      display: grid;
      gap: 14px;
    }
    .grid.cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .grid.cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
    .grid.cols-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
    .section {
      margin-top: 18px;
      padding: 16px;
      border: 1px solid var(--line);
      border-radius: 12px;
      background: rgba(8, 16, 32, 0.64);
      box-shadow: 0 16px 45px rgba(0, 0, 0, 0.18);
    }
    .section-head {
      display: flex;
      justify-content: space-between;
      align-items: end;
      gap: 12px;
      margin-bottom: 12px;
    }
    .section h3, .section h4 {
      margin: 0;
    }
    .section h3 {
      font-size: 22px;
      line-height: 1.1;
    }
    .section h4 {
      font-size: 16px;
      line-height: 1.25;
    }
    .card, .record, .stat-card {
      border: 1px solid rgba(148, 163, 184, 0.22);
      border-radius: 10px;
      background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.035), rgba(255, 255, 255, 0.012)),
        rgba(15, 23, 42, 0.7);
      box-shadow: 0 12px 34px rgba(0, 0, 0, 0.17);
      min-width: 0;
    }
    .card, .stat-card { padding: 14px; }
    .stat-card strong {
      display: block;
      font-size: clamp(25px, 4vw, 42px);
      line-height: 1;
    }
    .stat-card span {
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-top: 6px;
      line-height: 1.35;
    }
    .record {
      display: grid;
      gap: 10px;
      padding: 13px;
      transition: border-color 160ms ease, transform 160ms ease, background 160ms ease;
    }
    .record:hover {
      border-color: rgba(34, 211, 238, 0.45);
      background: rgba(15, 23, 42, 0.88);
      transform: translateY(-1px);
    }
    .record-title {
      display: flex;
      gap: 9px;
      justify-content: space-between;
      align-items: start;
      min-width: 0;
    }
    .record-title strong {
      display: block;
      min-width: 0;
      font-size: 15px;
      line-height: 1.22;
      overflow-wrap: anywhere;
    }
    .record-meta {
      color: var(--muted);
      font-size: 10px;
      line-height: 1.4;
      overflow-wrap: anywhere;
    }
    .record p, .card p {
      margin: 0;
      color: var(--soft);
      line-height: 1.48;
      font-size: 13px;
      overflow-wrap: anywhere;
    }
    .tag-row {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .meter {
      display: grid;
      gap: 6px;
    }
    .meter-top {
      display: flex;
      justify-content: space-between;
      gap: 8px;
    }
    .meter-label {
      color: var(--soft);
      font-size: 11px;
    }
    .bar {
      height: 9px;
      overflow: hidden;
      border-radius: 999px;
      background: rgba(148, 163, 184, 0.18);
      border: 1px solid rgba(148, 163, 184, 0.12);
    }
    .fill {
      height: 100%;
      width: var(--value);
      border-radius: inherit;
      background: linear-gradient(90deg, var(--cyan), var(--fuchsia), var(--gold));
    }
    .rank {
      min-width: 42px;
      height: 34px;
      display: inline-grid;
      place-items: center;
      border-radius: 8px;
      color: #04111c;
      font-weight: 900;
      background: linear-gradient(135deg, var(--gold), var(--cyan));
      border: 1px solid rgba(255, 255, 255, 0.2);
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .rank.s { background: linear-gradient(135deg, #fef08a, #22d3ee); }
    .rank.a { background: linear-gradient(135deg, #86efac, #38bdf8); }
    .rank.b { background: linear-gradient(135deg, #c4b5fd, #67e8f9); }
    .rank.c, .rank.d { background: linear-gradient(135deg, #94a3b8, #f0abfc); }
    .media-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
      gap: 14px;
    }
    .media-card {
      overflow: hidden;
      border: 1px solid rgba(148, 163, 184, 0.22);
      border-radius: 10px;
      background: rgba(15, 23, 42, 0.7);
    }
    .media-card img {
      display: block;
      width: 100%;
      aspect-ratio: 16 / 10;
      object-fit: cover;
      background: rgba(2, 6, 23, 0.9);
    }
    .media-card .record { border: 0; border-radius: 0; box-shadow: none; }
    .source-link {
      overflow-wrap: anywhere;
      color: #bfdbfe;
      font-size: 12px;
    }
    .empty {
      padding: 24px;
      border: 1px dashed rgba(148, 163, 184, 0.34);
      border-radius: 10px;
      color: var(--muted);
      background: rgba(15, 23, 42, 0.44);
    }
    .show-more {
      width: 100%;
      min-height: 42px;
      margin-top: 14px;
      border-color: rgba(34, 211, 238, 0.34);
      color: #a5f3fc;
      background: rgba(34, 211, 238, 0.08);
      font-weight: 800;
    }
    .matrix {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 12px;
    }
    .avatar-line {
      min-height: 230px;
      background:
        linear-gradient(180deg, rgba(2, 6, 23, 0.18), rgba(2, 6, 23, 0.78)),
        var(--selected-character-image, url("assets/avatar-lineage-thumbnail.png")) center / cover no-repeat;
    }
    .protocol-line {
      min-height: 230px;
      background:
        linear-gradient(180deg, rgba(2, 6, 23, 0.18), rgba(2, 6, 23, 0.78)),
        url("assets/protocol-spine-thumbnail.png") center / cover no-repeat;
    }
    .mode-switch {
      display: inline-grid;
      grid-template-columns: repeat(2, minmax(98px, 1fr));
      gap: 4px;
      padding: 4px;
      border-radius: 999px;
      border: 1px solid rgba(34, 211, 238, 0.24);
      background: rgba(2, 6, 23, 0.72);
    }
    .mode-switch button {
      min-height: 28px;
      border: 0;
      border-radius: 999px;
      padding: 0 10px;
      background: transparent;
      color: var(--muted);
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .mode-switch button.active {
      color: #05111c;
      background: linear-gradient(135deg, var(--cyan), var(--gold));
    }
    .sound-toggle {
      min-height: 38px;
      padding: 0 12px;
      border-radius: 999px;
      border-color: rgba(148, 163, 184, 0.24);
      color: var(--muted);
      background: rgba(2, 6, 23, 0.72);
      font-size: 11px;
      font-weight: 850;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .sound-toggle.active {
      color: #04111c;
      border-color: rgba(52, 211, 153, 0.45);
      background: linear-gradient(135deg, var(--green), var(--cyan));
      box-shadow: 0 0 24px rgba(52, 211, 153, 0.16);
    }
    .app.presentation {
      grid-template-columns: minmax(0, 1fr);
    }
    .app.presentation .sidebar,
    .app.presentation .controls {
      display: none;
    }
    .app.presentation .topbar {
      background:
        linear-gradient(90deg, rgba(34, 211, 238, 0.12), rgba(251, 191, 36, 0.08), rgba(232, 121, 249, 0.1)),
        rgba(2, 6, 23, 0.86);
      border-bottom-color: rgba(251, 191, 36, 0.22);
    }
    .app.presentation .content {
      padding: 16px;
    }
    .presentation-shell {
      width: min(1600px, 100%);
      margin: 0 auto;
      display: grid;
      gap: 14px;
    }
    .game-tabs {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      padding: 8px;
      border: 1px solid rgba(148, 163, 184, 0.18);
      border-radius: 12px;
      background: rgba(2, 6, 23, 0.68);
    }
    .game-tabs button {
      min-height: 38px;
      border-radius: 8px;
      padding: 0 13px;
      border-color: rgba(148, 163, 184, 0.22);
      color: var(--soft);
      background: linear-gradient(180deg, rgba(15, 23, 42, 0.88), rgba(2, 6, 23, 0.74));
      font-weight: 850;
    }
    .game-tabs button.active {
      color: #05111c;
      border-color: rgba(251, 191, 36, 0.55);
      background: linear-gradient(135deg, var(--cyan), var(--gold));
      box-shadow: 0 0 28px rgba(34, 211, 238, 0.16);
    }
    .mode-switch button,
    .sound-toggle,
    .game-tabs button,
    .game-list-row,
    .proof-chip-big,
    .proof-step,
    .tree-branch,
    .graph-node,
    .slot-card,
    .inventory-item,
    .skill-highlight-row,
    .proof-layer-row,
    .proof-flow-step,
    .profile-run-card,
    .profile-section-card,
    .profile-observation-card,
    .profile-voice-card,
    .rank-medal {
      transition: transform 180ms ease, border-color 180ms ease, background 180ms ease, box-shadow 180ms ease, filter 180ms ease;
    }
    .mode-switch button:hover,
    .sound-toggle:hover,
    .game-tabs button:hover,
    .game-list-row:hover,
    .proof-chip-big:hover,
    .proof-step:hover,
    .tree-branch:hover,
    .graph-node:hover,
    .slot-card:hover,
    .inventory-item:hover,
    .skill-highlight-row:hover,
    .proof-layer-row:hover,
    .proof-flow-step:hover,
    .profile-run-card:hover,
    .profile-section-card:hover,
    .profile-observation-card:hover,
    .profile-voice-card:hover {
      transform: translateY(-2px);
      border-color: rgba(34, 211, 238, 0.58);
      box-shadow: 0 0 26px rgba(34, 211, 238, 0.12), inset 0 0 18px rgba(34, 211, 238, 0.05);
      filter: saturate(1.12);
    }
    .mode-switch button:focus-visible,
    .sound-toggle:focus-visible,
    .game-tabs button:focus-visible,
    .nav-button:focus-visible,
    .segmented button:focus-visible {
      outline: 2px solid var(--gold);
      outline-offset: 2px;
    }
    .game-frame {
      position: relative;
      overflow: hidden;
      border: 1px solid rgba(251, 191, 36, 0.28);
      border-radius: 14px;
      background:
        linear-gradient(90deg, rgba(255, 255, 255, 0.035) 1px, transparent 1px),
        linear-gradient(0deg, rgba(255, 255, 255, 0.025) 1px, transparent 1px),
        radial-gradient(circle at 50% 10%, rgba(34, 211, 238, 0.14), transparent 28rem),
        linear-gradient(145deg, rgba(6, 12, 24, 0.96), rgba(11, 16, 28, 0.96));
      background-size: 30px 30px, 30px 30px, auto, auto;
      box-shadow: 0 24px 80px rgba(0, 0, 0, 0.42), inset 0 0 80px rgba(251, 191, 36, 0.035);
      animation: panelWake 420ms ease both;
    }
    .game-frame:before {
      content: "";
      position: absolute;
      inset: 0;
      pointer-events: none;
      background: repeating-linear-gradient(0deg, rgba(255,255,255,0.028) 0, rgba(255,255,255,0.028) 1px, transparent 1px, transparent 5px);
      mix-blend-mode: screen;
      opacity: 0.5;
    }
    .game-frame:after {
      content: "";
      position: absolute;
      z-index: 0;
      top: -35%;
      left: -20%;
      width: 140%;
      height: 34%;
      pointer-events: none;
      background: linear-gradient(90deg, transparent, rgba(34, 211, 238, 0.08), rgba(251, 191, 36, 0.05), transparent);
      transform: rotate(-7deg);
      animation: sweepLine 8s linear infinite;
    }
    .game-panel {
      position: relative;
      z-index: 1;
      padding: clamp(14px, 2vw, 22px);
      animation: panelRise 360ms ease both;
    }
    .game-hero-grid {
      display: grid;
      grid-template-columns: minmax(260px, 340px) minmax(0, 1fr) minmax(260px, 360px);
      gap: 14px;
      align-items: stretch;
    }
    .portrait-card, .game-card, .game-stat, .slot-card, .proof-node-card {
      border: 1px solid rgba(148, 163, 184, 0.24);
      border-radius: 10px;
      background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.045), rgba(255, 255, 255, 0.015)),
        rgba(8, 16, 32, 0.78);
      box-shadow: inset 0 0 28px rgba(34, 211, 238, 0.035), 0 14px 38px rgba(0, 0, 0, 0.24);
    }
    .portrait-card {
      min-height: 520px;
      display: grid;
      grid-template-rows: minmax(260px, 1fr) auto auto auto;
      overflow: hidden;
    }
    .portrait-card.model-card {
      min-height: 650px;
      grid-template-rows: minmax(470px, 1fr) auto auto auto;
    }
    .portrait-art {
      position: relative;
      min-height: 320px;
      background:
        linear-gradient(180deg, rgba(2, 6, 23, 0.08), rgba(2, 6, 23, 0.58)),
        var(--selected-character-image, url("hapa-character-sheet-game-mock-04-mobile-passport.png")) center 12% / cover no-repeat;
      border-bottom: 1px solid rgba(34, 211, 238, 0.28);
      animation: portraitDrift 9s ease-in-out infinite;
    }
    .portrait-art.model-stage {
      min-height: 500px;
      isolation: isolate;
      display: grid;
      place-items: stretch;
      background:
        radial-gradient(circle at 50% 18%, rgba(34, 211, 238, 0.18), transparent 34%),
        linear-gradient(180deg, rgba(2, 6, 23, 0.08), rgba(2, 6, 23, 0.74)),
        var(--selected-character-image, url("hapa-character-sheet-game-mock-04-mobile-passport.png")) center 12% / cover no-repeat;
    }
    .character-model-video {
      position: absolute;
      inset: 0;
      z-index: 0;
      width: 100%;
      height: 100%;
      object-fit: cover;
      object-position: center 43%;
      filter: saturate(1.08) contrast(1.06) brightness(0.94);
      background: rgba(2, 6, 23, 0.86);
    }
    .portrait-art:before {
      content: "";
      position: absolute;
      inset: 0;
      z-index: 1;
      background:
        linear-gradient(90deg, rgba(34, 211, 238, 0.1) 1px, transparent 1px),
        linear-gradient(0deg, rgba(232, 121, 249, 0.08) 1px, transparent 1px);
      background-size: 18px 18px;
      opacity: 0.18;
      animation: holoGrid 5s linear infinite;
    }
    .portrait-art:after {
      content: "";
      position: absolute;
      inset: 18px;
      z-index: 2;
      border: 1px solid rgba(34, 211, 238, 0.36);
      border-radius: 10px;
      box-shadow: inset 0 0 32px rgba(34, 211, 238, 0.16);
    }
    .model-hud {
      position: absolute;
      inset: 20px;
      z-index: 3;
      pointer-events: none;
      display: grid;
      align-content: space-between;
      gap: 12px;
    }
    .model-hud-row {
      display: flex;
      justify-content: space-between;
      gap: 8px;
      align-items: center;
    }
    .model-status-chip,
    .model-class-chip {
      display: inline-flex;
      align-items: center;
      gap: 7px;
      min-height: 30px;
      padding: 6px 9px;
      border-radius: 7px;
      border: 1px solid rgba(34, 211, 238, 0.34);
      background: rgba(2, 6, 23, 0.72);
      color: var(--soft);
      font-size: 10px;
      font-weight: 900;
      letter-spacing: 0;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      box-shadow: 0 0 22px rgba(34, 211, 238, 0.1);
    }
    .model-status-chip:before {
      content: "";
      width: 7px;
      aspect-ratio: 1;
      border-radius: 999px;
      background: var(--green);
      box-shadow: 0 0 14px var(--green);
    }
    .model-class-chip {
      justify-self: start;
      color: #fff7cc;
      border-color: rgba(251, 191, 36, 0.36);
    }
    .model-rank-chip {
      color: #04111c;
      border-color: rgba(251, 191, 36, 0.62);
      background: linear-gradient(135deg, rgba(34, 211, 238, 0.9), rgba(251, 191, 36, 0.92));
      box-shadow: 0 0 28px rgba(251, 191, 36, 0.16);
    }
    .model-rank-chip:before {
      display: none;
    }
    .model-reticle {
      position: absolute;
      z-index: 3;
      left: 50%;
      top: 50%;
      width: 72px;
      aspect-ratio: 1;
      transform: translate(-50%, -50%);
      border: 1px solid rgba(34, 211, 238, 0.26);
      border-radius: 999px;
      opacity: 0.72;
      box-shadow: 0 0 26px rgba(34, 211, 238, 0.1);
      animation: modelReticle 4.8s linear infinite;
      pointer-events: none;
    }
    .model-reticle:before,
    .model-reticle:after {
      content: "";
      position: absolute;
      left: 50%;
      top: -16px;
      bottom: -16px;
      width: 1px;
      background: linear-gradient(180deg, transparent, rgba(34, 211, 238, 0.42), transparent);
      transform: translateX(-50%);
    }
    .model-reticle:after {
      inset: 50% -16px auto;
      width: auto;
      height: 1px;
      transform: translateY(-50%);
      background: linear-gradient(90deg, transparent, rgba(251, 191, 36, 0.34), transparent);
    }
    .class-plate {
      padding: 14px;
      border-top: 1px solid rgba(251, 191, 36, 0.22);
      background: rgba(2, 6, 23, 0.78);
    }
    .class-plate strong {
      display: block;
      color: var(--cyan);
      font-size: 24px;
      line-height: 1.05;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .class-plate span {
      color: var(--soft);
      font-size: 12px;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .identity-strip {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 1px;
      background: rgba(148, 163, 184, 0.18);
    }
    .identity-strip div {
      padding: 10px;
      background: rgba(2, 6, 23, 0.82);
    }
    .character-rank-console {
      position: relative;
      overflow: hidden;
      display: grid;
      gap: 10px;
      padding: 12px;
      border-top: 1px solid rgba(34, 211, 238, 0.22);
      background:
        radial-gradient(circle at 20% 20%, rgba(34, 211, 238, 0.12), transparent 10rem),
        radial-gradient(circle at 88% 80%, rgba(251, 191, 36, 0.1), transparent 9rem),
        rgba(2, 6, 23, 0.88);
    }
    .character-rank-console:before {
      content: "";
      position: absolute;
      inset: 0;
      background:
        linear-gradient(90deg, rgba(34, 211, 238, 0.08) 1px, transparent 1px),
        linear-gradient(0deg, rgba(232, 121, 249, 0.05) 1px, transparent 1px);
      background-size: 18px 18px;
      opacity: 0.45;
      pointer-events: none;
      animation: holoGrid 8s linear infinite;
    }
    .character-rank-console > * {
      position: relative;
      z-index: 1;
    }
    .character-rank-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
    }
    .character-rank-head strong {
      display: block;
      color: var(--cyan);
      font-size: 13px;
      line-height: 1.05;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .character-rank-head span {
      color: var(--muted);
      font-size: 9px;
      line-height: 1.2;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .character-rank-seal {
      min-width: 48px;
      min-height: 42px;
      display: grid;
      place-items: center;
      border-radius: 10px;
      border: 1px solid rgba(251, 191, 36, 0.48);
      color: #04111c;
      font-size: 18px;
      font-weight: 950;
      background: linear-gradient(135deg, var(--cyan), var(--fuchsia), var(--gold));
      box-shadow: 0 0 24px rgba(34, 211, 238, 0.15);
      animation: gemGlow 3.2s ease-in-out infinite;
    }
    .character-rank-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 7px;
    }
    .character-rank-stat {
      min-height: 66px;
      padding: 8px;
      border-radius: 8px;
      border: 1px solid rgba(148, 163, 184, 0.18);
      background: rgba(2, 6, 23, 0.56);
    }
    .character-rank-stat strong {
      display: block;
      color: #fff7cc;
      font-size: 19px;
      line-height: 1;
    }
    .character-rank-stat span {
      display: block;
      margin-top: 5px;
      color: var(--muted);
      font-size: 9px;
      line-height: 1.22;
      text-transform: uppercase;
      overflow-wrap: anywhere;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .character-rank-meter {
      height: 4px;
      margin-top: 7px;
      border-radius: 999px;
      overflow: hidden;
      background: rgba(148, 163, 184, 0.18);
    }
    .character-rank-meter i {
      display: block;
      width: var(--value, 0%);
      height: 100%;
      border-radius: inherit;
      background: linear-gradient(90deg, var(--cyan), var(--gold));
      box-shadow: 0 0 16px rgba(34, 211, 238, 0.24);
      animation: chargeBar 620ms ease both;
    }
    .character-rank-row {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 8px;
      align-items: center;
      min-height: 34px;
      padding: 7px 8px;
      border-radius: 8px;
      border: 1px solid rgba(148, 163, 184, 0.16);
      background: rgba(15, 23, 42, 0.48);
      color: var(--soft);
      text-align: left;
      font: inherit;
      cursor: pointer;
    }
    .character-rank-row:hover {
      border-color: rgba(34, 211, 238, 0.46);
      box-shadow: 0 0 20px rgba(34, 211, 238, 0.1);
    }
    .character-rank-row strong {
      display: block;
      color: var(--soft);
      font-size: 11px;
      line-height: 1.18;
      overflow-wrap: anywhere;
    }
    .character-rank-row span {
      display: block;
      margin-top: 3px;
      color: var(--muted);
      font-size: 9px;
      line-height: 1.2;
      text-transform: uppercase;
      overflow-wrap: anywhere;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .character-rank-row em {
      color: #fff7cc;
      font-size: 10px;
      font-style: normal;
      font-weight: 950;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .game-title {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 14px;
      align-items: center;
      margin-bottom: 14px;
    }
    .game-title h3 {
      margin: 0;
      font-size: clamp(42px, 7vw, 92px);
      line-height: 0.9;
      font-weight: 950;
      text-transform: uppercase;
      text-shadow: 0 0 34px rgba(34, 211, 238, 0.16);
      animation: titleResolve 680ms ease both;
    }
    .game-title p {
      margin: 10px 0 0;
      max-width: 880px;
      color: var(--soft);
      line-height: 1.45;
    }
    .rank-medal {
      position: relative;
      overflow: hidden;
      width: 124px;
      aspect-ratio: 1;
      display: grid;
      place-items: center;
      border-radius: 18px;
      border: 1px solid rgba(251, 191, 36, 0.45);
      color: #fff7cc;
      background:
        radial-gradient(circle, rgba(251, 191, 36, 0.23), rgba(2, 6, 23, 0.8) 68%),
        rgba(15, 23, 42, 0.74);
      font-size: 56px;
      font-weight: 950;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      box-shadow: 0 0 44px rgba(251, 191, 36, 0.16);
      animation: medalPulse 2.8s ease-in-out infinite;
    }
    .rank-medal:after {
      content: "";
      position: absolute;
      inset: -40%;
      background: linear-gradient(115deg, transparent 42%, rgba(255,255,255,0.42) 49%, transparent 56%);
      transform: translateX(-50%);
      animation: medalGlint 4.4s ease-in-out infinite;
    }
    .game-stats {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
    }
    .game-stat {
      padding: 12px;
      min-height: 110px;
      display: grid;
      gap: 8px;
      align-content: start;
      animation: staggerIn 420ms ease both;
    }
    .game-stat:nth-child(2) { animation-delay: 45ms; }
    .game-stat:nth-child(3) { animation-delay: 90ms; }
    .game-stat:nth-child(4) { animation-delay: 135ms; }
    .game-stat:nth-child(5) { animation-delay: 180ms; }
    .game-stat:nth-child(6) { animation-delay: 225ms; }
    .game-stat:nth-child(7) { animation-delay: 270ms; }
    .game-stat:nth-child(8) { animation-delay: 315ms; }
    .game-stat .fill,
    .meter .fill {
      transform-origin: left center;
      animation: chargeBar 900ms cubic-bezier(.2,.9,.2,1) both;
    }
    .game-stat-head {
      display: grid;
      grid-template-columns: 42px minmax(0, 1fr);
      gap: 9px;
      align-items: center;
    }
    .stat-icon {
      position: relative;
      width: 38px;
      aspect-ratio: 1;
      display: grid;
      place-items: center;
      overflow: hidden;
      border-radius: 10px;
      border: 1px solid rgba(34, 211, 238, 0.34);
      background:
        radial-gradient(circle at 35% 30%, rgba(255,255,255,0.28), transparent 13px),
        linear-gradient(135deg, rgba(34, 211, 238, 0.28), rgba(232, 121, 249, 0.12)),
        rgba(2, 6, 23, 0.74);
      box-shadow: 0 0 24px rgba(34, 211, 238, 0.12), inset 0 0 20px rgba(34, 211, 238, 0.07);
      animation: statIconPulse 3.4s ease-in-out infinite;
    }
    .stat-icon:before {
      content: "";
      position: absolute;
      inset: 4px;
      border-radius: 8px;
      border: 1px solid rgba(255,255,255,0.12);
      background:
        linear-gradient(90deg, transparent 0 44%, rgba(255,255,255,0.18) 45% 48%, transparent 49%),
        linear-gradient(0deg, transparent 0 44%, rgba(255,255,255,0.12) 45% 48%, transparent 49%);
      opacity: 0.55;
    }
    .stat-icon:after {
      content: "";
      position: absolute;
      width: 6px;
      aspect-ratio: 1;
      border-radius: 999px;
      background: var(--gold);
      box-shadow: 0 0 14px var(--gold);
      animation: statIconOrbit 2.8s linear infinite;
    }
    .stat-icon i {
      position: relative;
      z-index: 1;
      display: block;
      width: 19px;
      aspect-ratio: 1;
      border: 2px solid var(--cyan);
      border-radius: 5px;
      box-shadow: inset 0 0 12px rgba(34, 211, 238, 0.22), 0 0 12px rgba(34, 211, 238, 0.18);
    }
    .stat-signal { border-color: rgba(34, 211, 238, 0.48); }
    .stat-signal i {
      width: 24px;
      height: 14px;
      border-width: 0 0 2px;
      border-radius: 0;
      background: linear-gradient(90deg, transparent 0 12%, var(--cyan) 13% 16%, transparent 17% 36%, var(--gold) 37% 41%, transparent 42% 65%, var(--fuchsia) 66% 70%, transparent 71%);
      box-shadow: 0 0 14px rgba(34, 211, 238, 0.2);
    }
    .stat-forge i {
      transform: rotate(45deg);
      border-color: var(--gold);
      border-radius: 4px;
    }
    .stat-stewardship i {
      width: 20px;
      height: 24px;
      border-color: var(--green);
      border-radius: 10px 10px 6px 6px;
      clip-path: polygon(50% 0, 96% 22%, 82% 86%, 50% 100%, 18% 86%, 4% 22%);
    }
    .stat-lore i {
      width: 20px;
      height: 24px;
      border-color: var(--fuchsia);
      border-radius: 3px;
      box-shadow: -5px 0 0 rgba(232, 121, 249, 0.2), 5px 0 0 rgba(34, 211, 238, 0.16);
    }
    .stat-tempo i {
      width: 23px;
      height: 23px;
      border-color: var(--gold);
      border-radius: 50%;
      background: conic-gradient(from 20deg, rgba(251,191,36,0.55), transparent 42%, rgba(34,211,238,0.55), transparent 72%);
    }
    .stat-craft i {
      width: 21px;
      height: 21px;
      border-color: var(--cyan);
      border-radius: 4px;
      transform: rotate(12deg);
    }
    .stat-craft i:after {
      content: "";
      position: absolute;
      width: 14px;
      height: 2px;
      left: 10px;
      top: 14px;
      background: var(--gold);
      transform: rotate(-42deg);
      box-shadow: 0 0 8px rgba(251, 191, 36, 0.35);
    }
    .stat-communion i {
      width: 24px;
      height: 18px;
      border-color: var(--fuchsia);
      border-radius: 999px;
      box-shadow: -8px 0 0 rgba(34,211,238,0.18), 8px 0 0 rgba(251,191,36,0.16), 0 0 14px rgba(232,121,249,0.2);
    }
    .game-stat-top {
      display: flex;
      justify-content: space-between;
      gap: 8px;
      color: var(--soft);
      font-size: 12px;
      font-weight: 850;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .game-stat-value {
      margin-top: 10px;
      font-size: 34px;
      line-height: 1;
      font-weight: 950;
      color: #fff;
    }
    .game-proof-strip {
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 10px;
      margin-top: 14px;
    }
    .proof-chip-big {
      min-height: 72px;
      padding: 12px;
      border-radius: 10px;
      border: 1px solid rgba(34, 211, 238, 0.24);
      background: rgba(2, 6, 23, 0.72);
      animation: staggerIn 420ms ease both;
    }
    .proof-chip-big:nth-child(2) { animation-delay: 50ms; }
    .proof-chip-big:nth-child(3) { animation-delay: 100ms; }
    .proof-chip-big:nth-child(4) { animation-delay: 150ms; }
    .proof-chip-big:nth-child(5) { animation-delay: 200ms; }
    .proof-chip-big strong {
      display: block;
      font-size: 25px;
      line-height: 1;
    }
    .proof-chip-big span {
      display: block;
      margin-top: 5px;
      color: var(--muted);
      font-size: 10px;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .second-brain-mini {
      position: relative;
      min-height: 430px;
      margin-top: 14px;
      padding: 14px;
      overflow: hidden;
      border-radius: 10px;
      border: 1px solid rgba(34, 211, 238, 0.25);
      background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.012)),
        radial-gradient(circle at 50% 0%, rgba(34, 211, 238, 0.12), transparent 42%),
        rgba(8, 16, 32, 0.76);
      box-shadow: inset 0 0 34px rgba(34, 211, 238, 0.045), 0 16px 42px rgba(0, 0, 0, 0.22);
    }
    .second-brain-mini:before {
      content: "";
      position: absolute;
      inset: 0;
      pointer-events: none;
      background:
        linear-gradient(90deg, rgba(34, 211, 238, 0.08) 1px, transparent 1px),
        linear-gradient(0deg, rgba(232, 121, 249, 0.055) 1px, transparent 1px);
      background-size: 16px 16px;
      opacity: 0.28;
      animation: holoGrid 7s linear infinite;
    }
    .second-brain-mini:after {
      content: "";
      position: absolute;
      left: -18%;
      right: -18%;
      top: 28%;
      height: 1px;
      pointer-events: none;
      background: linear-gradient(90deg, transparent, rgba(34, 211, 238, 0.7), rgba(251, 191, 36, 0.35), transparent);
      animation: sweepLine 9s linear infinite;
      opacity: 0.6;
    }
    .second-brain-mini > * {
      position: relative;
      z-index: 1;
    }
    .sb-head {
      display: flex;
      align-items: start;
      justify-content: space-between;
      gap: 12px;
    }
    .sb-head h4 {
      margin: 0;
      color: var(--cyan);
      font-size: 18px;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .sb-status {
      display: flex;
      flex-wrap: wrap;
      justify-content: flex-end;
      gap: 6px;
    }
    .sb-status span,
    .sb-pane-title,
    .sb-node em,
    .sb-topic-chip em {
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      text-transform: uppercase;
    }
    .sb-status span {
      min-height: 24px;
      display: inline-grid;
      place-items: center;
      padding: 0 8px;
      border-radius: 999px;
      border: 1px solid rgba(34, 211, 238, 0.32);
      background: rgba(2, 6, 23, 0.66);
      color: #a7f3d0;
      font-size: 10px;
    }
    .sb-grid {
      display: grid;
      grid-template-columns: minmax(190px, 0.88fr) minmax(250px, 1.12fr) minmax(210px, 0.95fr);
      gap: 12px;
      margin-top: 12px;
    }
    .sb-pane,
    .sb-radar {
      min-width: 0;
      border-radius: 10px;
      border: 1px solid rgba(148, 163, 184, 0.18);
      background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.035), rgba(255, 255, 255, 0.01)),
        rgba(2, 6, 23, 0.56);
      box-shadow: inset 0 0 24px rgba(34, 211, 238, 0.035);
    }
    .sb-pane {
      padding: 10px;
      display: grid;
      align-content: start;
      gap: 9px;
    }
    .sb-pane-title {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      color: var(--gold);
      font-size: 11px;
    }
    .sb-pane-title span:last-child {
      color: var(--muted);
      font-size: 10px;
    }
    .sb-source-list,
    .sb-layer-list {
      display: grid;
      gap: 7px;
    }
    .sb-source-row {
      position: relative;
      min-height: 47px;
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 8px;
      align-items: center;
      overflow: hidden;
      padding: 8px 9px 10px;
      border-radius: 8px;
      border: 1px solid rgba(148, 163, 184, 0.15);
      background: rgba(8, 16, 32, 0.64);
    }
    .sb-source-row strong,
    .sb-layer-row strong,
    .sb-topic-chip strong {
      color: var(--text);
      font-size: 12px;
      line-height: 1.15;
      overflow-wrap: anywhere;
    }
    .sb-source-row em,
    .sb-layer-row span,
    .sb-topic-chip em {
      display: block;
      margin-top: 3px;
      color: var(--muted);
      font-size: 10px;
      font-style: normal;
      line-height: 1.2;
    }
    .sb-source-row b {
      color: #fff7cc;
      font-size: 12px;
    }
    .sb-source-row i {
      position: absolute;
      left: 0;
      bottom: 0;
      width: var(--value);
      height: 3px;
      background: linear-gradient(90deg, var(--cyan), var(--fuchsia), var(--gold));
      box-shadow: 0 0 16px rgba(34, 211, 238, 0.22);
    }
    .sb-radar {
      position: relative;
      min-height: 322px;
      overflow: hidden;
      background:
        radial-gradient(circle at center, rgba(34, 211, 238, 0.14) 0 2px, transparent 3px),
        radial-gradient(circle at center, transparent 0 26%, rgba(34, 211, 238, 0.16) 27%, transparent 28%, transparent 46%, rgba(232, 121, 249, 0.14) 47%, transparent 48%, transparent 66%, rgba(251, 191, 36, 0.12) 67%, transparent 68%),
        rgba(2, 6, 23, 0.62);
    }
    .sb-radar:before {
      content: "";
      position: absolute;
      inset: 15%;
      border-radius: 50%;
      border: 1px dashed rgba(34, 211, 238, 0.25);
      animation: proofRingSpin 18s linear infinite;
    }
    .sb-radar:after {
      content: "";
      position: absolute;
      inset: 0;
      background: conic-gradient(from 45deg, rgba(34, 211, 238, 0.22), transparent 18%, transparent 100%);
      mix-blend-mode: screen;
      opacity: 0.52;
      animation: proofRingSpin 10s linear infinite;
    }
    .sb-radar-core {
      position: absolute;
      z-index: 2;
      left: 50%;
      top: 50%;
      width: 96px;
      aspect-ratio: 1;
      transform: translate(-50%, -50%);
      display: grid;
      place-items: center;
      border-radius: 50%;
      border: 1px solid rgba(251, 191, 36, 0.48);
      background: radial-gradient(circle, rgba(34, 211, 238, 0.3), rgba(2, 6, 23, 0.86));
      color: #fff7cc;
      text-align: center;
      font-size: 13px;
      font-weight: 950;
      box-shadow: 0 0 40px rgba(34, 211, 238, 0.18);
    }
    .sb-node {
      position: absolute;
      z-index: 3;
      left: var(--x);
      top: var(--y);
      width: 88px;
      min-height: 54px;
      transform: translate(-50%, -50%);
      padding: 8px;
      border-radius: 9px;
      border: 1px solid rgba(34, 211, 238, 0.25);
      background: rgba(2, 6, 23, 0.78);
      box-shadow: 0 0 22px rgba(34, 211, 238, 0.12);
      animation: nodePulse 4s ease-in-out infinite;
    }
    .sb-node strong {
      display: block;
      color: var(--cyan);
      font-size: 11px;
      line-height: 1.1;
      text-transform: uppercase;
    }
    .sb-node em {
      display: block;
      margin-top: 4px;
      color: var(--text);
      font-size: 11px;
      font-style: normal;
    }
    .sb-topic-cloud {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      max-height: 122px;
      overflow: auto;
      padding-right: 3px;
    }
    .sb-topic-chip {
      min-width: 0;
      max-width: 100%;
      display: grid;
      gap: 2px;
      padding: 7px 8px;
      border-radius: 8px;
      border: 1px solid rgba(232, 121, 249, 0.28);
      background: rgba(15, 23, 42, 0.58);
    }
    .sb-layer-row {
      min-height: 36px;
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      align-items: center;
      gap: 8px;
      padding: 7px 8px;
      border-radius: 8px;
      border: 1px solid rgba(148, 163, 184, 0.14);
      background: rgba(2, 6, 23, 0.48);
    }
    .sb-layer-row i {
      width: 9px;
      aspect-ratio: 1;
      display: inline-block;
      margin-right: 6px;
      border-radius: 50%;
      vertical-align: middle;
      box-shadow: 0 0 12px currentColor;
    }
    .sb-footer {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 8px;
      margin-top: 12px;
    }
    .sb-footer div {
      min-height: 54px;
      padding: 9px;
      border-radius: 9px;
      border: 1px solid rgba(251, 191, 36, 0.22);
      background: rgba(2, 6, 23, 0.58);
    }
    .sb-footer strong {
      display: block;
      color: #fff;
      font-size: 18px;
      line-height: 1;
    }
    .sb-footer span {
      display: block;
      margin-top: 5px;
      color: var(--gold);
      font-size: 10px;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .game-side-stack {
      display: grid;
      gap: 10px;
    }
    .image-manager {
      overflow: hidden;
    }
    .image-preview {
      position: relative;
      min-height: 180px;
      border-radius: 10px;
      border: 1px solid rgba(34, 211, 238, 0.24);
      overflow: hidden;
      background:
        linear-gradient(180deg, rgba(2, 6, 23, 0.08), rgba(2, 6, 23, 0.68)),
        var(--selected-character-image, url("hapa-character-sheet-game-mock-04-mobile-passport.png")) center 15% / cover no-repeat;
      box-shadow: inset 0 0 28px rgba(34, 211, 238, 0.08);
    }
    .image-preview:after {
      content: "";
      position: absolute;
      inset: 12px;
      border: 1px solid rgba(251, 191, 36, 0.28);
      border-radius: 8px;
      pointer-events: none;
    }
    .source-links {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 7px;
      margin-top: 10px;
    }
    .source-links a,
    .image-source-filters button,
    .image-actions button,
    .image-file-label {
      min-height: 34px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border-radius: 8px;
      border: 1px solid rgba(148, 163, 184, 0.22);
      background: rgba(2, 6, 23, 0.58);
      color: var(--soft);
      font-size: 10px;
      font-weight: 850;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .source-links a:hover,
    .image-source-filters button:hover,
    .image-actions button:hover,
    .image-file-label:hover {
      color: #fff7cc;
      border-color: rgba(34, 211, 238, 0.48);
      box-shadow: 0 0 20px rgba(34, 211, 238, 0.1);
    }
    .image-source-filters {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 7px;
      margin-top: 10px;
    }
    .image-source-filters button.active {
      color: #04111c;
      border-color: rgba(251, 191, 36, 0.48);
      background: linear-gradient(135deg, var(--cyan), var(--gold));
    }
    .image-source-list {
      display: grid;
      gap: 7px;
      max-height: 245px;
      overflow: auto;
      padding-right: 4px;
      margin-top: 10px;
    }
    .image-source-row {
      display: grid;
      grid-template-columns: 44px minmax(0, 1fr) auto;
      gap: 8px;
      align-items: center;
      min-height: 54px;
      padding: 7px;
      border-radius: 9px;
      border: 1px solid rgba(148, 163, 184, 0.16);
      background: rgba(2, 6, 23, 0.55);
      color: var(--soft);
      text-align: left;
    }
    .image-source-row.selected {
      border-color: rgba(251, 191, 36, 0.58);
      background:
        linear-gradient(90deg, rgba(34, 211, 238, 0.1), rgba(251, 191, 36, 0.08)),
        rgba(2, 6, 23, 0.72);
      box-shadow: inset 3px 0 0 var(--gold);
    }
    .image-source-thumb {
      width: 44px;
      aspect-ratio: 1;
      border-radius: 8px;
      border: 1px solid rgba(34, 211, 238, 0.28);
      background:
        linear-gradient(180deg, rgba(2, 6, 23, 0.06), rgba(2, 6, 23, 0.5)),
        var(--source-image, var(--selected-character-image, url("hapa-character-sheet-game-mock-04-mobile-passport.png"))) center / cover no-repeat;
    }
    .image-source-row strong {
      display: block;
      font-size: 12px;
      line-height: 1.2;
      overflow-wrap: anywhere;
    }
    .image-source-row span {
      display: block;
      margin-top: 3px;
      color: var(--muted);
      font-size: 10px;
      line-height: 1.25;
      overflow-wrap: anywhere;
    }
    .image-source-row em {
      color: #fff7cc;
      font-size: 10px;
      font-style: normal;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .character-model-panel .model-callout {
      display: grid;
      grid-template-columns: 48px minmax(0, 1fr);
      gap: 9px;
      align-items: center;
      min-height: 58px;
      padding: 8px;
      margin-bottom: 10px;
      border-radius: 9px;
      border: 1px solid rgba(251, 191, 36, 0.3);
      background:
        linear-gradient(90deg, rgba(34, 211, 238, 0.1), rgba(251, 191, 36, 0.08)),
        rgba(2, 6, 23, 0.58);
    }
    .model-callout-thumb {
      width: 48px;
      aspect-ratio: 9 / 14;
      border-radius: 8px;
      border: 1px solid rgba(34, 211, 238, 0.32);
      background:
        linear-gradient(180deg, rgba(2, 6, 23, 0.02), rgba(2, 6, 23, 0.48)),
        var(--model-poster, var(--selected-character-image, url("hapa-character-sheet-game-mock-04-mobile-passport.png"))) center / cover no-repeat;
      box-shadow: 0 0 18px rgba(34, 211, 238, 0.11);
    }
    .model-callout strong {
      display: block;
      color: var(--text);
      font-size: 12px;
      line-height: 1.18;
      overflow-wrap: anywhere;
    }
    .model-callout span {
      display: block;
      margin-top: 4px;
      color: var(--muted);
      font-size: 10px;
      line-height: 1.25;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .image-actions {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 7px;
      margin-top: 10px;
    }
    .image-actions input {
      min-height: 34px;
      min-width: 0;
      padding: 0 9px;
      font-size: 12px;
    }
    .image-file-input {
      position: absolute;
      width: 1px;
      height: 1px;
      opacity: 0;
      pointer-events: none;
    }
    .image-apply-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 7px;
      margin-top: 7px;
    }
    .game-card {
      padding: 13px;
    }
    .game-card h4 {
      margin: 0 0 10px;
      font-size: 16px;
      text-transform: uppercase;
      color: var(--cyan);
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .profile-shell {
      display: grid;
      gap: 14px;
    }
    .profile-brief {
      display: grid;
      grid-template-columns: minmax(0, 1.45fr) minmax(280px, 0.55fr);
      gap: 14px;
      align-items: stretch;
    }
    .profile-title-card {
      position: relative;
      overflow: hidden;
      min-height: 260px;
      display: grid;
      align-content: end;
      isolation: isolate;
      background:
        radial-gradient(circle at 14% 16%, rgba(34, 211, 238, 0.2), transparent 18rem),
        radial-gradient(circle at 82% 72%, rgba(232, 121, 249, 0.14), transparent 18rem),
        linear-gradient(135deg, rgba(8, 16, 32, 0.92), rgba(2, 6, 23, 0.88));
    }
    .profile-title-card:before {
      content: "";
      position: absolute;
      inset: 18px;
      border: 1px solid rgba(34, 211, 238, 0.2);
      border-radius: 10px;
      pointer-events: none;
      box-shadow: inset 0 0 36px rgba(34, 211, 238, 0.08);
      z-index: 1;
    }
    .profile-video-backdrop {
      position: absolute;
      inset: 0;
      z-index: 0;
      overflow: hidden;
      border-radius: 10px;
      background: #020617;
      pointer-events: none;
      box-shadow: inset 0 -180px 180px rgba(2, 6, 23, 0.64);
    }
    .profile-video-poster {
      position: absolute;
      inset: 0;
      background-size: cover;
      background-position: center;
      opacity: 0.92;
      filter: saturate(1.14) contrast(1.08) brightness(0.82);
      transform: scale(1.01);
    }
    .profile-video-backdrop video {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      object-fit: cover;
      object-position: center;
      opacity: 0;
      filter: saturate(1.16) contrast(1.1) brightness(0.86);
      transform: scale(1.015);
    }
    .profile-bg-video.is-primary {
      opacity: 0.82;
      animation: profileVideoCyclePrimary 20s linear infinite;
    }
    .profile-bg-video.is-secondary {
      animation: profileVideoCycleSecondary 20s linear infinite;
    }
    .profile-video-backdrop:after {
      content: "";
      position: absolute;
      inset: 0;
      background:
        linear-gradient(180deg, rgba(2, 6, 23, 0.04), rgba(2, 6, 23, 0.28) 48%, rgba(2, 6, 23, 0.86)),
        linear-gradient(90deg, rgba(2, 6, 23, 0.1), rgba(2, 6, 23, 0.34) 52%, rgba(2, 6, 23, 0.1)),
        radial-gradient(circle at 18% 18%, rgba(34, 211, 238, 0.12), transparent 28rem),
        radial-gradient(circle at 78% 70%, rgba(232, 121, 249, 0.12), transparent 28rem),
        repeating-linear-gradient(0deg, rgba(255,255,255,0.035), rgba(255,255,255,0.035) 1px, transparent 1px, transparent 4px);
    }
    .profile-title-card > :not(.profile-video-backdrop) {
      position: relative;
      z-index: 2;
    }
    .profile-title-card > .profile-video-backdrop {
      position: absolute;
      inset: 0;
      z-index: 0;
    }
    .profile-title-card h3 {
      margin: 0;
      font-size: clamp(42px, 7vw, 86px);
      line-height: 0.9;
      text-transform: uppercase;
      font-weight: 950;
      text-shadow: 0 0 34px rgba(34, 211, 238, 0.16);
    }
    .profile-title-card p {
      max-width: 980px;
      margin: 12px 0 0;
      color: var(--soft);
      font-size: 15px;
      line-height: 1.5;
    }
    .profile-kpi-grid,
    .profile-section-grid,
    .profile-run-grid,
    .profile-lower-grid {
      display: grid;
      gap: 10px;
    }
    .profile-kpi-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .profile-section-grid {
      grid-template-columns: repeat(4, minmax(0, 1fr));
    }
    .profile-run-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .profile-lower-grid {
      grid-template-columns: minmax(260px, 0.85fr) minmax(0, 1.15fr) minmax(280px, 0.9fr);
    }
    .profile-run-card,
    .profile-section-card,
    .profile-observation-card,
    .profile-voice-card {
      position: relative;
      overflow: hidden;
      padding: 12px;
      border-radius: 10px;
      border: 1px solid rgba(148, 163, 184, 0.2);
      background:
        linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.012)),
        rgba(2, 6, 23, 0.58);
    }
    .profile-run-card:before,
    .profile-observation-card:before {
      content: "";
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      width: 3px;
      background: linear-gradient(180deg, var(--cyan), var(--fuchsia), var(--gold));
      opacity: 0.9;
    }
    .profile-run-card strong,
    .profile-section-card strong,
    .profile-observation-card strong,
    .profile-voice-card strong {
      display: block;
      color: #f8fafc;
      line-height: 1.2;
      overflow-wrap: anywhere;
    }
    .profile-run-card p,
    .profile-section-card p,
    .profile-observation-card p,
    .profile-voice-card p {
      margin: 8px 0 0;
      color: var(--soft);
      font-size: 12px;
      line-height: 1.45;
    }
    .profile-section-card {
      min-height: 128px;
      display: grid;
      align-content: space-between;
    }
    .profile-section-card em,
    .profile-run-card em,
    .profile-observation-card em {
      color: #fff7cc;
      font-size: 10px;
      font-style: normal;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .profile-ledger-scroll {
      max-height: 640px;
      overflow: auto;
      padding-right: 4px;
      scrollbar-color: var(--cyan) rgba(2, 6, 23, 0.7);
    }
    .profile-status-strip {
      display: flex;
      flex-wrap: wrap;
      gap: 7px;
      margin-top: 12px;
    }
    .profile-adapter {
      border-color: rgba(251, 191, 36, 0.28);
      background:
        radial-gradient(circle at 90% 10%, rgba(251, 191, 36, 0.12), transparent 13rem),
        rgba(8, 16, 32, 0.78);
    }
    .profile-adapter .game-list-row {
      border-color: rgba(251, 191, 36, 0.22);
    }
    .profile-voice-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
    }
    .profile-voice-card {
      min-height: 160px;
      animation: staggerIn 420ms ease both;
    }
    .profile-voice-card:nth-child(2) { animation-delay: 60ms; }
    .profile-voice-card:nth-child(3) { animation-delay: 120ms; }
    .profile-voice-card:nth-child(4) { animation-delay: 180ms; }
    .game-list {
      display: grid;
      gap: 7px;
    }
    .game-list-row {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 8px;
      align-items: center;
      min-height: 34px;
      padding: 7px 9px;
      border-radius: 7px;
      border: 1px solid rgba(148, 163, 184, 0.18);
      background: rgba(2, 6, 23, 0.54);
      color: var(--soft);
      font-size: 12px;
    }
    .game-list-row.selected,
    .proof-chip-big.selected,
    .slot-card.selected {
      border-color: rgba(251, 191, 36, 0.58);
      background:
        linear-gradient(90deg, rgba(34, 211, 238, 0.12), rgba(251, 191, 36, 0.09)),
        rgba(2, 6, 23, 0.74);
      box-shadow: inset 3px 0 0 var(--gold), 0 0 30px rgba(251, 191, 36, 0.12);
    }
    .game-list-row.interactive {
      cursor: pointer;
    }
    .interactive[data-passport-detail] {
      cursor: pointer;
    }
    .game-list-row.interactive:hover strong {
      color: #fff7cc;
    }
    .game-list-row.compact {
      grid-template-columns: 32px minmax(0, 1fr) auto;
      min-height: 46px;
    }
    .game-list-row.compact span,
    .game-list-row.compact strong {
      overflow-wrap: anywhere;
    }
    .game-list-row.compact > span > strong {
      display: block;
      line-height: 1.22;
    }
    .game-list-row.compact > span > span {
      display: block;
      margin-top: 3px;
      color: var(--muted);
      font-size: 10px;
      line-height: 1.25;
    }
    .skill-highlight-row {
      display: grid;
      grid-template-columns: 34px minmax(0, 1fr) auto;
      gap: 8px;
      align-items: center;
      min-height: 42px;
      padding: 6px 8px;
      border-radius: 8px;
      border: 1px solid rgba(148, 163, 184, 0.18);
      background: rgba(2, 6, 23, 0.54);
      color: var(--soft);
      animation: staggerIn 420ms ease both;
    }
    .skill-highlight-row strong {
      display: block;
      font-size: 12px;
      line-height: 1.22;
      overflow-wrap: anywhere;
    }
    .skill-highlight-row span span {
      display: block;
      margin-top: 3px;
      color: var(--muted);
      font-size: 10px;
      line-height: 1.25;
      overflow-wrap: anywhere;
    }
    .skill-highlight-row em {
      color: #fff7cc;
      font-style: normal;
      font-size: 11px;
      font-weight: 950;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .codex-meta-strip {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
      margin-top: 12px;
    }
    .codex-inspector {
      min-height: 650px;
      display: grid;
      align-content: start;
      gap: 12px;
      overflow: hidden;
    }
    .codex-inspector p {
      max-height: 190px;
      overflow: auto;
      padding-right: 4px;
    }
    .codex-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      max-height: 112px;
      overflow: auto;
      padding: 2px 4px 2px 0;
    }
    .codex-tags .badge {
      max-width: 100%;
      min-height: auto;
      white-space: normal;
      line-height: 1.28;
      overflow-wrap: anywhere;
      border-radius: 8px;
    }
    .codex-mini-list {
      max-height: 170px;
      overflow: auto;
      padding-right: 4px;
    }
    .codex-inventory-grid {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 14px;
    }
    .inventory-panel {
      min-height: 360px;
      overflow: hidden;
    }
    .inventory-head {
      display: flex;
      align-items: start;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 10px;
    }
    .inventory-scroll {
      max-height: 420px;
      overflow: auto;
      display: grid;
      gap: 10px;
      padding-right: 4px;
    }
    .inventory-group {
      display: grid;
      gap: 7px;
      padding: 9px;
      border-radius: 10px;
      border: 1px solid rgba(148, 163, 184, 0.15);
      background: rgba(2, 6, 23, 0.38);
    }
    .inventory-group-title {
      display: flex;
      justify-content: space-between;
      gap: 8px;
      color: var(--gold);
      font-size: 10px;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .inventory-item {
      display: grid;
      grid-template-columns: 32px minmax(0, 1fr) auto;
      gap: 8px;
      align-items: center;
      min-height: 44px;
      padding: 6px 8px;
      border-radius: 8px;
      border: 1px solid rgba(148, 163, 184, 0.16);
      background: rgba(15, 23, 42, 0.46);
      color: var(--soft);
      text-align: left;
      font: inherit;
      cursor: pointer;
    }
    .inventory-item:hover,
    .inventory-item.selected {
      border-color: rgba(34, 211, 238, 0.5);
      background:
        linear-gradient(90deg, rgba(34, 211, 238, 0.1), rgba(232, 121, 249, 0.06)),
        rgba(15, 23, 42, 0.66);
    }
    .inventory-item:focus-visible {
      outline: 2px solid var(--gold);
      outline-offset: 2px;
    }
    .inventory-item strong {
      display: block;
      color: var(--soft);
      font-size: 12px;
      line-height: 1.22;
      overflow-wrap: anywhere;
    }
    .inventory-item span {
      display: block;
      margin-top: 3px;
      color: var(--muted);
      font-size: 10px;
      line-height: 1.25;
      overflow-wrap: anywhere;
    }
    .inventory-item em {
      color: #fff7cc;
      font-size: 10px;
      font-style: normal;
      font-weight: 900;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .quality-panel {
      position: relative;
      overflow: hidden;
      min-height: 420px;
    }
    .quality-panel:before {
      content: "";
      position: absolute;
      inset: 0;
      background:
        radial-gradient(circle at 18% 28%, rgba(34, 211, 238, 0.14), transparent 18rem),
        radial-gradient(circle at 78% 70%, rgba(232, 121, 249, 0.1), transparent 18rem),
        linear-gradient(90deg, rgba(34, 211, 238, 0.05) 1px, transparent 1px),
        linear-gradient(0deg, rgba(251, 191, 36, 0.035) 1px, transparent 1px);
      background-size: auto, auto, 28px 28px, 28px 28px;
      opacity: 0.72;
      pointer-events: none;
      animation: holoGrid 14s linear infinite;
    }
    .quality-panel > * {
      position: relative;
      z-index: 1;
    }
    .quality-head {
      display: flex;
      align-items: start;
      justify-content: space-between;
      gap: 14px;
      margin-bottom: 12px;
    }
    .quality-head p {
      max-width: 980px;
      margin: 4px 0 0;
      color: var(--soft);
      font-size: 12px;
      line-height: 1.4;
    }
    .quality-grid {
      display: grid;
      grid-template-columns: minmax(260px, 360px) minmax(420px, 1fr) minmax(280px, 360px);
      gap: 12px;
      align-items: stretch;
    }
    .quality-ladder,
    .quality-pair-list {
      display: grid;
      gap: 7px;
      max-height: 348px;
      overflow: auto;
      padding-right: 4px;
    }
    .quality-row,
    .quality-pair-row {
      display: grid;
      grid-template-columns: 34px minmax(0, 1fr) auto;
      gap: 8px;
      align-items: center;
      min-height: 50px;
      padding: 7px 8px;
      border-radius: 8px;
      border: 1px solid rgba(148, 163, 184, 0.18);
      background: rgba(2, 6, 23, 0.58);
      color: var(--soft);
      text-align: left;
      font: inherit;
      animation: staggerIn 420ms ease both;
    }
    .quality-row:hover,
    .quality-pair-row:hover,
    .quality-row.selected {
      border-color: rgba(251, 191, 36, 0.58);
      background:
        linear-gradient(90deg, rgba(34, 211, 238, 0.11), rgba(251, 191, 36, 0.08)),
        rgba(2, 6, 23, 0.76);
    }
    .quality-rank-token {
      width: 30px;
      aspect-ratio: 1;
      display: grid;
      place-items: center;
      border-radius: 8px;
      border: 1px solid rgba(251, 191, 36, 0.4);
      background:
        radial-gradient(circle at 40% 30%, rgba(255, 247, 204, 0.28), transparent 14px),
        linear-gradient(135deg, rgba(34, 211, 238, 0.18), rgba(232, 121, 249, 0.12)),
        rgba(2, 6, 23, 0.74);
      color: #fff7cc;
      font-size: 10px;
      font-weight: 950;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      animation: gemGlow 3.4s ease-in-out infinite;
    }
    .quality-row strong,
    .quality-pair-row strong {
      display: block;
      color: #eef6ff;
      font-size: 12px;
      line-height: 1.2;
      overflow-wrap: anywhere;
    }
    .quality-row span span,
    .quality-pair-row span span {
      display: block;
      margin-top: 3px;
      color: var(--muted);
      font-size: 10px;
      line-height: 1.25;
      overflow-wrap: anywhere;
    }
    .quality-score-pill {
      min-width: 52px;
      display: inline-flex;
      justify-content: center;
      padding: 4px 7px;
      border-radius: 999px;
      border: 1px solid rgba(34, 211, 238, 0.34);
      color: #fff7cc;
      background: rgba(2, 6, 23, 0.68);
      font-size: 10px;
      font-weight: 950;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .quality-meter {
      grid-column: 2 / -1;
      height: 4px;
      border-radius: 999px;
      overflow: hidden;
      background: rgba(148, 163, 184, 0.16);
    }
    .quality-meter i {
      display: block;
      width: var(--value, 0%);
      height: 100%;
      border-radius: inherit;
      background: linear-gradient(90deg, var(--cyan), var(--fuchsia), var(--gold));
      box-shadow: 0 0 16px rgba(34, 211, 238, 0.28);
      animation: chargeBar 620ms ease both;
    }
    .quality-scatter {
      position: relative;
      min-height: 350px;
      border-radius: 12px;
      border: 1px solid rgba(34, 211, 238, 0.22);
      background:
        linear-gradient(90deg, rgba(34, 211, 238, 0.08) 1px, transparent 1px),
        linear-gradient(0deg, rgba(232, 121, 249, 0.06) 1px, transparent 1px),
        radial-gradient(circle at 50% 50%, rgba(34, 211, 238, 0.12), transparent 16rem),
        rgba(2, 6, 23, 0.58);
      background-size: 36px 36px, 36px 36px, auto, auto;
      overflow: hidden;
    }
    .quality-axis {
      position: absolute;
      color: var(--muted);
      font-size: 10px;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      pointer-events: none;
    }
    .quality-axis.x { left: 14px; right: 14px; bottom: 10px; display: flex; justify-content: space-between; }
    .quality-axis.y { left: 12px; top: 12px; writing-mode: vertical-rl; transform: rotate(180deg); }
    .quality-crosshair {
      position: absolute;
      inset: 48px;
      border-left: 1px solid rgba(34, 211, 238, 0.2);
      border-bottom: 1px solid rgba(251, 191, 36, 0.18);
      pointer-events: none;
    }
    .quality-dot {
      position: absolute;
      left: var(--x, 50%);
      top: var(--y, 50%);
      width: var(--s, 28px);
      aspect-ratio: 1;
      display: grid;
      place-items: center;
      border: 1px solid rgba(251, 191, 36, 0.56);
      border-radius: 999px;
      background:
        radial-gradient(circle at 35% 25%, rgba(255,255,255,0.42), transparent 11px),
        linear-gradient(135deg, var(--cyan), var(--fuchsia), var(--gold));
      color: #030712;
      font-size: 9px;
      font-weight: 950;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      transform: translate(-50%, -50%);
      box-shadow: 0 0 24px rgba(34, 211, 238, 0.2), 0 0 18px rgba(251, 191, 36, 0.14);
      cursor: pointer;
      animation: nodePulse 3.8s ease-in-out infinite;
    }
    .quality-dot:hover,
    .quality-dot.selected {
      z-index: 4;
      border-color: #fff7cc;
      box-shadow: 0 0 34px rgba(251, 191, 36, 0.34), 0 0 22px rgba(34, 211, 238, 0.24);
    }
    .quality-preview {
      margin-top: 14px;
      padding: 12px;
      border-radius: 10px;
      border: 1px solid rgba(34, 211, 238, 0.22);
      background: rgba(2, 6, 23, 0.56);
    }
    .quality-preview-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 8px;
      margin-top: 10px;
    }
    .quality-preview-tile {
      min-height: 72px;
      padding: 9px;
      border-radius: 8px;
      border: 1px solid rgba(148, 163, 184, 0.18);
      background: rgba(15, 23, 42, 0.48);
    }
    .quality-preview-tile strong {
      display: block;
      color: #fff7cc;
      font-size: 20px;
      line-height: 1;
    }
    .quality-preview-tile span {
      display: block;
      margin-top: 5px;
      color: var(--muted);
      font-size: 10px;
      line-height: 1.2;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .proof-chain {
      display: grid;
      grid-template-columns: repeat(6, minmax(0, 1fr));
      gap: 8px;
      margin-top: 14px;
    }
    .proof-step {
      padding: 10px;
      border-radius: 9px;
      border: 1px solid rgba(251, 191, 36, 0.2);
      background: rgba(2, 6, 23, 0.65);
      text-align: center;
      animation: staggerIn 420ms ease both;
    }
    .proof-step:nth-child(2) { animation-delay: 55ms; }
    .proof-step:nth-child(3) { animation-delay: 110ms; }
    .proof-step:nth-child(4) { animation-delay: 165ms; }
    .proof-step:nth-child(5) { animation-delay: 220ms; }
    .proof-step:nth-child(6) { animation-delay: 275ms; }
    .proof-step strong {
      display: block;
      color: var(--gold);
      font-size: 12px;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .proof-step span {
      display: block;
      margin-top: 5px;
      color: var(--soft);
      font-size: 16px;
      font-weight: 900;
    }
    .proof-step em {
      display: block;
      margin-top: 3px;
      color: var(--muted);
      font-size: 9px;
      font-style: normal;
      line-height: 1.15;
      text-transform: uppercase;
      overflow-wrap: anywhere;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .codex-grid {
      display: grid;
      grid-template-columns: 320px minmax(0, 1fr) 360px;
      gap: 14px;
    }
    .codex-shell {
      display: grid;
      gap: 14px;
    }
    .skill-tree {
      position: relative;
      min-height: 650px;
      display: grid;
      place-items: center;
      overflow: hidden;
    }
    .skill-tree:before {
      content: "";
      position: absolute;
      inset: 48px;
      border-radius: 50%;
      border: 1px solid rgba(34, 211, 238, 0.18);
      box-shadow: 0 0 0 80px rgba(34, 211, 238, 0.025), 0 0 0 160px rgba(232, 121, 249, 0.018);
    }
    .tree-core {
      position: relative;
      z-index: 2;
      width: 140px;
      aspect-ratio: 1;
      display: grid;
      place-items: center;
      border-radius: 50%;
      border: 1px solid rgba(251, 191, 36, 0.45);
      background: radial-gradient(circle, rgba(34, 211, 238, 0.28), rgba(2, 6, 23, 0.8));
      font-weight: 950;
      color: #fff;
      text-align: center;
      box-shadow: 0 0 50px rgba(34, 211, 238, 0.22);
      animation: corePulse 3s ease-in-out infinite;
    }
    .tree-core.skill-loop-core {
      width: min(260px, 44%);
      min-width: 210px;
      aspect-ratio: 9 / 14;
      overflow: hidden;
      border-radius: 18px;
      border-color: rgba(251, 191, 36, 0.52);
      background:
        radial-gradient(circle at 50% 12%, rgba(34, 211, 238, 0.24), transparent 30%),
        rgba(2, 6, 23, 0.88);
      box-shadow: 0 0 52px rgba(34, 211, 238, 0.18), 0 0 34px rgba(251, 191, 36, 0.12);
    }
    .skill-loop-video {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      object-fit: cover;
      object-position: center;
      filter: saturate(1.08) contrast(1.05) brightness(0.94);
    }
    .skill-loop-core:before {
      content: "";
      position: absolute;
      inset: 0;
      z-index: 1;
      background:
        linear-gradient(180deg, rgba(2, 6, 23, 0.08), rgba(2, 6, 23, 0.16) 54%, rgba(2, 6, 23, 0.76)),
        linear-gradient(90deg, rgba(34, 211, 238, 0.12) 1px, transparent 1px),
        linear-gradient(0deg, rgba(232, 121, 249, 0.08) 1px, transparent 1px);
      background-size: auto, 18px 18px, 18px 18px;
      pointer-events: none;
      animation: holoGrid 6s linear infinite;
    }
    .skill-loop-core:after {
      content: "";
      position: absolute;
      inset: 12px;
      z-index: 2;
      border: 1px solid rgba(34, 211, 238, 0.38);
      border-radius: 14px;
      box-shadow: inset 0 0 28px rgba(34, 211, 238, 0.12);
      pointer-events: none;
    }
    .skill-loop-hud {
      position: absolute;
      inset: auto 12px 12px;
      z-index: 3;
      display: grid;
      gap: 6px;
      text-align: left;
      pointer-events: none;
    }
    .skill-loop-hud strong {
      display: block;
      color: #fff7cc;
      font-size: 14px;
      line-height: 1.1;
      text-transform: uppercase;
      overflow-wrap: anywhere;
      text-shadow: 0 0 18px rgba(2, 6, 23, 0.9);
    }
    .skill-loop-hud span {
      display: block;
      color: var(--soft);
      font-size: 10px;
      line-height: 1.22;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .skill-loop-chip-row {
      position: absolute;
      inset: 12px 12px auto;
      z-index: 3;
      display: flex;
      justify-content: space-between;
      gap: 8px;
      pointer-events: none;
    }
    .skill-loop-chip {
      min-height: 28px;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 5px 8px;
      border-radius: 7px;
      border: 1px solid rgba(34, 211, 238, 0.34);
      background: rgba(2, 6, 23, 0.7);
      color: var(--soft);
      font-size: 9px;
      font-weight: 900;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .skill-loop-chip:first-child:before {
      content: "";
      width: 7px;
      aspect-ratio: 1;
      border-radius: 999px;
      background: var(--green);
      box-shadow: 0 0 14px var(--green);
    }
    .tree-branch {
      position: absolute;
      z-index: 3;
      width: 170px;
      min-height: 78px;
      display: grid;
      grid-template-columns: 44px minmax(0, 1fr);
      gap: 10px;
      align-items: center;
      padding: 10px;
      border-radius: 10px;
      border: 1px solid rgba(148, 163, 184, 0.25);
      background: rgba(8, 16, 32, 0.86);
      color: inherit;
      text-align: left;
      font: inherit;
      box-shadow: 0 0 28px rgba(0, 0, 0, 0.28);
      animation: branchIdle 4.2s ease-in-out infinite;
      cursor: pointer;
    }
    .tree-branch.selected {
      border-color: rgba(251, 191, 36, 0.58);
      background:
        linear-gradient(135deg, rgba(34, 211, 238, 0.13), rgba(251, 191, 36, 0.09)),
        rgba(8, 16, 32, 0.94);
      box-shadow: 0 0 36px rgba(251, 191, 36, 0.14), inset 0 0 22px rgba(34, 211, 238, 0.06);
    }
    .tree-branch.selected strong {
      color: #fff7cc;
    }
    .tree-branch:focus-visible {
      outline: 2px solid var(--gold);
      outline-offset: 2px;
    }
    .tree-branch strong {
      display: block;
      color: var(--cyan);
      font-size: 12px;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      overflow-wrap: anywhere;
    }
    .tree-branch span {
      color: var(--soft);
      font-size: 11px;
      line-height: 1.35;
      overflow-wrap: anywhere;
    }
    .family-thumb {
      width: 42px;
      aspect-ratio: 1;
      display: inline-block;
      flex: 0 0 auto;
      border-radius: 8px;
      border: 1px solid rgba(34, 211, 238, 0.35);
      background-image: url("hapa-character-sheet-codex-family-sprites.png");
      background-size: 400% 200%;
      background-position: var(--sprite-x, 0%) var(--sprite-y, 0%);
      background-repeat: no-repeat;
      box-shadow: 0 0 24px rgba(34, 211, 238, 0.14), inset 0 0 0 1px rgba(255,255,255,0.08);
      filter: saturate(1.08) contrast(1.06);
    }
    .family-thumb.small {
      width: 32px;
      border-radius: 7px;
    }
    .family-thumb.animated {
      position: relative;
      overflow: hidden;
      animation: familyThumbGlow 3.2s ease-in-out infinite;
    }
    .family-thumb.animated:after {
      content: "";
      position: absolute;
      inset: -20%;
      background: linear-gradient(115deg, transparent 35%, rgba(255,255,255,0.35) 49%, transparent 62%);
      transform: translateX(-120%);
      animation: thumbSweep 3.8s ease-in-out infinite;
    }
    .family-thumb.node {
      display: grid;
      place-items: center;
      background-image:
        radial-gradient(circle at 30% 25%, rgba(255,255,255,0.44), transparent 18px),
        linear-gradient(135deg, var(--cyan), var(--fuchsia), var(--gold));
      color: #04111c;
      font-size: 10px;
      font-weight: 950;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .node-thumb {
      --node-a: var(--cyan);
      --node-b: var(--fuchsia);
      --node-c: var(--gold);
      width: 54px;
      aspect-ratio: 1;
      position: relative;
      display: inline-grid;
      place-items: center;
      flex: 0 0 auto;
      overflow: hidden;
      border-radius: 12px;
      border: 1px solid color-mix(in srgb, var(--node-a) 56%, transparent);
      background:
        radial-gradient(circle at 30% 20%, color-mix(in srgb, var(--node-a) 34%, transparent), transparent 30%),
        radial-gradient(circle at 72% 74%, color-mix(in srgb, var(--node-c) 28%, transparent), transparent 34%),
        linear-gradient(135deg, rgba(2, 6, 23, 0.94), color-mix(in srgb, var(--node-b) 22%, rgba(2, 6, 23, 0.84)));
      box-shadow: 0 0 28px color-mix(in srgb, var(--node-a) 20%, transparent), inset 0 0 0 1px rgba(255,255,255,0.08);
      isolation: isolate;
    }
    .node-thumb.small {
      width: 32px;
      border-radius: 8px;
    }
    .node-thumb.large {
      width: 68px;
      border-radius: 14px;
    }
    .node-thumb.animated {
      animation: nodeThumbGlow 3.8s ease-in-out infinite;
    }
    .node-thumb:before {
      content: "";
      position: absolute;
      inset: 8px;
      border: 1px solid color-mix(in srgb, var(--node-a) 52%, transparent);
      border-radius: 8px;
      transform: rotate(45deg);
      opacity: 0.76;
      box-shadow: inset 0 0 16px color-mix(in srgb, var(--node-a) 18%, transparent);
      animation: nodeThumbOrbit 6.2s linear infinite;
    }
    .node-thumb:after {
      content: "";
      position: absolute;
      inset: -30%;
      background: linear-gradient(115deg, transparent 38%, rgba(255,255,255,0.32) 49%, transparent 60%);
      transform: translateX(-120%);
      animation: thumbSweep 4.8s ease-in-out infinite;
      opacity: 0.74;
    }
    .node-thumb-mark {
      position: absolute;
      width: 34%;
      height: 34%;
      border: 2px solid color-mix(in srgb, var(--node-c) 80%, white 8%);
      border-radius: 3px;
      z-index: 1;
      opacity: 0.92;
      box-shadow: 0 0 18px color-mix(in srgb, var(--node-c) 26%, transparent);
    }
    .node-thumb strong {
      position: relative;
      z-index: 2;
      color: #ecfeff;
      font-size: 12px;
      font-weight: 950;
      letter-spacing: 0;
      text-shadow: 0 2px 0 rgba(0,0,0,0.45), 0 0 16px color-mix(in srgb, var(--node-a) 44%, transparent);
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .node-thumb.small strong {
      font-size: 9px;
    }
    .node-thumb.large strong {
      font-size: 15px;
    }
    .node-thumb.node-type-existing-node {
      --node-a: #22d3ee;
      --node-b: #2563eb;
      --node-c: #a7f3d0;
    }
    .node-thumb.node-type-proposed-node {
      --node-a: #f472b6;
      --node-b: #7c3aed;
      --node-c: #fbbf24;
    }
    .node-thumb.node-type-hapa-node {
      --node-a: #34d399;
      --node-b: #0891b2;
      --node-c: #67e8f9;
    }
    .node-thumb.node-type-cymatica-node {
      --node-a: #fbbf24;
      --node-b: #db2777;
      --node-c: #c4b5fd;
    }
    .node-thumb.node-type-node-map {
      --node-a: #38bdf8;
      --node-b: #14b8a6;
      --node-c: #f0abfc;
    }
    .node-thumb.node-type-proposed-node .node-thumb-mark {
      clip-path: polygon(50% 0, 100% 50%, 50% 100%, 0 50%);
      border-radius: 0;
    }
    .node-thumb.node-type-hapa-node .node-thumb-mark {
      border-radius: 50%;
    }
    .node-thumb.node-type-cymatica-node .node-thumb-mark {
      transform: rotate(30deg);
      border-radius: 50% 8% 50% 8%;
    }
    .node-thumb.node-type-node-map .node-thumb-mark {
      width: 42%;
      height: 22%;
      border-radius: 10px;
    }
    .tree-branch:nth-child(2) { top: 44px; left: 50%; transform: translateX(-50%); }
    .tree-branch:nth-child(3) { top: 124px; right: 52px; }
    .tree-branch:nth-child(4) { bottom: 140px; right: 72px; }
    .tree-branch:nth-child(5) { bottom: 44px; left: 50%; transform: translateX(-50%); }
    .tree-branch:nth-child(6) { bottom: 140px; left: 72px; }
    .tree-branch:nth-child(7) { top: 124px; left: 52px; }
    .tree-branch:nth-child(8) { top: 300px; left: 32px; }
    .tree-branch:nth-child(9) { top: 300px; right: 32px; }
    .proof-shell {
      display: grid;
      gap: 14px;
    }
    .proof-map-grid {
      display: grid;
      grid-template-columns: minmax(260px, 320px) minmax(0, 1fr) minmax(300px, 390px);
      gap: 14px;
    }
    .constellation {
      position: relative;
      min-height: 720px;
      overflow: hidden;
      border: 1px solid rgba(34, 211, 238, 0.22);
      border-radius: 12px;
      background:
        radial-gradient(circle at 50% 50%, rgba(34, 211, 238, 0.18), transparent 15rem),
        radial-gradient(circle at 20% 25%, rgba(251, 191, 36, 0.1), transparent 18rem),
        rgba(2, 6, 23, 0.72);
    }
    .constellation:before {
      content: "";
      position: absolute;
      inset: 0;
      background-image:
        radial-gradient(circle, rgba(255,255,255,0.7) 1px, transparent 1px),
        linear-gradient(35deg, transparent 48%, rgba(34,211,238,0.14) 49%, rgba(34,211,238,0.14) 51%, transparent 52%);
      background-size: 70px 70px, 180px 180px;
      opacity: 0.28;
    }
    .constellation:after {
      content: "";
      position: absolute;
      inset: 34px;
      border-radius: 50%;
      border: 1px solid rgba(251, 191, 36, 0.16);
      box-shadow: 0 0 0 92px rgba(34, 211, 238, 0.025), 0 0 0 178px rgba(232, 121, 249, 0.018);
      animation: proofRingSpin 18s linear infinite;
      pointer-events: none;
    }
    .proof-edges {
      position: absolute;
      inset: 0;
      z-index: 1;
      width: 100%;
      height: 100%;
      pointer-events: none;
      opacity: 0.78;
    }
    .proof-edges line {
      stroke: rgba(34, 211, 238, 0.25);
      stroke-width: 1.6;
      stroke-dasharray: 6 8;
      vector-effect: non-scaling-stroke;
      animation: edgeFlow 6s linear infinite;
    }
    .proof-edges line.chain {
      stroke: rgba(251, 191, 36, 0.25);
      stroke-width: 2.1;
      stroke-dasharray: 10 9;
    }
    .proof-edges line.selected {
      stroke: rgba(251, 191, 36, 0.78);
      stroke-width: 3;
      filter: drop-shadow(0 0 10px rgba(251, 191, 36, 0.42));
    }
    .proof-spark {
      position: absolute;
      z-index: 1;
      width: 5px;
      aspect-ratio: 1;
      border-radius: 999px;
      background: var(--cyan);
      box-shadow: 0 0 14px var(--cyan);
      opacity: 0.5;
      animation: sparkDrift 7s ease-in-out infinite;
    }
    .proof-spark:nth-of-type(1) { left: 28%; top: 22%; animation-delay: 0.2s; }
    .proof-spark:nth-of-type(2) { left: 72%; top: 24%; animation-delay: 1.1s; background: var(--gold); box-shadow: 0 0 14px var(--gold); }
    .proof-spark:nth-of-type(3) { left: 78%; top: 68%; animation-delay: 2.3s; background: var(--fuchsia); box-shadow: 0 0 14px var(--fuchsia); }
    .proof-spark:nth-of-type(4) { left: 23%; top: 70%; animation-delay: 3.2s; background: var(--green); box-shadow: 0 0 14px var(--green); }
    .graph-core, .graph-node {
      position: absolute;
      z-index: 2;
      display: grid;
      place-items: center;
      text-align: center;
      border-radius: 50%;
      border: 1px solid rgba(34, 211, 238, 0.42);
      background: rgba(8, 16, 32, 0.88);
      box-shadow: 0 0 32px rgba(34, 211, 238, 0.18);
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      text-transform: uppercase;
    }
    .graph-core {
      width: 160px;
      aspect-ratio: 1;
      left: 50%;
      top: 50%;
      transform: translate(-50%, -50%);
      color: #fff;
      font-size: 18px;
      font-weight: 950;
      animation: corePulse 3.2s ease-in-out infinite;
    }
    .graph-node {
      width: 126px;
      aspect-ratio: 1;
      left: var(--x, 50%);
      top: var(--y, 50%);
      transform: translate(-50%, -50%);
      color: var(--soft);
      font-size: 11px;
      padding: 12px;
      font: inherit;
      animation: nodePulse 4.6s ease-in-out infinite;
      cursor: pointer;
    }
    .graph-node.selected {
      color: #fff7cc;
      border-color: rgba(251, 191, 36, 0.76);
      background:
        radial-gradient(circle at 50% 35%, rgba(251, 191, 36, 0.24), transparent 55%),
        rgba(8, 16, 32, 0.94);
      box-shadow: 0 0 42px rgba(251, 191, 36, 0.22), inset 0 0 26px rgba(34, 211, 238, 0.08);
    }
    .graph-node:focus-visible {
      outline: 2px solid var(--gold);
      outline-offset: 3px;
    }
    .graph-node strong {
      display: block;
      color: var(--cyan);
      font-size: 19px;
      margin-top: 4px;
    }
    .graph-node.selected strong {
      color: #fff7cc;
    }
    .graph-node:nth-child(2) { left: 12%; top: 16%; }
    .graph-node:nth-child(3) { left: 48%; top: 8%; }
    .graph-node:nth-child(4) { right: 12%; top: 18%; }
    .graph-node:nth-child(5) { right: 11%; top: 52%; }
    .graph-node:nth-child(6) { right: 30%; bottom: 8%; }
    .graph-node:nth-child(7) { left: 27%; bottom: 8%; }
    .graph-node:nth-child(8) { left: 8%; top: 52%; }
    .graph-node:nth-child(9) { left: 29%; top: 34%; }
    .constellation .graph-node {
      left: var(--x, 50%) !important;
      top: var(--y, 50%) !important;
      right: auto !important;
      bottom: auto !important;
      transform: translate(-50%, -50%);
    }
    .proof-layer-list,
    .proof-example-scroll {
      display: grid;
      gap: 7px;
      max-height: 520px;
      overflow: auto;
      padding-right: 4px;
    }
    .proof-layer-row {
      display: grid;
      grid-template-columns: 34px minmax(0, 1fr) auto;
      gap: 8px;
      align-items: center;
      min-height: 50px;
      padding: 7px 9px;
      border-radius: 9px;
      border: 1px solid rgba(148, 163, 184, 0.18);
      background: rgba(2, 6, 23, 0.56);
      color: var(--soft);
      text-align: left;
      font: inherit;
    }
    .proof-layer-row.selected {
      border-color: rgba(251, 191, 36, 0.58);
      background:
        linear-gradient(90deg, rgba(34, 211, 238, 0.12), rgba(251, 191, 36, 0.08)),
        rgba(2, 6, 23, 0.72);
      box-shadow: inset 3px 0 0 var(--gold);
    }
    .proof-layer-icon {
      width: 32px;
      aspect-ratio: 1;
      display: grid;
      place-items: center;
      border-radius: 8px;
      border: 1px solid rgba(34, 211, 238, 0.3);
      background:
        radial-gradient(circle at 35% 25%, rgba(255,255,255,0.24), transparent 14px),
        linear-gradient(135deg, rgba(34,211,238,0.3), rgba(232,121,249,0.15)),
        rgba(2, 6, 23, 0.7);
      color: #fff7cc;
      font-size: 10px;
      font-weight: 950;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      animation: familyThumbGlow 3.4s ease-in-out infinite;
    }
    .proof-layer-row strong {
      display: block;
      font-size: 12px;
      line-height: 1.2;
      overflow-wrap: anywhere;
    }
    .proof-layer-row span span {
      display: block;
      margin-top: 3px;
      color: var(--muted);
      font-size: 10px;
      line-height: 1.25;
    }
    .proof-layer-row em {
      color: #fff7cc;
      font-style: normal;
      font-size: 11px;
      font-weight: 950;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .proof-inspector {
      min-height: 720px;
      display: grid;
      align-content: start;
      gap: 12px;
      overflow: hidden;
    }
    .proof-inspector p {
      max-height: 160px;
      overflow: auto;
      padding-right: 4px;
    }
    .proof-inspector .example-list {
      max-height: 230px;
      overflow: auto;
      padding-right: 4px;
    }
    .proof-flow-strip {
      display: grid;
      grid-template-columns: repeat(6, minmax(0, 1fr));
      gap: 8px;
    }
    .proof-flow-step {
      min-height: 78px;
      padding: 10px;
      border-radius: 10px;
      border: 1px solid rgba(251, 191, 36, 0.22);
      background: rgba(2, 6, 23, 0.68);
      text-align: left;
      color: var(--soft);
      font: inherit;
      animation: staggerIn 420ms ease both;
    }
    .proof-flow-step.selected {
      border-color: rgba(251, 191, 36, 0.62);
      box-shadow: 0 0 26px rgba(251, 191, 36, 0.12), inset 0 0 18px rgba(34, 211, 238, 0.06);
    }
    .proof-flow-step strong {
      display: block;
      color: var(--gold);
      font-size: 11px;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .proof-flow-step span {
      display: block;
      margin-top: 6px;
      font-size: 17px;
      font-weight: 950;
      color: #fff;
    }
    .proof-flow-step small {
      display: block;
      margin-top: 5px;
      color: var(--muted);
      font-size: 10px;
      line-height: 1.25;
    }
    .proof-comprehensive-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
    }
    .proof-mini-panel {
      min-height: 250px;
      overflow: hidden;
    }
    .proof-mini-panel .game-list {
      max-height: 210px;
      overflow: auto;
      padding-right: 4px;
    }
    .loadout-grid {
      display: grid;
      grid-template-columns: minmax(0, 1.35fr) minmax(340px, 0.65fr);
      gap: 14px;
      align-items: start;
    }
    .loadout-armory {
      display: grid;
      gap: 12px;
      min-height: 720px;
    }
    .loadout-head {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: start;
    }
    .loadout-head p {
      margin: 0;
      max-width: 720px;
      color: var(--soft);
      font-size: 13px;
      line-height: 1.45;
    }
    .loadout-type-filters {
      display: flex;
      flex-wrap: wrap;
      gap: 7px;
    }
    .loadout-type-filter {
      min-height: 34px;
      padding: 0 10px;
      border-radius: 8px;
      border: 1px solid rgba(34, 211, 238, 0.2);
      background: rgba(2, 6, 23, 0.68);
      color: var(--soft);
      font-weight: 900;
      font-size: 11px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      text-transform: uppercase;
    }
    .loadout-type-filter.selected {
      color: #04111c;
      border-color: rgba(251, 191, 36, 0.72);
      background: linear-gradient(135deg, var(--cyan), var(--gold));
      box-shadow: 0 0 24px rgba(34, 211, 238, 0.12);
    }
    .loadout-summary-strip {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 8px;
    }
    .loadout-summary-strip .proof-chip-big {
      min-height: 62px;
    }
    .slot-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(185px, 1fr));
      gap: 10px;
    }
    .loadout-node-grid {
      max-height: 860px;
      overflow: auto;
      padding: 2px 6px 4px 0;
      scrollbar-color: rgba(34,211,238,0.6) rgba(15,23,42,0.7);
    }
    .slot-card {
      min-height: 202px;
      padding: 12px;
      display: grid;
      align-content: space-between;
      gap: 10px;
      width: 100%;
      border-radius: 10px;
      text-align: left;
      color: var(--soft);
      font: inherit;
      animation: staggerIn 420ms ease both;
    }
    .node-slot {
      position: relative;
      overflow: hidden;
      cursor: pointer;
      background:
        linear-gradient(145deg, color-mix(in srgb, var(--node-a, #22d3ee) 12%, transparent), transparent 42%),
        rgba(15, 23, 42, 0.7);
    }
    .node-slot:before {
      content: "";
      position: absolute;
      inset: 0;
      background:
        linear-gradient(90deg, transparent 0 48%, color-mix(in srgb, var(--node-a, #22d3ee) 18%, transparent) 49% 51%, transparent 52%),
        linear-gradient(0deg, transparent 0 48%, rgba(255,255,255,0.04) 49% 51%, transparent 52%);
      background-size: 34px 34px;
      opacity: 0.18;
      pointer-events: none;
    }
    .node-slot:hover {
      transform: translateY(-2px);
      border-color: color-mix(in srgb, var(--node-a, #22d3ee) 52%, transparent);
      box-shadow: 0 16px 44px rgba(0,0,0,0.22), 0 0 30px color-mix(in srgb, var(--node-a, #22d3ee) 14%, transparent);
    }
    .node-slot:focus-visible {
      outline: 2px solid var(--gold);
      outline-offset: 2px;
    }
    .slot-card:nth-child(2) { animation-delay: 45ms; }
    .slot-card:nth-child(3) { animation-delay: 90ms; }
    .slot-card:nth-child(4) { animation-delay: 135ms; }
    .slot-card:nth-child(5) { animation-delay: 180ms; }
    .slot-card:nth-child(6) { animation-delay: 225ms; }
    .node-slot-top {
      position: relative;
      z-index: 1;
      display: flex;
      justify-content: space-between;
      align-items: start;
      gap: 10px;
    }
    .node-slot-body {
      position: relative;
      z-index: 1;
      display: grid;
      gap: 6px;
    }
    .node-slot-body strong {
      display: block;
      color: #eef6ff;
      font-size: 16px;
      line-height: 1.08;
      overflow-wrap: anywhere;
    }
    .node-slot-meter {
      height: 6px;
      overflow: hidden;
      border-radius: 99px;
      background: rgba(148, 163, 184, 0.2);
    }
    .node-slot-meter span {
      display: block;
      width: var(--value, 20%);
      height: 100%;
      border-radius: inherit;
      background: linear-gradient(90deg, var(--node-a, var(--cyan)), var(--gold));
      box-shadow: 0 0 18px color-mix(in srgb, var(--node-a, #22d3ee) 32%, transparent);
    }
    .node-slot-meta {
      position: relative;
      z-index: 1;
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 6px;
    }
    .node-slot-meta span {
      min-height: 30px;
      padding: 6px;
      border-radius: 7px;
      border: 1px solid rgba(148, 163, 184, 0.16);
      background: rgba(2, 6, 23, 0.5);
      color: var(--muted);
      font-size: 10px;
      line-height: 1.1;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .node-slot-meta strong {
      display: block;
      color: #fff7cc;
      font-size: 14px;
      line-height: 1;
    }
    .loadout-inspector {
      min-height: 420px;
    }
    .loadout-inspector .record-title {
      align-items: start;
    }
    .loadout-inspector p {
      max-height: 160px;
      overflow: auto;
      padding-right: 4px;
    }
    .node-inspector-hero {
      display: grid;
      grid-template-columns: 76px minmax(0, 1fr);
      gap: 12px;
      align-items: center;
      margin-bottom: 12px;
      padding: 10px;
      border-radius: 10px;
      border: 1px solid rgba(34, 211, 238, 0.18);
      background: rgba(2, 6, 23, 0.44);
    }
    .node-inspector-hero strong {
      display: block;
      color: #fff;
      line-height: 1.12;
      overflow-wrap: anywhere;
    }
    .node-inspector-hero span {
      display: block;
      margin-top: 4px;
      color: var(--muted);
      font-size: 11px;
      overflow-wrap: anywhere;
    }
    .loadout-side-list {
      max-height: 250px;
      overflow: auto;
      padding-right: 4px;
    }
    .timeline-shell {
      display: grid;
      gap: 14px;
    }
    .timeline-brief {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(280px, 420px);
      gap: 14px;
      align-items: stretch;
    }
    .timeline-title-card {
      position: relative;
      overflow: hidden;
      min-height: 180px;
      background:
        radial-gradient(circle at 18% 30%, rgba(34, 211, 238, 0.2), transparent 22rem),
        radial-gradient(circle at 82% 40%, rgba(251, 191, 36, 0.13), transparent 22rem),
        rgba(15, 23, 42, 0.72);
    }
    .timeline-title-card:before {
      content: "";
      position: absolute;
      inset: 0;
      background:
        linear-gradient(90deg, transparent 0 48%, rgba(34,211,238,0.11) 49% 51%, transparent 52%),
        linear-gradient(0deg, transparent 0 48%, rgba(251,191,36,0.08) 49% 51%, transparent 52%);
      background-size: 42px 42px;
      opacity: 0.26;
      animation: holoGrid 12s linear infinite;
      pointer-events: none;
    }
    .timeline-title-card > * {
      position: relative;
      z-index: 1;
    }
    .timeline-title-card h3 {
      margin: 4px 0 8px;
      font-size: clamp(34px, 5vw, 78px);
      line-height: 0.92;
      text-transform: uppercase;
    }
    .timeline-title-card p {
      max-width: 860px;
      margin: 0;
      color: var(--soft);
      font-size: 15px;
      line-height: 1.45;
    }
    .timeline-kpi-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
    }
    .timeline-era-rail,
    .timeline-layer-rail,
    .timeline-scale-rail {
      display: flex;
      gap: 8px;
      overflow-x: auto;
      padding: 2px 2px 6px;
      scrollbar-color: rgba(34,211,238,0.62) rgba(15,23,42,0.7);
    }
    .timeline-era-card,
    .timeline-layer-card,
    .timeline-scale-card {
      flex: 0 0 230px;
      min-height: 120px;
      padding: 11px;
      border-radius: 10px;
      border: 1px solid rgba(148, 163, 184, 0.2);
      background: rgba(2, 6, 23, 0.62);
      color: var(--soft);
      text-align: left;
      font: inherit;
      position: relative;
      overflow: hidden;
    }
    .timeline-layer-card {
      flex-basis: 190px;
      min-height: 96px;
    }
    .timeline-scale-card {
      flex-basis: 180px;
      min-height: 88px;
    }
    .timeline-era-card:before,
    .timeline-layer-card:before,
    .timeline-scale-card:before {
      content: "";
      position: absolute;
      inset: auto 10px 10px 10px;
      height: 3px;
      border-radius: 99px;
      background: linear-gradient(90deg, var(--cyan), var(--fuchsia), var(--gold));
      opacity: 0.7;
    }
    .timeline-era-card.selected,
    .timeline-layer-card.selected,
    .timeline-scale-card.selected {
      border-color: rgba(251, 191, 36, 0.68);
      box-shadow: inset 3px 0 0 var(--gold), 0 0 30px rgba(251, 191, 36, 0.12);
      background:
        linear-gradient(135deg, rgba(34, 211, 238, 0.13), rgba(251, 191, 36, 0.08)),
        rgba(2, 6, 23, 0.8);
    }
    .timeline-era-card strong,
    .timeline-layer-card strong,
    .timeline-scale-card strong {
      display: block;
      color: #fff;
      font-size: 14px;
      line-height: 1.15;
      text-transform: uppercase;
    }
    .timeline-era-card span,
    .timeline-layer-card span,
    .timeline-scale-card span {
      display: block;
      margin-top: 5px;
      color: var(--muted);
      font-size: 10px;
      line-height: 1.3;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .timeline-era-card p {
      margin: 8px 0 0;
      color: var(--soft);
      font-size: 11px;
      line-height: 1.35;
    }
    .timeline-scale-card p {
      margin: 7px 0 0;
      color: var(--soft);
      font-size: 10px;
      line-height: 1.3;
    }
    .timeline-daily-brief {
      display: grid;
      grid-template-columns: minmax(0, 1.2fr) repeat(4, minmax(140px, 1fr));
      gap: 8px;
      padding: 10px;
      border-radius: 10px;
      border: 1px solid rgba(34, 211, 238, 0.2);
      background:
        linear-gradient(90deg, rgba(34, 211, 238, 0.1), rgba(251, 191, 36, 0.04)),
        rgba(2, 6, 23, 0.58);
    }
    .timeline-daily-brief.active {
      border-color: rgba(251, 191, 36, 0.52);
      box-shadow: 0 0 34px rgba(34, 211, 238, 0.09), inset 0 0 26px rgba(251, 191, 36, 0.05);
    }
    .timeline-daily-copy {
      min-width: 0;
    }
    .timeline-daily-copy strong {
      display: block;
      color: var(--cyan);
      font-size: 13px;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .timeline-daily-copy span {
      display: block;
      margin-top: 4px;
      color: var(--soft);
      font-size: 11px;
      line-height: 1.35;
    }
    .timeline-daily-stat {
      min-width: 0;
      padding: 8px 10px;
      border-radius: 8px;
      border: 1px solid rgba(148, 163, 184, 0.18);
      background: rgba(2, 6, 23, 0.58);
    }
    .timeline-daily-stat strong {
      display: block;
      color: #eef6ff;
      font-size: 18px;
      line-height: 1.1;
      overflow-wrap: anywhere;
    }
    .timeline-daily-stat span {
      display: block;
      margin-top: 4px;
      color: var(--muted);
      font-size: 9px;
      line-height: 1.2;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .timeline-layout {
      display: grid;
      grid-template-columns: minmax(300px, 420px) minmax(0, 1fr) minmax(310px, 410px);
      gap: 14px;
      align-items: start;
    }
    .timeline-beat-list {
      display: grid;
      gap: 8px;
      max-height: 760px;
      overflow: auto;
      padding-right: 5px;
      scrollbar-color: rgba(34,211,238,0.62) rgba(15,23,42,0.7);
    }
    .timeline-beat-card {
      min-height: 82px;
      display: grid;
      grid-template-columns: 42px minmax(0, 1fr) auto;
      gap: 9px;
      align-items: center;
      padding: 9px;
      border-radius: 10px;
      border: 1px solid rgba(148, 163, 184, 0.18);
      background: rgba(2, 6, 23, 0.58);
      color: var(--soft);
      text-align: left;
      font: inherit;
      cursor: pointer;
    }
    .timeline-beat-card.selected {
      border-color: rgba(251, 191, 36, 0.68);
      box-shadow: inset 3px 0 0 var(--gold), 0 0 26px rgba(251, 191, 36, 0.12);
      background:
        linear-gradient(90deg, rgba(34, 211, 238, 0.12), rgba(251, 191, 36, 0.08)),
        rgba(2, 6, 23, 0.78);
    }
    .timeline-beat-icon {
      width: 40px;
      aspect-ratio: 1;
      display: grid;
      place-items: center;
      border-radius: 9px;
      border: 1px solid rgba(34, 211, 238, 0.34);
      background:
        radial-gradient(circle at 30% 20%, rgba(255,255,255,0.28), transparent 16px),
        linear-gradient(135deg, rgba(34,211,238,0.32), rgba(232,121,249,0.18)),
        rgba(2, 6, 23, 0.68);
      color: #fff7cc;
      font-size: 10px;
      font-weight: 950;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      animation: familyThumbGlow 3.6s ease-in-out infinite;
    }
    .timeline-beat-card strong {
      display: block;
      color: #eef6ff;
      font-size: 12px;
      line-height: 1.2;
      overflow-wrap: anywhere;
    }
    .timeline-beat-card span {
      display: block;
      margin-top: 4px;
      color: var(--muted);
      font-size: 10px;
      line-height: 1.25;
      overflow-wrap: anywhere;
    }
    .timeline-beat-card em {
      color: #fff7cc;
      font-style: normal;
      font-size: 10px;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .timeline-series-panel {
      min-height: 760px;
    }
    .timeline-chart-wrap {
      position: relative;
      min-height: 270px;
      margin: 12px 0 14px;
      padding: 10px 10px 8px;
      border-radius: 10px;
      border: 1px solid rgba(34, 211, 238, 0.18);
      background:
        linear-gradient(90deg, rgba(34, 211, 238, 0.08) 1px, transparent 1px),
        linear-gradient(0deg, rgba(148, 163, 184, 0.04) 1px, transparent 1px),
        radial-gradient(circle at 50% 0%, rgba(34, 211, 238, 0.12), transparent 19rem),
        rgba(2, 6, 23, 0.56);
      background-size: 32px 32px, 32px 32px, auto, auto;
      overflow: hidden;
    }
    .timeline-chart-wrap:before {
      content: "";
      position: absolute;
      inset: 0;
      pointer-events: none;
      background: linear-gradient(90deg, transparent, rgba(34, 211, 238, 0.12), transparent);
      opacity: 0.38;
      transform: translateX(-100%);
      animation: scanSweep 6.8s ease-in-out infinite;
    }
    .timeline-chart-head {
      position: relative;
      z-index: 1;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 8px;
    }
    .timeline-chart-head strong {
      color: var(--cyan);
      font-size: 12px;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .timeline-chart-head span {
      color: var(--muted);
      font-size: 10px;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .timeline-linechart {
      position: relative;
      z-index: 1;
      width: 100%;
      min-height: 230px;
    }
    .timeline-linechart svg {
      display: block;
      width: 100%;
      height: auto;
      min-height: 230px;
    }
    .timeline-chart-grid {
      stroke: rgba(148, 163, 184, 0.18);
      stroke-width: 1;
      vector-effect: non-scaling-stroke;
    }
    .timeline-chart-axis {
      stroke: rgba(226, 246, 255, 0.38);
      stroke-width: 1;
      vector-effect: non-scaling-stroke;
    }
    .timeline-chart-label {
      fill: rgba(186, 199, 218, 0.86);
      font-size: 10px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      text-transform: uppercase;
    }
    .timeline-chart-area {
      opacity: 0.32;
      filter: drop-shadow(0 0 14px rgba(34, 211, 238, 0.12));
      animation: chartBandIn 680ms ease both;
    }
    .timeline-chart-line {
      fill: none;
      stroke-width: 2.2;
      stroke-linejoin: round;
      stroke-linecap: round;
      vector-effect: non-scaling-stroke;
      filter: drop-shadow(0 0 10px currentColor);
      animation: chartLineDraw 980ms ease both;
    }
    .timeline-chart-dot {
      stroke: rgba(2, 6, 23, 0.92);
      stroke-width: 1.2;
      vector-effect: non-scaling-stroke;
      filter: drop-shadow(0 0 8px currentColor);
    }
    .timeline-chart-legend {
      position: relative;
      z-index: 1;
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 8px;
    }
    .timeline-chart-legend span {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      min-height: 22px;
      padding: 4px 7px;
      border-radius: 999px;
      border: 1px solid rgba(148, 163, 184, 0.18);
      background: rgba(2, 6, 23, 0.62);
      color: var(--soft);
      font-size: 9px;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .timeline-chart-legend i {
      width: 8px;
      aspect-ratio: 1;
      border-radius: 99px;
      background: currentColor;
      box-shadow: 0 0 10px currentColor;
    }
    .timeline-chart-readout {
      position: relative;
      z-index: 1;
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 7px;
      margin-top: 10px;
    }
    .timeline-chart-readout div {
      min-width: 0;
      padding: 8px;
      border-radius: 8px;
      border: 1px solid rgba(148, 163, 184, 0.16);
      background: rgba(2, 6, 23, 0.58);
    }
    .timeline-chart-readout strong,
    .timeline-chart-readout span {
      display: block;
      overflow-wrap: anywhere;
    }
    .timeline-chart-readout strong {
      color: #eef6ff;
      font-size: 12px;
      line-height: 1.2;
    }
    .timeline-chart-readout span {
      margin-top: 4px;
      color: var(--muted);
      font-size: 9px;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .timeline-series-list {
      display: grid;
      gap: 7px;
      max-height: 700px;
      overflow: auto;
      padding-right: 4px;
    }
    .timeline-series-row {
      display: grid;
      grid-template-columns: 70px minmax(0, 1fr) 88px;
      gap: 8px;
      align-items: center;
      min-height: 36px;
    }
    .timeline-series-row > span:first-child,
    .timeline-series-row > strong {
      color: var(--muted);
      font-size: 10px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .timeline-track {
      min-height: 22px;
      display: flex;
      gap: 3px;
      align-items: stretch;
      padding: 3px;
      border-radius: 999px;
      border: 1px solid rgba(148, 163, 184, 0.16);
      background: rgba(2, 6, 23, 0.62);
      overflow: hidden;
    }
    .timeline-track i {
      display: block;
      min-width: 3px;
      width: var(--w, 8%);
      border-radius: 999px;
      background: var(--cyan);
      box-shadow: 0 0 16px rgba(34, 211, 238, 0.22);
      animation: chargeBar 520ms ease both;
    }
    .timeline-layer-knowledge,
    .timeline-track i.timeline-layer-knowledge { background: var(--green); }
    .timeline-layer-turns,
    .timeline-track i.timeline-layer-turns { background: var(--cyan); }
    .timeline-layer-skills,
    .timeline-track i.timeline-layer-skills { background: var(--fuchsia); }
    .timeline-layer-nodes,
    .timeline-track i.timeline-layer-nodes { background: var(--gold); }
    .timeline-layer-capabilities,
    .timeline-track i.timeline-layer-capabilities { background: var(--violet); }
    .timeline-inspector {
      min-height: 620px;
    }
    .timeline-inspector p {
      max-height: 180px;
      overflow: auto;
      padding-right: 4px;
    }
    .timeline-source-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
    }
    .slot-gem {
      width: 54px;
      aspect-ratio: 1;
      display: grid;
      place-items: center;
      border-radius: 12px;
      color: #04111c;
      background: linear-gradient(135deg, var(--cyan), var(--fuchsia), var(--gold));
      font-weight: 950;
      box-shadow: 0 0 28px rgba(34, 211, 238, 0.16);
      animation: gemGlow 3.4s ease-in-out infinite;
    }
    .passport-wrap {
      display: grid;
      grid-template-columns: minmax(300px, 440px) minmax(0, 1fr);
      gap: 18px;
      align-items: start;
    }
    .phone-frame {
      border: 1px solid rgba(34, 211, 238, 0.35);
      border-radius: 26px;
      padding: 12px;
      background: rgba(2, 6, 23, 0.88);
      box-shadow: 0 24px 80px rgba(0, 0, 0, 0.35);
    }
    .phone-screen {
      min-height: 760px;
      border-radius: 20px;
      overflow: hidden;
      border: 1px solid rgba(251, 191, 36, 0.22);
      background: rgba(8, 16, 32, 0.92);
    }
    .phone-hero {
      min-height: 230px;
      padding: 18px;
      background:
        linear-gradient(180deg, rgba(2, 6, 23, 0.2), rgba(2, 6, 23, 0.82)),
        var(--selected-character-image, url("hapa-character-sheet-game-mock-04-mobile-passport.png")) center 0 / cover no-repeat;
      display: grid;
      align-content: end;
    }
    .phone-hero h3 {
      margin: 0;
      font-size: 31px;
      line-height: 0.98;
      text-transform: uppercase;
    }
    .phone-body {
      padding: 12px;
      display: grid;
      gap: 10px;
    }
    .passport-detail {
      min-height: 360px;
      animation: panelRise 260ms ease both;
    }
    .passport-detail h4 {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
    }
    .detail-kicker {
      color: var(--gold);
      font-size: 10px;
      text-transform: uppercase;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .lower-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
      margin-top: 12px;
    }
    .lower-tile {
      min-height: 64px;
      padding: 9px;
      border-radius: 8px;
      border: 1px solid rgba(148, 163, 184, 0.2);
      background: rgba(2, 6, 23, 0.62);
    }
    .lower-tile strong {
      display: block;
      color: #fff;
      font-size: 18px;
      line-height: 1;
    }
    .lower-tile span {
      display: block;
      margin-top: 4px;
      color: var(--muted);
      font-size: 10px;
      text-transform: uppercase;
      overflow-wrap: anywhere;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .example-list {
      display: grid;
      gap: 8px;
      margin-top: 12px;
    }
    .example-card {
      padding: 9px;
      border-radius: 8px;
      border: 1px solid rgba(148, 163, 184, 0.18);
      background: rgba(15, 23, 42, 0.54);
    }
    .example-card strong {
      display: block;
      color: var(--soft);
      font-size: 12px;
      line-height: 1.25;
      overflow-wrap: anywhere;
    }
    .example-card span {
      display: block;
      margin-top: 4px;
      color: var(--muted);
      font-size: 11px;
      line-height: 1.35;
      overflow-wrap: anywhere;
    }
    .mock-gallery {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin-top: 14px;
    }
    .mock-gallery img {
      width: 100%;
      aspect-ratio: 16 / 10;
      object-fit: cover;
      border-radius: 8px;
      border: 1px solid rgba(148, 163, 184, 0.26);
      filter: saturate(1.08) contrast(1.04);
    }
    @keyframes panelWake {
      from { opacity: 0; transform: translateY(10px) scale(0.992); filter: saturate(0.8); }
      to { opacity: 1; transform: translateY(0) scale(1); filter: saturate(1); }
    }
    @keyframes panelRise {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }
    @keyframes sweepLine {
      0% { transform: translateY(-20%) rotate(-7deg); opacity: 0; }
      12% { opacity: 0.7; }
      38% { opacity: 0.2; }
      100% { transform: translateY(360%) rotate(-7deg); opacity: 0; }
    }
    @keyframes scanSweep {
      0%, 55% { transform: translateX(-110%); opacity: 0; }
      68% { opacity: 0.35; }
      88%, 100% { transform: translateX(110%); opacity: 0; }
    }
    @keyframes chartBandIn {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 0.32; transform: translateY(0); }
    }
    @keyframes chartLineDraw {
      from { stroke-dasharray: 1; stroke-dashoffset: 1; opacity: 0.28; }
      to { stroke-dasharray: 1; stroke-dashoffset: 0; opacity: 1; }
    }
    @keyframes portraitDrift {
      0%, 100% { background-position: center 10%; filter: saturate(1.04) brightness(0.96); }
      50% { background-position: center 15%; filter: saturate(1.15) brightness(1.04); }
    }
    @keyframes holoGrid {
      from { background-position: 0 0, 0 0; }
      to { background-position: 18px 18px, -18px 18px; }
    }
    @keyframes modelReticle {
      from { transform: translate(-50%, -50%) rotate(0deg); }
      to { transform: translate(-50%, -50%) rotate(360deg); }
    }
    @keyframes titleResolve {
      0% { opacity: 0; letter-spacing: 0; transform: translateX(-8px); filter: blur(6px); }
      55% { opacity: 1; filter: blur(0); }
      100% { opacity: 1; letter-spacing: 0; transform: translateX(0); filter: blur(0); }
    }
    @keyframes profileVideoCyclePrimary {
      0%, 43% { opacity: 0.82; transform: scale(1.015); }
      49%, 94% { opacity: 0; transform: scale(1.04); }
      100% { opacity: 0.82; transform: scale(1.015); }
    }
    @keyframes profileVideoCycleSecondary {
      0%, 43% { opacity: 0; transform: scale(1.04); }
      49%, 94% { opacity: 0.82; transform: scale(1.015); }
      100% { opacity: 0; transform: scale(1.04); }
    }
    @keyframes medalPulse {
      0%, 100% { box-shadow: 0 0 34px rgba(251, 191, 36, 0.14); transform: translateY(0); }
      50% { box-shadow: 0 0 58px rgba(251, 191, 36, 0.28), 0 0 24px rgba(34, 211, 238, 0.12); transform: translateY(-1px); }
    }
    @keyframes medalGlint {
      0%, 60% { transform: translateX(-70%) rotate(0deg); opacity: 0; }
      72% { opacity: 0.85; }
      86%, 100% { transform: translateX(70%) rotate(0deg); opacity: 0; }
    }
    @keyframes chargeBar {
      from { transform: scaleX(0.08); filter: brightness(0.8); }
      to { transform: scaleX(1); filter: brightness(1); }
    }
    @keyframes statIconPulse {
      0%, 100% { filter: saturate(1) brightness(1); transform: translateY(0); }
      50% { filter: saturate(1.2) brightness(1.12); transform: translateY(-1px); }
    }
    @keyframes statIconOrbit {
      0% { transform: translate(13px, -13px) scale(0.8); opacity: 0.4; }
      25% { transform: translate(13px, 13px) scale(1); opacity: 0.9; }
      50% { transform: translate(-13px, 13px) scale(0.82); opacity: 0.5; }
      75% { transform: translate(-13px, -13px) scale(1); opacity: 0.9; }
      100% { transform: translate(13px, -13px) scale(0.8); opacity: 0.4; }
    }
    @keyframes familyThumbGlow {
      0%, 100% { box-shadow: 0 0 18px rgba(34, 211, 238, 0.12), inset 0 0 0 1px rgba(255,255,255,0.08); }
      50% { box-shadow: 0 0 28px rgba(232, 121, 249, 0.18), inset 0 0 12px rgba(34, 211, 238, 0.08); }
    }
    @keyframes nodeThumbGlow {
      0%, 100% { filter: saturate(1) brightness(1); transform: translateY(0); }
      50% { filter: saturate(1.2) brightness(1.08); transform: translateY(-1px); }
    }
    @keyframes nodeThumbOrbit {
      from { transform: rotate(45deg); }
      to { transform: rotate(405deg); }
    }
    @keyframes thumbSweep {
      0%, 58% { transform: translateX(-120%); opacity: 0; }
      72% { opacity: 0.7; }
      90%, 100% { transform: translateX(120%); opacity: 0; }
    }
    @keyframes staggerIn {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }
    @keyframes corePulse {
      0%, 100% { box-shadow: 0 0 38px rgba(34, 211, 238, 0.17); }
      50% { box-shadow: 0 0 68px rgba(34, 211, 238, 0.28), 0 0 28px rgba(251, 191, 36, 0.11); }
    }
    @keyframes branchIdle {
      0%, 100% { filter: saturate(1); }
      50% { filter: saturate(1.18) brightness(1.04); }
    }
    @keyframes nodePulse {
      0%, 100% { box-shadow: 0 0 24px rgba(34, 211, 238, 0.13); }
      50% { box-shadow: 0 0 44px rgba(34, 211, 238, 0.24), inset 0 0 20px rgba(34, 211, 238, 0.05); }
    }
    @keyframes edgeFlow {
      from { stroke-dashoffset: 0; }
      to { stroke-dashoffset: -64; }
    }
    @keyframes proofRingSpin {
      from { transform: rotate(0deg); opacity: 0.62; }
      to { transform: rotate(360deg); opacity: 0.62; }
    }
    @keyframes sparkDrift {
      0%, 100% { transform: translate3d(0, 0, 0) scale(0.85); opacity: 0.35; }
      35% { transform: translate3d(12px, -8px, 0) scale(1.15); opacity: 0.9; }
      70% { transform: translate3d(-7px, 10px, 0) scale(0.95); opacity: 0.48; }
    }
    @keyframes gemGlow {
      0%, 100% { filter: saturate(1) brightness(1); }
      50% { filter: saturate(1.25) brightness(1.1); }
    }
    @media (max-width: 1180px) {
      .app { grid-template-columns: 1fr; }
      .app.presentation { grid-template-columns: 1fr; }
      .sidebar {
        position: relative;
        height: auto;
        border-right: 0;
        border-bottom: 1px solid var(--line);
      }
      .nav {
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      }
      .side-stats { grid-template-columns: repeat(4, minmax(0, 1fr)); }
      .controls { grid-template-columns: repeat(3, minmax(0, 1fr)); }
      .topbar { position: relative; }
      .game-hero-grid, .codex-grid, .codex-inventory-grid, .quality-grid, .proof-map-grid, .proof-comprehensive-grid, .loadout-grid, .timeline-brief, .timeline-layout, .timeline-daily-brief, .timeline-source-grid, .profile-brief, .profile-lower-grid, .passport-wrap {
        grid-template-columns: 1fr;
      }
      .portrait-card { min-height: 420px; }
      .portrait-card.model-card { min-height: 580px; }
      .portrait-art.model-stage { min-height: 480px; }
      .game-stats, .game-proof-strip, .proof-chain, .proof-flow-strip, .quality-preview-grid, .timeline-kpi-grid, .timeline-chart-readout, .profile-section-grid, .profile-voice-grid, .mock-gallery {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
      .sb-grid, .sb-footer {
        grid-template-columns: 1fr 1fr;
      }
      .sb-radar {
        min-height: 300px;
      }
    }
    @media (max-width: 760px) {
      .topbar, .controls, .content { padding-left: 14px; padding-right: 14px; }
      .main, .topbar, .controls, .content {
        width: 100vw;
        max-width: 100vw;
        overflow-x: hidden;
      }
      .topbar { grid-template-columns: 1fr; }
      .status-row { justify-content: flex-start; }
      .controls { grid-template-columns: 1fr; }
      .grid.cols-2, .grid.cols-3, .grid.cols-4 { grid-template-columns: 1fr; }
      .sidebar {
        width: 100%;
        max-width: 100vw;
        padding: 12px;
        overflow-x: hidden;
      }
      .brand { max-width: calc(100vw - 24px); }
      .brand p, .route p { max-width: calc(100vw - 28px); }
      .side-stats {
        display: flex;
        gap: 8px;
        overflow-x: auto;
        max-width: 100%;
        min-width: 0;
        padding-bottom: 2px;
      }
      .mini-stat { flex: 0 0 118px; }
      .nav {
        display: flex;
        gap: 8px;
        overflow-x: auto;
        max-width: 100%;
        min-width: 0;
        padding-bottom: 3px;
      }
      .nav-button {
        flex: 0 0 156px;
        grid-template-columns: 28px minmax(0, 1fr);
      }
      .nav-meta { display: none; }
      .chip { white-space: normal; }
      .hero { min-height: 360px; background-position: center; }
      .section-head { align-items: start; flex-direction: column; }
      .app.presentation .topbar,
      .app.presentation .content {
        width: 100vw;
        max-width: 100vw;
      }
      .game-title {
        grid-template-columns: 1fr;
      }
      .game-title h3 {
        font-size: 40px;
      }
      .rank-medal {
        width: 92px;
        font-size: 42px;
      }
      .profile-title-card {
        min-height: 300px;
      }
      .profile-title-card h3 {
        font-size: 40px;
      }
      .profile-kpi-grid, .profile-run-grid, .profile-section-grid, .profile-voice-grid {
        grid-template-columns: 1fr;
      }
      .portrait-card.model-card { min-height: 540px; }
      .portrait-art.model-stage { min-height: 430px; }
      .model-hud { inset: 14px; }
      .model-status-chip, .model-class-chip, .model-rank-chip { min-height: 28px; font-size: 9px; }
      .character-rank-grid {
        grid-template-columns: 1fr;
      }
      .game-stats, .game-proof-strip, .proof-chain, .proof-flow-strip, .quality-preview-grid, .timeline-chart-readout, .mock-gallery {
        grid-template-columns: 1fr;
      }
      .timeline-chart-wrap {
        padding: 8px 6px;
      }
      .timeline-chart-head {
        align-items: flex-start;
        flex-direction: column;
      }
      .quality-scatter {
        min-height: 420px;
      }
      .second-brain-mini {
        min-height: auto;
      }
      .sb-head {
        display: grid;
      }
      .sb-status {
        justify-content: flex-start;
      }
      .sb-grid, .sb-footer {
        grid-template-columns: 1fr;
      }
      .sb-radar {
        min-height: 340px;
      }
      .skill-tree, .constellation {
        min-height: 560px;
      }
      .tree-branch {
        position: relative;
        inset: auto !important;
        transform: none !important;
        width: 100%;
      }
      .codex-inspector {
        min-height: auto;
      }
      .skill-tree {
        display: grid;
        gap: 8px;
        place-items: stretch;
      }
      .tree-core {
        justify-self: center;
      }
      .tree-core.skill-loop-core {
        width: min(280px, 84vw);
        min-width: 0;
        margin-bottom: 10px;
      }
      .constellation {
        min-height: 720px;
      }
      .graph-core, .graph-node {
        position: relative;
        left: auto !important;
        top: auto !important;
        right: auto !important;
        bottom: auto !important;
        transform: none;
        margin: 10px auto;
      }
    }
    @media (max-width: 520px) {
      .app, .sidebar, .main, .topbar, .controls, .content {
        width: min(100vw, 390px);
        max-width: min(100vw, 390px);
      }
      .brand, .brand p, .route p, .status-row {
        max-width: 362px;
      }
    }
    @media (prefers-reduced-motion: reduce) {
      *, *:before, *:after { transition: none !important; animation: none !important; }
      .profile-bg-video.is-primary { opacity: 0.78; transform: scale(1); }
      .profile-bg-video.is-secondary { opacity: 0; }
    }
  </style>
</head>
<body>
  <div class="app">
    <aside class="sidebar">
      <section class="brand">
        <div class="brand-kicker">Hapa resume node</div>
        <h1>Character Sheet</h1>
        <p id="brand-copy">Loading Second Brain projection...</p>
      </section>
      <nav class="nav" id="nav"></nav>
      <section class="side-stats" id="side-stats"></section>
    </aside>
    <main class="main">
      <header class="topbar">
        <div class="route">
          <div class="section-kicker" id="route-kicker">Projection</div>
          <h2 id="route-title">Hapa Character Sheet</h2>
          <p id="route-copy">A professional resume, RPG stats page, skill codex, media kit, and lineage browser drawn from Hapa Second Brain.</p>
        </div>
        <div class="status-row" id="status-row"></div>
      </header>
      <section class="controls">
        <label class="field">
          <span class="label">Search</span>
          <input id="q" type="search" placeholder="Filter skills, nodes, turns, media, protocols">
        </label>
        <label class="field">
          <span class="label">Skill Family</span>
          <select id="family-filter"></select>
        </label>
        <label class="field">
          <span class="label">Rank</span>
          <select id="rank-filter">
            <option value="all">All ranks</option>
            <option value="SS">SS</option>
            <option value="S">S</option>
            <option value="A">A</option>
            <option value="B">B</option>
            <option value="C">C</option>
            <option value="D">D</option>
          </select>
        </label>
        <label class="field">
          <span class="label">Type</span>
          <select id="type-filter"></select>
        </label>
        <label class="field">
          <span class="label">Mode</span>
          <select id="mode-filter"></select>
        </label>
        <label class="field">
          <span class="label">Sort</span>
          <select id="sort-filter">
            <option value="evidence">Evidence</option>
            <option value="score">Score</option>
            <option value="source">Source Count</option>
            <option value="artifact">Artifacts</option>
            <option value="name">Name</option>
            <option value="updated">Updated</option>
          </select>
        </label>
        <div class="field">
          <span class="label">Abstraction</span>
          <div class="segmented" id="levels">
            <button type="button" data-level="signal" class="active">Signal</button>
            <button type="button" data-level="proof">Proof</button>
            <button type="button" data-level="raw">Raw</button>
          </div>
        </div>
      </section>
      <section class="content" id="content"></section>
    </main>
  </div>
  <script src="hapa-character-sheet-data.js"></script>
  <script>
    const DATA = window.HAPA_CHARACTER_SHEET_DATA;
    const state = {
      view: window.location.hash.includes("presentation") ? "presentation" : "data",
      gamePanel: (() => {
        const route = window.location.hash.split("&")[0];
        return route.includes("codex") ? "codex" : route.includes("proof") ? "proof" : route.includes("loadout") ? "loadout" : route.includes("timeline") ? "timeline" : route.includes("profile") ? "profile" : route.includes("passport") ? "passport" : "hero";
      })(),
      passportFocus: (() => {
        const match = decodeURIComponent(window.location.hash).match(/focus=([^&]+)/);
        return match ? match[1] : "metric:evidence";
      })(),
      codexFamily: (() => {
        const match = decodeURIComponent(window.location.hash).match(/family=([^&]+)/);
        return match ? match[1] : (DATA.skill_families[0]?.label || "");
      })(),
      codexCapabilityId: (() => {
        const match = decodeURIComponent(window.location.hash).match(/cap=([^&]+)/);
        return match ? match[1] : "";
      })(),
      codexSkillId: (() => {
        const match = decodeURIComponent(window.location.hash).match(/skill=([^&]+)/);
        return match ? match[1] : "";
      })(),
      proofFocus: (() => {
        const match = decodeURIComponent(window.location.hash).match(/proof=([^&]+)/);
        return match ? match[1] : "skills";
      })(),
      loadoutNodeId: (() => {
        const match = decodeURIComponent(window.location.hash).match(/node=([^&]+)/);
        return match ? match[1] : (DATA.nodes[0]?.node_id || "");
      })(),
      loadoutType: (() => {
        const match = decodeURIComponent(window.location.hash).match(/loadoutType=([^&]+)/);
        return match ? match[1] : "all";
      })(),
      timelineLayer: (() => {
        const match = decodeURIComponent(window.location.hash).match(/layer=([^&]+)/);
        return match ? match[1] : "all";
      })(),
      timelineEra: (() => {
        const match = decodeURIComponent(window.location.hash).match(/era=([^&]+)/);
        return match ? match[1] : "all";
      })(),
      timelineScale: (() => {
        const match = decodeURIComponent(window.location.hash).match(/scale=([^&]+)/);
        return match ? match[1] : "month";
      })(),
      timelineBeatId: (() => {
        const match = decodeURIComponent(window.location.hash).match(/beat=([^&]+)/);
        return match ? match[1] : "";
      })(),
      imageSrc: localStorage.getItem("hapaCharacterSheetImageSrc") || DATA.image_sources?.default_url || "hapa-character-sheet-game-mock-04-mobile-passport.png",
      imageLabel: localStorage.getItem("hapaCharacterSheetImageLabel") || DATA.image_sources?.default_label || "Calder Character Model Poster",
      imageFilter: localStorage.getItem("hapaCharacterSheetImageFilter") || "character_model",
      sound: localStorage.getItem("hapaCharacterSheetSfx") === "on",
      panel: "sheet",
      q: "",
      family: "all",
      rank: "all",
      type: "all",
      mode: "all",
      sort: "evidence",
      level: "signal",
      limit: 120
    };
    const panelInfo = {
      sheet: ["Character Sheet", "Compressed operator stats, resume signals, source mix, and live Hapa scope."],
      resume: ["Resume", "Professional brochure view with outcomes, proof lanes, and portfolio-ready claims."],
      skills: ["Skills", "The skill inventory ranked like a game sheet, with evidence and source lineage."],
      nodes: ["Nodes", "Hapa nodes as portfolio artifacts, tools, workflows, and operating surfaces."],
      capabilities: ["Capabilities", "Using and enhancing skills for each node, bridged to general skills and practice signals."],
      lineage: ["Lineage", "AI turns and learning links connecting exposure, practice, result, and reusable wisdom."],
      sources: ["Sources", "Material consumed, source systems, media types, topics, and knowledge bodies."],
      media: ["Media", "Generated and queued visual assets for cards, nodes, avatars, protocols, and results."],
      agents: ["Agents", "Avatars, agents, harnesses, and capability profiles available to operate the sheet."],
      protocols: ["Protocols", "Hapa protocol docs, wiki protocol articles, API, CLI, manifests, and flow contracts."],
      board: ["Board", "Kanban state for turning this prototype into a standard Hapa happ."]
    };
    const gamePanelInfo = {
      hero: ["Hero Detail", "A high-production public character screen for quick human understanding."],
      codex: ["Skill Codex", "Skills as job classes, capabilities as unlocks, nodes as equipment, evidence as XP."],
      proof: ["Proof Map", "A visual constellation connecting sources, turns, skills, nodes, capabilities, media, agents, and protocols."],
      loadout: ["Loadout", "Portfolio nodes, agent companions, protocol runes, and media artifacts as usable inventory."],
      timeline: ["Timeline", "A historical lore/canon rail for knowledge acquired, AI turns, skills, capabilities, and Hapa nodes."],
      profile: ["Profile", "A mined personality, lore, voice, values, and persona-adapter dossier for humans and agents."],
      passport: ["Passport", "A compact mobile-first character card for quick sharing."]
    };
    const navIcons = {
      sheet: "CS",
      resume: "CV",
      skills: "SK",
      nodes: "ND",
      capabilities: "CP",
      lineage: "LN",
      sources: "SR",
      media: "MD",
      agents: "AG",
      protocols: "PR",
      board: "KB"
    };
    const countByPanel = {
      sheet: DATA.summary.total_records,
      resume: DATA.nodes.length + DATA.skills.length,
      skills: DATA.skills.length,
      nodes: DATA.nodes.length,
      capabilities: DATA.capabilities.length,
      lineage: DATA.turns.length,
      sources: DATA.topics.length,
      media: DATA.media.length,
      agents: DATA.agents.length,
      protocols: DATA.protocols.length + DATA.docs.length,
      board: DATA.board.tasks.length
    };
    const el = (tag, cls, html) => {
      const node = document.createElement(tag);
      if (cls) node.className = cls;
      if (html !== undefined) node.innerHTML = html;
      return node;
    };
    const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (m) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[m]));
    const fmt = (value) => Number(value || 0).toLocaleString();
    const pct = (value) => `${Math.max(1, Math.min(100, Number(value || 0)))}%`;
    const NODE_SCORE_MAX = Math.max(1, ...DATA.nodes.map((node) => Number(node.score || 0)));
    const textOf = (item) => Object.values(item || {}).filter((value) => typeof value === "string" || typeof value === "number").join(" ").toLowerCase();
    const queryMatch = (item) => !state.q || textOf(item).includes(state.q.toLowerCase());
    const rankClass = (rank) => String(rank || "").toLowerCase().replace(/[^a-z]/g, "");
    const badge = (text, cls = "") => `<span class="badge ${cls}">${esc(text)}</span>`;
    const chips = (items, cls = "") => (items || []).filter(Boolean).slice(0, 8).map((item) => badge(item, cls)).join("");
    const proofVisible = () => state.level === "proof" || state.level === "raw";
    const rawVisible = () => state.level === "raw";
    let audioCtx = null;
    let lastHoverTarget = null;
    let lastHoverTone = 0;
    function audioContext() {
      const Ctx = window.AudioContext || window.webkitAudioContext;
      if (!Ctx) return null;
      if (!audioCtx) audioCtx = new Ctx();
      return audioCtx;
    }
    function playTone(kind = "click") {
      if (!state.sound) return;
      const ctx = audioContext();
      if (!ctx) return;
      const profiles = {
        hover: [620, 0.026, "sine", 0.018],
        click: [420, 0.04, "triangle", 0.026],
        select: [760, 0.055, "sine", 0.03],
        change: [540, 0.05, "triangle", 0.024],
        toggle: [880, 0.07, "sine", 0.034]
      };
      const [freq, duration, wave, volume] = profiles[kind] || profiles.click;
      try {
        if (ctx.state === "suspended") ctx.resume();
        const now = ctx.currentTime;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = wave;
        osc.frequency.setValueAtTime(freq, now);
        if (kind === "select" || kind === "toggle") osc.frequency.exponentialRampToValueAtTime(freq * 1.36, now + duration);
        gain.gain.setValueAtTime(0.0001, now);
        gain.gain.exponentialRampToValueAtTime(volume, now + 0.008);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + duration);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now);
        osc.stop(now + duration + 0.012);
      } catch (err) {
        state.sound = false;
        localStorage.setItem("hapaCharacterSheetSfx", "off");
      }
    }
    const gameMocks = [
      ["Hero Detail", "hapa-character-sheet-game-mock-01-hero-detail.png"],
      ["Proof Map", "hapa-character-sheet-game-mock-02-proof-constellation.png"],
      ["Skill Codex", "hapa-character-sheet-game-mock-03-skill-codex.png"],
      ["Mobile Passport", "hapa-character-sheet-game-mock-04-mobile-passport.png"]
    ];
    function sortItems(items) {
      const key = state.sort;
      return [...items].sort((a, b) => {
        if (key === "name") return String(a.label || a.title || "").localeCompare(String(b.label || b.title || ""));
        if (key === "updated") return String(b.updated_at || b.turn_started_at || b.ts || "").localeCompare(String(a.updated_at || a.turn_started_at || a.ts || ""));
        const map = { evidence: "evidence_count", score: "score", source: "source_count", artifact: "artifact_count" };
        const prop = map[key] || "score";
        return Number(b[prop] || 0) - Number(a[prop] || 0);
      });
    }
    function limited(items) {
      return sortItems(items).slice(0, state.limit);
    }
    function section(title, subtitle, body) {
      return `<section class="section"><div class="section-head"><div><div class="section-kicker">${esc(subtitle || "Layer")}</div><h3>${esc(title)}</h3></div></div>${body}</section>`;
    }
    function record(title, meta, description, badges, extra = "") {
      return `<article class="record">
        <div class="record-title"><strong>${esc(title)}</strong><div>${badges || ""}</div></div>
        ${meta ? `<div class="record-meta">${esc(meta)}</div>` : ""}
        ${description ? `<p>${esc(description)}</p>` : ""}
        ${extra}
      </article>`;
    }
    function meter(label, value, detail) {
      return `<div class="meter">
        <div class="meter-top"><span class="meter-label">${esc(label)}</span><span class="meter-label">${fmt(value)}</span></div>
        <div class="bar"><div class="fill" style="--value:${pct(value)}"></div></div>
        ${detail ? `<div class="record-meta">${esc(detail)}</div>` : ""}
      </div>`;
    }
    function showMore(total) {
      if (total <= state.limit) return "";
      return `<button class="show-more" type="button" data-show-more="1">Show more - ${fmt(Math.min(total - state.limit, 120))} of ${fmt(total - state.limit)} remaining</button>`;
    }
    function modeSwitch() {
      return `<div class="mode-switch" aria-label="View mode">
        <button type="button" data-view="data" class="${state.view === "data" ? "active" : ""}">Data View</button>
        <button type="button" data-view="presentation" class="${state.view === "presentation" ? "active" : ""}">Presentation</button>
      </div>`;
    }
    function soundButton() {
      return `<button type="button" class="sound-toggle ${state.sound ? "active" : ""}" data-sound-toggle aria-pressed="${state.sound ? "true" : "false"}">${state.sound ? "SFX On" : "SFX Off"}</button>`;
    }
    function setHeader() {
      const [title, copy] = state.view === "presentation" ? gamePanelInfo[state.gamePanel] : panelInfo[state.panel];
      document.getElementById("route-title").textContent = title;
      document.getElementById("route-copy").textContent = copy;
      document.getElementById("route-kicker").textContent = state.view === "presentation" ? `${DATA.profile.handle} / Character Mode` : `${DATA.profile.handle} / Admin Data / ${state.level}`;
      document.getElementById("status-row").innerHTML = [
        modeSwitch(),
        soundButton(),
        `<span class="chip green"><span class="dot"></span>${esc(DATA.summary.generated_label)}</span>`,
        `<span class="chip cyan">${fmt(DATA.summary.items)} items</span>`,
        `<span class="chip pink">${fmt(DATA.summary.skills)} skills</span>`,
        `<span class="chip gold">${fmt(DATA.summary.turns)} turns</span>`
      ].join("");
    }
    function renderNav() {
      const nav = document.getElementById("nav");
      nav.innerHTML = Object.keys(panelInfo).map((key) => `<button class="nav-button ${state.panel === key ? "active" : ""}" type="button" data-panel="${key}">
        <span class="nav-icon">${navIcons[key]}</span>
        <span class="nav-title">${panelInfo[key][0]}</span>
        <span class="nav-meta">${fmt(countByPanel[key])}</span>
      </button>`).join("");
    }
    function renderSideStats() {
      const stats = [
        ["Evidence", DATA.summary.skill_evidence],
        ["Edges", DATA.summary.edges],
        ["Media", DATA.summary.media_jobs],
        ["Topics", DATA.summary.topics]
      ];
      document.getElementById("side-stats").innerHTML = stats.map(([label, value]) => `<div class="mini-stat"><strong>${fmt(value)}</strong><span>${esc(label)}</span></div>`).join("");
      document.getElementById("brand-copy").textContent = `${fmt(DATA.summary.skills)} skills, ${fmt(DATA.summary.nodes)} nodes, ${fmt(DATA.summary.turns)} turns, ${fmt(DATA.summary.media_jobs)} media jobs, and ${fmt(DATA.summary.topics)} topic profiles compressed into a public-facing dossier.`;
    }
    function fillOptions() {
      const family = document.getElementById("family-filter");
      const families = [...new Set(DATA.skills.map((item) => item.skill_family).filter(Boolean))].sort();
      family.innerHTML = `<option value="all">All families</option>` + families.map((value) => `<option value="${esc(value)}">${esc(value.replaceAll("_", " "))}</option>`).join("");
      const type = document.getElementById("type-filter");
      const types = [...new Set([...DATA.nodes.map((item) => item.node_type), ...DATA.media.map((item) => item.status), ...DATA.protocols.map((item) => item.article_type)].filter(Boolean))].sort();
      type.innerHTML = `<option value="all">All types</option>` + types.map((value) => `<option value="${esc(value)}">${esc(value.replaceAll("_", " "))}</option>`).join("");
      const mode = document.getElementById("mode-filter");
      const modes = [...new Set(DATA.capabilities.map((item) => item.mode).filter(Boolean))].sort();
      mode.innerHTML = `<option value="all">All modes</option>` + modes.map((value) => `<option value="${esc(value)}">${esc(value)}</option>`).join("");
    }
    function statsGrid(cards) {
      return `<div class="grid cols-4">${cards.map(([value, label, detail]) => `<div class="stat-card"><strong>${esc(value)}</strong><span>${esc(label)}</span>${detail ? `<div class="record-meta">${esc(detail)}</div>` : ""}</div>`).join("")}</div>`;
    }
    function renderSheet() {
      const statMeters = DATA.stats.map((stat) => `<div class="card">${meter(stat.label, stat.value, stat.detail)}<div class="tag-row">${chips(stat.top_skills, "cyan")}</div></div>`).join("");
      const families = DATA.skill_families.slice(0, 18).map((family) => record(family.label.replaceAll("_", " "), `${fmt(family.skill_count)} skills / ${fmt(family.evidence_count)} evidence`, family.top_skill || "", badge(family.rank, "gold"))).join("");
      const claimCards = DATA.resume.claims.map((claim) => record(claim.title, claim.meta, claim.body, chips(claim.proof, "cyan"))).join("");
      return `<section class="hero">
        <div class="section-kicker">Professional RPG dossier</div>
        <h3>${esc(DATA.profile.name)}</h3>
        <p>${esc(DATA.profile.summary)}</p>
        <div class="hero-strip">
          ${badge(`${fmt(DATA.summary.items)} source items`, "cyan")}
          ${badge(`${fmt(DATA.summary.skill_evidence)} skill evidence links`, "gold")}
          ${badge(`${fmt(DATA.summary.capability_bridges)} capability bridges`, "pink")}
          ${badge(`${fmt(DATA.summary.board_tasks)} board cards`, "green")}
        </div>
      </section>
      ${section("Core Stats", "Game sheet compression", `<div class="grid cols-4">${statMeters}</div>`)}
      ${section("Resume Signals", "Public proof layer", `<div class="grid cols-3">${claimCards}</div>`)}
      ${section("Dominant Skill Families", "Abstraction layer", `<div class="grid cols-3">${families}</div>`)}
      ${section("Portfolio Lanes", "Node result mix", statsGrid(DATA.node_type_summary.slice(0, 8).map((item) => [fmt(item.count), item.label.replaceAll("_", " "), `${fmt(item.topic_count)} topics / ${fmt(item.card_count)} cards`])) )}`;
    }
    function renderResume() {
      const impact = DATA.resume.outcomes.map((item) => record(item.title, item.meta, item.body, chips(item.tags, "gold"))).join("");
      const nodes = DATA.nodes.filter(queryMatch).slice(0, 9).map((item) => record(item.label, `${item.node_type} / score ${fmt(item.score)}`, item.description, `${badge(`${fmt(item.topic_count)} topics`, "cyan")}${badge(`${fmt(item.card_count)} cards`, "pink")}`)).join("");
      const proof = DATA.resume.proof_lanes.map((lane) => `<div class="card"><h4>${esc(lane.label)}</h4><p>${esc(lane.body)}</p><div class="tag-row">${chips(lane.metrics, "green")}</div></div>`).join("");
      return `${section("Professional Summary", "Brochure view", `<div class="grid cols-2"><div class="card"><h4>${esc(DATA.profile.title)}</h4><p>${esc(DATA.profile.resume_summary)}</p><div class="tag-row">${chips(DATA.profile.roles, "cyan")}</div></div><div class="card avatar-line"></div></div>`)}
      ${section("Outcome Claims", "Resume bullets with lineage", `<div class="grid cols-3">${impact}</div>`)}
      ${section("Proof Lanes", "What backs the claim", `<div class="grid cols-3">${proof}</div>`)}
      ${section("Representative Portfolio Nodes", "Result artifacts", `<div class="grid cols-3">${nodes}</div>`)}`;
    }
    function renderSkills() {
      let items = DATA.skills.filter(queryMatch);
      if (state.family !== "all") items = items.filter((item) => item.skill_family === state.family);
      if (state.rank !== "all") items = items.filter((item) => item.rank === state.rank);
      const visible = limited(items);
      const body = visible.map((item) => {
        const extra = [
          `<div class="tag-row">${chips([item.skill_family, `${fmt(item.source_count)} sources`, `${fmt(item.artifact_count)} artifacts`], "cyan")}</div>`,
          proofVisible() ? `<p>${esc(item.summary || "Evidence-backed skill projection.")}</p>` : "",
          proofVisible() && item.related_bodies.length ? `<div class="tag-row">${chips(item.related_bodies, "pink")}</div>` : "",
          rawVisible() ? `<div class="record-meta">${esc(item.skill_id)} / updated ${esc(item.updated_at || "")}</div>` : ""
        ].join("");
        return record(item.label, `${fmt(item.evidence_count)} evidence links / ${fmt(item.source_count)} sources`, "", `<span class="rank ${rankClass(item.rank)}">${esc(item.rank)}</span>`, extra);
      }).join("");
      return section("Skill Codex", `Showing ${fmt(visible.length)} of ${fmt(items.length)} filtered / ${fmt(DATA.skills.length)} total`, `<div class="grid cols-3">${body || `<div class="empty">No skills match the current filters.</div>`}</div>${showMore(items.length)}`);
    }
    function renderNodes() {
      let items = DATA.nodes.filter(queryMatch);
      if (state.type !== "all") items = items.filter((item) => item.node_type === state.type);
      const visible = limited(items);
      const body = visible.map((item) => {
        const extra = [
          `<div class="tag-row">${chips([item.node_type, `${fmt(item.topic_count)} topics`, `${fmt(item.body_count)} bodies`, `${fmt(item.card_count)} cards`], "cyan")}</div>`,
          rawVisible() ? `<div class="source-link">${esc(item.source_path || item.node_id)}</div>` : ""
        ].join("");
        return record(item.label, `Score ${fmt(item.score)}`, item.description, badge(item.node_type, "gold"), extra);
      }).join("");
      return section("Node Portfolio", `Showing ${fmt(visible.length)} of ${fmt(items.length)} filtered / ${fmt(DATA.nodes.length)} total`, `<div class="grid cols-3">${body || `<div class="empty">No nodes match the current filters.</div>`}</div>${showMore(items.length)}`);
    }
    function renderCapabilities() {
      let items = DATA.capabilities.filter(queryMatch);
      if (state.family !== "all") items = items.filter((item) => item.skill_family === state.family);
      if (state.mode !== "all") items = items.filter((item) => item.mode === state.mode);
      const visible = limited(items);
      const body = visible.map((item) => {
        const extra = [
          `<div class="tag-row">${chips([item.mode, item.skill_family, item.node_label], "pink")}</div>`,
          proofVisible() && item.practice_steps.length ? `<p>Practice: ${esc(item.practice_steps.join(" / "))}</p>` : "",
          proofVisible() && item.success_signals.length ? `<div class="tag-row">${chips(item.success_signals, "green")}</div>` : "",
          rawVisible() ? `<div class="record-meta">${esc(item.node_skill_id)} / ${fmt(item.link_count)} bridges / best ${fmt(item.best_link_score)}</div>` : ""
        ].join("");
        return record(item.label, `${item.node_label} / ${fmt(item.topic_count)} topics / ${fmt(item.card_count)} cards`, item.description, badge(item.mode, item.mode === "using" ? "cyan" : "gold"), extra);
      }).join("");
      return section("Capability Library", `Showing ${fmt(visible.length)} of ${fmt(items.length)} filtered / ${fmt(DATA.capabilities.length)} total`, `<div class="grid cols-2">${body || `<div class="empty">No capabilities match the current filters.</div>`}</div>${showMore(items.length)}`);
    }
    function renderLineage() {
      let turns = DATA.turns.filter(queryMatch);
      const visibleTurns = sortItems(turns).slice(0, Math.min(state.limit, 160));
      const turnCards = visibleTurns.map((item) => {
        const extra = [
          `<div class="tag-row">${chips([item.platform, item.turn_type, `${fmt(item.learning_link_count)} learning`, `${fmt(item.result_link_count)} results`], "cyan")}</div>`,
          proofVisible() ? `<p>${esc(item.user_excerpt || item.model_response_summary || "")}</p>` : "",
          rawVisible() ? `<div class="record-meta">${esc(item.turn_id)} / ${esc(item.thread_title || "")}</div>` : ""
        ].join("");
        return record(item.objective || item.thread_title || item.turn_id, `${item.turn_started_at || "undated"} / relevance ${fmt(item.hapa_relevance_score)}`, item.model_response_summary, badge(item.platform || "turn", "gold"), extra);
      }).join("");
      let links = DATA.learning_links.filter(queryMatch).slice(0, 80);
      const linkCards = links.map((item) => record(item.source_title || item.skill_label || item.article_title || item.link_id, `${item.source_type} / ${item.source_system || item.platform || ""} / score ${fmt(item.score)}`, item.evidence_text, chips([item.skill_label, item.body_label, item.article_title], "pink"), rawVisible() ? `<div class="record-meta">${esc(item.link_id)} / turn ${esc(item.turn_id)}</div>` : "")).join("");
      return `${section("Turns To Results", `Showing ${fmt(visibleTurns.length)} of ${fmt(turns.length)} filtered / ${fmt(DATA.turns.length)} total`, `<div class="grid cols-2">${turnCards || `<div class="empty">No turns match the current filters.</div>`}</div>${showMore(turns.length)}`)}
      ${section("Learning Evidence Links", `Top ${fmt(links.length)} evidence links from indexed lineage`, `<div class="grid cols-2">${linkCards || `<div class="empty">No learning links match the current filters.</div>`}</div>`)}`;
    }
    function renderSources() {
      let topics = DATA.topics.filter(queryMatch);
      const visibleTopics = topics.slice(0, Math.min(state.limit, 180));
      const sourceCards = DATA.source_systems.slice(0, 18).map((item) => record(item.source_system || "unknown", `${fmt(item.items)} items / ${fmt(item.exposures)} exposures`, `${fmt(item.owned)} owned records`, badge(item.mediums || "source", "cyan"))).join("");
      const mediumCards = DATA.mediums.slice(0, 16).map((item) => record(item.medium || "unknown", `${fmt(item.items)} items`, `${fmt(item.exposures)} exposures`, badge("medium", "gold"))).join("");
      const topicCards = visibleTopics.map((item) => record(item.label, `${item.topic_type} / ${fmt(item.evidence_count)} evidence / ${fmt(item.skill_count)} skills`, item.definition || item.scope_note, chips([item.topic_type, `${fmt(item.item_count)} items`], "green"), rawVisible() ? `<div class="record-meta">${esc(item.topic_id)}</div>` : "")).join("");
      return `${section("Source Systems", "Material and import origins", `<div class="grid cols-3">${sourceCards}</div>`)}
      ${section("Media Types", "Consumption layer", `<div class="grid cols-4">${mediumCards}</div>`)}
      ${section("Topic Profiles", `Showing ${fmt(visibleTopics.length)} of ${fmt(topics.length)} filtered / ${fmt(DATA.topics.length)} total`, `<div class="grid cols-3">${topicCards || `<div class="empty">No topics match the current filters.</div>`}</div>${showMore(topics.length)}`)}`;
    }
    function renderMedia() {
      let items = DATA.media.filter(queryMatch);
      if (state.type !== "all") items = items.filter((item) => item.status === state.type || item.media_type === state.type || item.target_type === state.type);
      const visible = limited(items);
      const body = visible.map((item) => {
        const image = item.preview_path ? `<img src="${esc(item.preview_path)}" alt="">` : "";
        const content = record(item.target_label || item.visual_label || item.job_id, `${item.status} / ${item.provider} / ${item.media_type}`, item.prompt_text || item.direction_prompt || "", chips([item.asset_role, item.target_type, item.node_label, item.turn_skill_family], "pink"), rawVisible() ? `<div class="record-meta">${esc(item.job_id)} / ${esc(item.output_local_path || item.image_url || "")}</div>` : "");
        return `<article class="media-card">${image}${content}</article>`;
      }).join("");
      return section("Media Registry", `Showing ${fmt(visible.length)} of ${fmt(items.length)} filtered / ${fmt(DATA.media.length)} total`, `<div class="media-grid">${body || `<div class="empty">No media jobs match the current filters.</div>`}</div>${showMore(items.length)}`);
    }
    function renderAgents() {
      const body = DATA.agents.filter(queryMatch).map((item) => {
        const extra = [
          `<div class="tag-row">${chips([item.agent_kind, item.status, item.provider, item.model_profile], "cyan")}</div>`,
          proofVisible() ? `<p>${esc(item.description || item.role_summary || "")}</p>` : "",
          rawVisible() ? `<div class="record-meta">${esc(item.agent_id)} / ${fmt(item.local_skill_count)} local skills / ${fmt(item.master_skill_count)} master skills / ${fmt(item.harness_count)} harnesses</div>` : ""
        ].join("");
        return record(item.label, `Score ${fmt(item.score)}`, item.role_summary, badge(`${fmt(item.local_skill_count)} local`, "gold"), extra);
      }).join("");
      return `${section("Agent And Avatar Profiles", "Operating roster", `<div class="grid cols-3">${body || `<div class="empty">No agents match the current filters.</div>`}</div>`)}
      ${section("Harness Context", "Runtime affordances", `<div class="grid cols-3">${DATA.harnesses.map((item) => record(item.label, item.harness_kind || "harness", item.description || item.role_summary || "", chips([item.status, item.provider, item.model_profile], "pink"))).join("") || `<div class="empty">No harness profiles indexed.</div>`}</div>`)}`;
    }
    function renderProtocols() {
      let protocols = DATA.protocols.filter(queryMatch);
      if (state.type !== "all") protocols = protocols.filter((item) => item.article_type === state.type);
      const wiki = protocols.map((item) => record(item.title, `${item.article_type} / updated ${item.updated_at || ""}`, item.summary, badge("wiki", "cyan"), rawVisible() ? `<div class="record-meta">${esc(item.slug)}</div>` : "")).join("");
      const docs = DATA.docs.filter(queryMatch).map((item) => record(item.title, item.kind, item.summary, badge("doc", "gold"), rawVisible() ? `<div class="source-link">${esc(item.path)}</div>` : "")).join("");
      const contracts = DATA.contracts.map((item) => record(item.title, item.kind, item.summary, chips(item.files, "green"))).join("");
      return `${section("Protocol Articles", `Showing ${fmt(protocols.length)} of ${fmt(DATA.protocols.length)} protocol/wiki records`, `<div class="grid cols-2">${wiki || `<div class="empty">No protocol articles match the filters.</div>`}</div>`)}
      ${section("Documentation Spine", "Environment and happ standards", `<div class="grid cols-2">${docs}</div>`)}
      ${section("Happ Contracts", "UI, CLI, API, desktop, web", `<div class="grid cols-3">${contracts}</div>`)}
      ${section("Protocol Visuals", "Media proof cards", `<div class="grid cols-2"><div class="card protocol-line"></div><div class="card avatar-line"></div></div>`)}`;
    }
    function renderBoard() {
      const laneCards = DATA.board.columns.map((item) => record(item.label, `${fmt(item.count)} tasks`, item.description || "", badge(item.label, item.label === "done" ? "green" : item.label === "blocked" ? "rose" : "cyan"))).join("");
      let tasks = DATA.board.tasks.filter(queryMatch);
      if (state.type !== "all") tasks = tasks.filter((item) => item.column === state.type || item.lane === state.type || item.priority === state.type);
      const visible = tasks.slice(0, Math.min(state.limit, 200));
      const taskCards = visible.map((item) => record(item.title, `${item.column} / ${item.lane} / ${item.priority}`, item.description, chips([item.owner, item.node, ...(item.tags || [])], "cyan"), proofVisible() ? `<div class="tag-row">${chips(item.acceptance, "green")}</div>` : "")).join("");
      const eventCards = DATA.board.events.slice(0, 24).map((item) => record(item.payload_title || item.type, `${item.ts} / ${item.actor}`, item.payload_body || item.task_id || "", badge(item.type, "gold"))).join("");
      return `${section("Board Columns", "Quest state", `<div class="grid cols-4">${laneCards}</div>`)}
      ${section("Task Cards", `Showing ${fmt(visible.length)} of ${fmt(tasks.length)} filtered / ${fmt(DATA.board.tasks.length)} total`, `<div class="grid cols-2">${taskCards || `<div class="empty">No board cards match the current filters.</div>`}</div>${showMore(tasks.length)}`)}
      ${section("Append-Only Events", "Protocol record", `<div class="grid cols-2">${eventCards}</div>`)}`;
    }
    function gameTabs() {
      return `<nav class="game-tabs">${Object.entries(gamePanelInfo).map(([key, info]) => `<button type="button" data-game-panel="${key}" class="${state.gamePanel === key ? "active" : ""}">${esc(info[0])}</button>`).join("")}</nav>`;
    }
    function mockGallery() {
      return `<div class="mock-gallery">${gameMocks.map(([label, path]) => `<img src="${esc(path)}" alt="${esc(label)} mock">`).join("")}</div>`;
    }
    function dataAttrs(attrs) {
      return Object.entries(attrs || {}).filter(([, value]) => value !== undefined && value !== null && value !== "").map(([key, value]) => ` ${key}="${esc(value)}"`).join("");
    }
    function cleanImageUrl(value) {
      return String(value || DATA.image_sources?.default_url || "hapa-character-sheet-game-mock-04-mobile-passport.png").replace(/["\\\n\r]/g, "");
    }
    function cleanAssetUrl(value) {
      return String(value || "").replace(/["\\\n\r]/g, "");
    }
    function cssImageValue(value) {
      return `url("${cleanImageUrl(value)}")`;
    }
    function cssImageStyleVar(name, value) {
      return `${name}:${cssImageValue(value)};`;
    }
    function defaultCharacterModel() {
      return (DATA.character_models?.items || [])[0] || null;
    }
    function modelPosterStyle(model) {
      return model?.poster ? cssImageStyleVar("--model-poster", model.poster) : cssImageStyleVar("--model-poster", state.imageSrc);
    }
    function characterModelStage() {
      const model = defaultCharacterModel();
      if (!model?.url) return `<div class="portrait-art"></div>`;
      const quality = skillQualityData();
      const topQuality = quality.skill_quality?.[0] || {};
      const topPair = quality.top_pairs?.[0] || {};
      const source = cleanAssetUrl(model.url);
      const poster = cleanAssetUrl(model.poster || state.imageSrc);
      return `<div class="portrait-art model-stage" style="${esc(modelPosterStyle(model))}">
        <video class="character-model-video" src="${esc(source)}" poster="${esc(poster)}" autoplay loop muted playsinline preload="auto" aria-label="${esc(model.label || "Character model video loop")}"></video>
        <span class="model-reticle" aria-hidden="true"></span>
        <div class="model-hud" aria-hidden="true">
          <div class="model-hud-row">
            <span class="model-status-chip">Live Model</span>
            <span class="model-status-chip model-rank-chip">Q ${esc(topQuality.quality_band || "S")} / EXP ${esc(topPair.experience_band || "S")}</span>
          </div>
          <span class="model-class-chip">${esc(model.display_role || "Character Model")} / ${esc(model.kind || "video")}</span>
        </div>
      </div>`;
    }
    function characterModelCard() {
      const model = defaultCharacterModel();
      if (!model) return "";
      return `<div class="game-card character-model-panel"><h4>Character Model</h4>
        <div class="model-callout" style="${esc(modelPosterStyle(model))}">
          <span class="model-callout-thumb" aria-hidden="true"></span>
          <span><strong>${esc(model.label)}</strong><span>${esc(model.meta || "looping video model")}</span></span>
        </div>
        <div class="game-list">
          ${gameListRow("Model Type", model.kind || "looping_video")}
          ${gameListRow("Resolution", model.resolution || "720 x 1280")}
          ${gameListRow("Duration", model.duration || "10s seamless loop")}
          ${gameListRow("Slot", model.display_role || "Hero Character Model")}
        </div>
      </div>`;
    }
    function imageSourceLabel(kind) {
      return {
        avatar: "Avatars",
        asset_viewer: "Asset Mgr",
        media_registry: "Media",
        character_model: "Model",
        character_sheet: "Sheet"
      }[kind] || kind;
    }
    function selectedImageSource() {
      return (DATA.image_sources?.items || []).find((item) => item.url === state.imageSrc) || { label: state.imageLabel, source_app: "Custom", kind: "custom", url: state.imageSrc, meta: "local selection" };
    }
    function applyCharacterImage() {
      document.documentElement.style.setProperty("--selected-character-image", cssImageValue(state.imageSrc));
    }
    function setCharacterImage(url, label = "Custom Image", filter = state.imageFilter) {
      if (!url) return;
      state.imageSrc = cleanImageUrl(url);
      state.imageLabel = label || "Custom Image";
      state.imageFilter = filter || state.imageFilter;
      try {
        localStorage.setItem("hapaCharacterSheetImageSrc", state.imageSrc);
        localStorage.setItem("hapaCharacterSheetImageLabel", state.imageLabel);
        localStorage.setItem("hapaCharacterSheetImageFilter", state.imageFilter);
      } catch (err) {
        // Large data URLs can exceed localStorage; keep the in-memory selection for this session.
      }
      playTone("select");
      render();
    }
    function resetCharacterImage() {
      state.imageSrc = DATA.image_sources?.default_url || "hapa-character-sheet-game-mock-04-mobile-passport.png";
      state.imageLabel = DATA.image_sources?.default_label || "Calder Character Model Poster";
      try {
        localStorage.removeItem("hapaCharacterSheetImageSrc");
        localStorage.removeItem("hapaCharacterSheetImageLabel");
      } catch (err) {}
      playTone("change");
      render();
    }
    function imageSourceRows() {
      const items = (DATA.image_sources?.items || []).filter((item) => state.imageFilter === "all" || item.kind === state.imageFilter).slice(0, 28);
      return items.map((item) => {
        const selected = item.url === state.imageSrc ? " selected" : "";
        return `<button type="button" class="image-source-row interactive${selected}" data-image-source="${esc(item.id)}" aria-selected="${selected ? "true" : "false"}">
          <span class="image-source-thumb" style="${esc(cssImageStyleVar("--source-image", item.url))}" aria-hidden="true"></span>
          <span><strong>${esc(item.label)}</strong><span>${esc(item.source_app)} / ${esc(item.meta || item.kind)}</span></span>
          <em>${esc(imageSourceLabel(item.kind))}</em>
        </button>`;
      }).join("") || `<div class="empty">No image sources indexed for this lane.</div>`;
    }
    function imageManager() {
      const source = selectedImageSource();
      const links = DATA.image_sources?.app_links || {};
      const filters = [
        ["character_model", "Model"],
        ["avatar", "Avatars"],
        ["asset_viewer", "Asset Mgr"],
        ["media_registry", "Media"],
        ["character_sheet", "Sheet"]
      ];
      return `<div class="game-card image-manager"><h4>Image Source</h4>
        <div class="image-preview"></div>
        <div class="record-meta" style="margin-top:8px">${esc(source.label || state.imageLabel)} / ${esc(source.source_app || "Custom")}</div>
        <div class="source-links">
          ${links.avatar_dashboard ? `<a href="${esc(links.avatar_dashboard)}" target="_blank" rel="noreferrer">Avatar Dashboard</a>` : ""}
          ${links.asset_viewer ? `<a href="${esc(links.asset_viewer)}" target="_blank" rel="noreferrer">Asset Viewer</a>` : ""}
        </div>
        <div class="image-source-filters">${filters.map(([key, label]) => `<button type="button" data-image-filter="${esc(key)}" class="${state.imageFilter === key ? "active" : ""}">${esc(label)}</button>`).join("")}</div>
        <div class="image-source-list">${imageSourceRows()}</div>
        <div class="image-actions">
          <input type="url" data-image-url-input placeholder="https:// or file:// image URL" value="">
          <button type="button" data-image-url-apply>Apply</button>
        </div>
        <div class="image-apply-row">
          <label class="image-file-label">Local File<input class="image-file-input" data-image-file type="file" accept="image/*"></label>
          <button type="button" data-image-reset>Reset</button>
        </div>
      </div>`;
    }
    function gameListRow(label, value, cls = "", detailKey = "") {
      const selected = detailKey && state.passportFocus === detailKey ? " selected" : "";
      const attrs = detailKey ? dataAttrs({ "data-passport-detail": detailKey, "aria-selected": state.passportFocus === detailKey ? "true" : "false" }) : "";
      return `<div class="game-list-row interactive${selected}" role="button" tabindex="0"${attrs}><span>${esc(label)}</span><strong class="${cls}">${esc(value)}</strong></div>`;
    }
    function passportChip(value, label, detailKey) {
      const selected = state.passportFocus === detailKey ? " selected" : "";
      return `<div class="proof-chip-big interactive${selected}" role="button" tabindex="0" data-passport-detail="${esc(detailKey)}" aria-selected="${state.passportFocus === detailKey ? "true" : "false"}"><strong>${fmt(value)}</strong><span>${esc(label)}</span></div>`;
    }
    function lowerTiles(items) {
      return `<div class="lower-grid">${items.slice(0, 8).map((item) => `<div class="lower-tile"><strong>${esc(item.value)}</strong><span>${esc(item.label)}</span></div>`).join("")}</div>`;
    }
    function exampleList(items) {
      return `<div class="example-list">${items.slice(0, 6).map((item) => `<div class="example-card"><strong>${esc(item.title)}</strong><span>${esc(item.meta || "")}</span>${item.body ? `<span>${esc(item.body)}</span>` : ""}</div>`).join("")}</div>`;
    }
    function aggregateBy(items, key, valueKey) {
      const map = new Map();
      for (const item of items || []) {
        const label = item[key] || "unknown";
        const value = Number(valueKey ? item[valueKey] || 0 : 1);
        map.set(label, (map.get(label) || 0) + value);
      }
      return [...map.entries()].sort((a, b) => b[1] - a[1]).map(([label, value]) => ({ label, value: fmt(value) }));
    }
    function proofLayers() {
      const protocolCount = DATA.protocols.length + DATA.docs.length + DATA.contracts.length;
      return [
        {
          key: "sources", label: "Sources", code: "SR", value: DATA.summary.items, meta: `${fmt(DATA.summary.exposures)} exposures`, cls: "cyan", x: 15, y: 22,
          body: "Source material is the intake layer: wiki records, videos, cards, artifacts, reading, music, dependencies, and watched media that taught or seeded later work.",
          lower: DATA.source_systems.slice(0, 8).map((item) => ({ label: item.source_system || "unknown", value: fmt(item.items) })),
          examples: DATA.source_systems.slice(0, 6).map((item) => ({ title: item.source_system || "unknown", meta: `${fmt(item.items)} items / ${fmt(item.exposures)} exposures`, body: item.mediums || "source system" })),
          facts: [["Items", DATA.summary.items], ["Exposures", DATA.summary.exposures], ["Mediums", DATA.mediums.length]]
        },
        {
          key: "turns", label: "Turns", code: "AI", value: DATA.summary.turns, meta: `${fmt(DATA.summary.turn_learning_links)} learning links`, cls: "gold", x: 50, y: 10,
          body: "AI turns are indexed as applied practice: prompt objective, model response summary, learning links, result links, and reusable wisdom cards.",
          lower: aggregateBy(DATA.turns, "platform").slice(0, 8),
          examples: DATA.turns.slice(0, 6).map((turn) => ({ title: turn.objective || turn.thread_title || turn.turn_id, meta: `${turn.platform || "turn"} / score ${fmt(turn.hapa_relevance_score)}`, body: turn.model_response_summary })),
          facts: [["Turns", DATA.summary.turns], ["Learning", DATA.summary.turn_learning_links], ["Results", DATA.summary.turn_result_links]]
        },
        {
          key: "skills", label: "Skills", code: "SK", value: DATA.skills.length, meta: `${fmt(DATA.summary.skill_evidence)} evidence XP`, cls: "pink", x: 84, y: 22,
          body: "Skills are the consolidated capability layer. They compress consumed material, turns, artifacts, and enrichment into professional skill families.",
          lower: DATA.skill_families.slice(0, 8).map((family) => ({ label: prettyFamily(family.label), value: `${fmt(family.skill_count)} skills` })),
          examples: DATA.skills.slice(0, 6).map((skill) => ({ title: skill.label, meta: `${prettyFamily(skill.skill_family)} / ${skill.rank} / ${fmt(skill.evidence_count)} XP`, body: skill.summary })),
          facts: [["Skills", DATA.skills.length], ["Families", DATA.skill_families.length], ["Evidence", DATA.summary.skill_evidence]]
        },
        {
          key: "nodes", label: "Nodes", code: "ND", value: DATA.nodes.length, meta: `${fmt(DATA.summary.node_skills)} node skills`, cls: "rose", x: 86, y: 55,
          body: "Hapa nodes are the portfolio and operating artifacts: apps, protocols, workflows, maps, existing nodes, proposed nodes, and generated surfaces.",
          lower: DATA.node_type_summary.slice(0, 8).map((item) => ({ label: prettyFamily(item.label), value: fmt(item.count) })),
          examples: DATA.nodes.slice(0, 6).map((node) => ({ title: node.label, meta: `${node.node_type} / ${fmt(node.topic_count)} topics / ${fmt(node.card_count)} cards`, body: node.description })),
          facts: [["Nodes", DATA.nodes.length], ["Topics", DATA.nodes.reduce((sum, node) => sum + Number(node.topic_count || 0), 0)], ["Cards", DATA.nodes.reduce((sum, node) => sum + Number(node.card_count || 0), 0)]]
        },
        {
          key: "capabilities", label: "Capabilities", code: "CP", value: DATA.capabilities.length, meta: `${fmt(DATA.summary.capability_bridges)} bridges`, cls: "cyan", x: 68, y: 84,
          body: "Capabilities connect general skills to Hapa nodes through using/enhancing modes, practice steps, success signals, bodies, topics, cards, and bridge counts.",
          lower: aggregateBy(DATA.capabilities, "mode").slice(0, 8),
          examples: DATA.capabilities.slice(0, 6).map((cap) => ({ title: cap.label, meta: `${cap.mode} / ${cap.node_label} / ${fmt(cap.link_count)} bridges`, body: cap.description })),
          facts: [["Node Skills", DATA.capabilities.length], ["Bridges", DATA.summary.capability_bridges], ["Modes", aggregateBy(DATA.capabilities, "mode").length]]
        },
        {
          key: "media", label: "Media", code: "MD", value: DATA.media.length, meta: `${fmt(DATA.image_sources?.items?.length || 0)} image sources`, cls: "green", x: 32, y: 84,
          body: "Media is the outward proof layer: generated images, cards, avatars, queue records, screenshots, videos, prompts, targets, and presentation artifacts.",
          lower: aggregateBy(DATA.media, "status").slice(0, 8),
          examples: DATA.media.slice(0, 6).map((media) => ({ title: media.target_label || media.visual_label || media.job_id, meta: `${media.status} / ${media.provider} / ${media.media_type}`, body: media.prompt_text || media.direction_prompt })),
          facts: [["Media Jobs", DATA.media.length], ["Generated", DATA.media.filter((item) => item.status === "generated").length], ["Image Sources", DATA.image_sources?.items?.length || 0]]
        },
        {
          key: "agents", label: "Agents", code: "AG", value: DATA.agents.length + DATA.harnesses.length, meta: `${fmt(DATA.harnesses.length)} harnesses`, cls: "green", x: 10, y: 55,
          body: "Agents and harnesses are operating profiles: who can use the proof, which avatar/agent context they carry, and what local runtime affordances support them.",
          lower: [{ label: "agents", value: fmt(DATA.agents.length) }, { label: "harnesses", value: fmt(DATA.harnesses.length) }, { label: "local skills", value: fmt(DATA.agents.reduce((sum, agent) => sum + Number(agent.local_skill_count || 0), 0)) }],
          examples: [...DATA.agents, ...DATA.harnesses].slice(0, 6).map((agent) => ({ title: agent.label, meta: agent.agent_kind || agent.harness_kind || "agent", body: agent.role_summary || agent.description })),
          facts: [["Agents", DATA.agents.length], ["Harnesses", DATA.harnesses.length], ["Profiles", DATA.agents.length + DATA.harnesses.length]]
        },
        {
          key: "protocols", label: "Protocols", code: "PR", value: protocolCount, meta: `${fmt(DATA.contracts.length)} contracts`, cls: "gold", x: 50, y: 68,
          body: "Protocols make the proof reusable. They define docs, manifests, API/CLI contracts, flow sidecars, board events, wiki articles, and operating standards.",
          lower: [{ label: "wiki protocols", value: fmt(DATA.protocols.length) }, { label: "docs", value: fmt(DATA.docs.length) }, { label: "contracts", value: fmt(DATA.contracts.length) }],
          examples: [...DATA.protocols.map((item) => ({ title: item.title, meta: item.article_type || "protocol", body: item.summary })), ...DATA.docs.map((item) => ({ title: item.title, meta: item.kind || "doc", body: item.summary })), ...DATA.contracts.map((item) => ({ title: item.title, meta: item.kind || "contract", body: item.summary }))].slice(0, 6),
          facts: [["Protocols", DATA.protocols.length], ["Docs", DATA.docs.length], ["Contracts", DATA.contracts.length]]
        }
      ];
    }
    function proofLayerByKey(key) {
      const layers = proofLayers();
      return layers.find((layer) => layer.key === key) || layers.find((layer) => layer.key === "skills") || layers[0];
    }
    function setProofFocus(key) {
      state.proofFocus = key || "skills";
      state.gamePanel = "proof";
      state.view = "presentation";
      window.location.hash = `presentation-proof&proof=${encodeURIComponent(state.proofFocus)}`;
      playTone("select");
      render();
    }
    function proofLayerRow(layer) {
      const selected = state.proofFocus === layer.key ? " selected" : "";
      return `<button type="button" class="proof-layer-row interactive${selected}" data-proof-focus="${esc(layer.key)}" aria-selected="${selected ? "true" : "false"}">
        <span class="proof-layer-icon">${esc(layer.code)}</span>
        <span><strong>${esc(layer.label)}</strong><span>${esc(layer.meta)}</span></span>
        <em>${fmt(layer.value)}</em>
      </button>`;
    }
    function proofEdges(layers) {
      const pos = Object.fromEntries(layers.map((layer) => [layer.key, layer]));
      const chain = [["sources", "turns"], ["turns", "skills"], ["skills", "nodes"], ["nodes", "capabilities"], ["capabilities", "media"], ["capabilities", "agents"], ["media", "protocols"], ["agents", "protocols"], ["protocols", "sources"]];
      const center = layers.map((layer) => `<line class="${state.proofFocus === layer.key ? "selected" : ""}" x1="50" y1="50" x2="${layer.x}" y2="${layer.y}"></line>`).join("");
      const chainLines = chain.filter(([a, b]) => pos[a] && pos[b]).map(([a, b]) => `<line class="chain ${state.proofFocus === a || state.proofFocus === b ? "selected" : ""}" x1="${pos[a].x}" y1="${pos[a].y}" x2="${pos[b].x}" y2="${pos[b].y}"></line>`).join("");
      return `<svg class="proof-edges" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">${center}${chainLines}</svg>`;
    }
    function proofFlowSteps() {
      const steps = [
        ["Read", DATA.summary.items, "sources", "source intake"],
        ["Practice", DATA.summary.turns, "turns", "AI turn proof"],
        ["Learn", DATA.skills.length, "skills", "skill consolidation"],
        ["Build", DATA.nodes.length, "nodes", "portfolio nodes"],
        ["Prove", DATA.capabilities.length, "capabilities", "capability bridges"],
        ["Publish", DATA.media.length, "media", "media artifacts"]
      ];
      return `<div class="proof-flow-strip">${steps.map(([label, value, key, meta]) => `<button type="button" class="proof-flow-step interactive${state.proofFocus === key ? " selected" : ""}" data-proof-focus="${esc(key)}"><strong>${esc(label)}</strong><span>${fmt(value)}</span><small>${esc(meta)}</small></button>`).join("")}</div>`;
    }
    function proofFactRows(layer) {
      return `<div class="game-list">${(layer.facts || []).map(([label, value]) => codexFactRow(label, fmt(value))).join("")}</div>`;
    }
    function proofMiniPanel(title, rows) {
      return `<aside class="game-card proof-mini-panel"><h4>${esc(title)}</h4><div class="game-list">${rows.map((item) => gameListRow(item.label, item.value)).join("")}</div></aside>`;
    }
    function prettyFamily(value) {
      return String(value || "unknown").replaceAll("_", " ");
    }
    function initials(value) {
      const parts = String(value || "HA").replace(/[^A-Za-z0-9 ]/g, " ").trim().split(/\s+/).filter(Boolean);
      const letters = parts.slice(0, 2).map((part) => part[0]).join("").toUpperCase();
      return (letters || "HA").slice(0, 2);
    }
    function familyIndex(family) {
      const index = DATA.skill_families.findIndex((item) => item.label === family);
      if (index >= 0) return index;
      return Math.abs(String(family || "").split("").reduce((sum, char) => sum + char.charCodeAt(0), 0)) % 8;
    }
    function familySpriteStyle(family) {
      const slot = familyIndex(family) % 8;
      const col = slot % 4;
      const row = Math.floor(slot / 4);
      return `--sprite-x:${col * 33.3333}%;--sprite-y:${row * 100}%;`;
    }
    function familyThumb(family, cls = "") {
      return `<span class="family-thumb ${esc(cls)}" style="${familySpriteStyle(family)}" aria-hidden="true"></span>`;
    }
    function stableIndex(value, modulo) {
      const text = String(value || "");
      let hash = 0;
      for (let index = 0; index < text.length; index += 1) {
        hash = (hash * 31 + text.charCodeAt(index)) >>> 0;
      }
      return modulo ? hash % modulo : hash;
    }
    function selectedCodexSkill(family) {
      let skill = DATA.skills.find((item) => item.skill_id === state.codexSkillId);
      if (!skill || (family && skill.skill_family !== family)) {
        skill = skillsForFamily(family)[0] || DATA.skills[0] || {};
      }
      state.codexSkillId = skill.skill_id || "";
      return skill;
    }
    function skillLoopForSelection(family, capability, skill) {
      const loops = DATA.skill_video_loops?.items || [];
      if (!loops.length) return null;
      const key = [skill?.skill_id, capability?.node_skill_id, family].filter(Boolean).join("|");
      return loops[stableIndex(key || family || "skill-loop", loops.length)];
    }
    function skillLoopStage(family, capability, skill) {
      const loop = skillLoopForSelection(family, capability, skill);
      if (!loop?.url) return `<div class="tree-core">Knowledge<br>Architect</div>`;
      const title = skill?.label || capability?.label || prettyFamily(family);
      const meta = [prettyFamily(family), skill?.rank || capability?.mode || "skill", loop.verb || "Loop"].filter(Boolean).join(" / ");
      return `<div class="tree-core skill-loop-core">
        <video class="skill-loop-video" src="${esc(cleanAssetUrl(loop.url))}" poster="${esc(cleanAssetUrl(loop.poster || ""))}" autoplay loop muted playsinline preload="auto" aria-label="${esc(title)} skill loop"></video>
        <div class="skill-loop-chip-row"><span class="skill-loop-chip">Skill Loop</span><span class="skill-loop-chip">${esc(loop.verb || "Loop")}</span></div>
        <div class="skill-loop-hud"><strong>${esc(title)}</strong><span>${esc(meta)}</span><span>${esc(loop.meta || "video skill preview")}</span></div>
      </div>`;
    }
    function nodeTypeClass(type) {
      return `node-type-${String(type || "node").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "")}`;
    }
    function nodeTypeLabel(type) {
      return prettyFamily(type || "hapa node");
    }
    function nodeTypeTheme(node) {
      const type = String(node?.node_type || "").toLowerCase();
      if (type === "existing_node") return ["#22d3ee", "#2563eb", "#a7f3d0"];
      if (type === "proposed_node") return ["#f472b6", "#7c3aed", "#fbbf24"];
      if (type === "hapa_node") return ["#34d399", "#0891b2", "#67e8f9"];
      if (type === "cymatica_node") return ["#fbbf24", "#db2777", "#c4b5fd"];
      if (type === "node_map") return ["#38bdf8", "#14b8a6", "#f0abfc"];
      return ["#22d3ee", "#a855f7", "#fbbf24"];
    }
    function nodeThemeStyle(node) {
      const [a, b, c] = nodeTypeTheme(node);
      return `--node-a:${a};--node-b:${b};--node-c:${c};`;
    }
    function nodeThumb(node, cls = "") {
      return `<span class="node-thumb ${esc(nodeTypeClass(node?.node_type))} ${esc(cls)}" style="${nodeThemeStyle(node)}" aria-hidden="true"><span class="node-thumb-mark"></span><strong>${esc(initials(node?.label || node?.node_label || "HN"))}</strong></span>`;
    }
    function uniqueBy(items, keyFn) {
      const seen = new Set();
      return (items || []).filter((item) => {
        const key = keyFn(item);
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      });
    }
    function skillsForFamily(family) {
      return DATA.skills.filter((skill) => skill.skill_family === family);
    }
    function capabilityFamilyMatch(capability, family, skillNames = null) {
      if (!capability || !family) return false;
      if (capability.skill_family === family) return true;
      const names = skillNames || new Set(skillsForFamily(family).map((skill) => String(skill.label || "").toLowerCase()));
      return (capability.connected_skills || []).some((skill) => names.has(String(skill || "").toLowerCase()));
    }
    function capabilitiesForFamily(family) {
      const familySkills = skillsForFamily(family);
      const skillNames = new Set(familySkills.map((skill) => String(skill.label || "").toLowerCase()));
      const matches = DATA.capabilities.filter((capability) => capabilityFamilyMatch(capability, family, skillNames));
      if (matches.length) return uniqueBy(matches, (capability) => capability.node_skill_id);
      const familySlot = Math.max(0, familyIndex(family));
      return uniqueBy(DATA.capabilities.filter((_, index) => index % Math.max(1, DATA.skill_families.length) === familySlot), (capability) => capability.node_skill_id).slice(0, 12);
    }
    function familyForCapability(capability) {
      const match = DATA.skill_families.find((family) => capabilityFamilyMatch(capability, family.label));
      return match?.label || state.codexFamily || DATA.skill_families[0]?.label || "";
    }
    function defaultCapabilityForFamily(family) {
      const caps = capabilitiesForFamily(family);
      const byNode = uniqueBy(caps, (capability) => capability.node_id || capability.node_label || capability.node_skill_id);
      const pool = byNode.length ? byNode : caps;
      return pool[familyIndex(family) % Math.max(1, pool.length)] || DATA.capabilities[0] || {};
    }
    function selectedCodexCapability(family) {
      const familyCaps = capabilitiesForFamily(family);
      let selected = DATA.capabilities.find((capability) => capability.node_skill_id === state.codexCapabilityId);
      if (!state.codexCapabilityId || !selected || !familyCaps.some((capability) => capability.node_skill_id === selected.node_skill_id)) {
        selected = defaultCapabilityForFamily(family);
      }
      return selected;
    }
    function nodesForFamily(family) {
      const caps = capabilitiesForFamily(family);
      const ids = new Set(caps.map((capability) => capability.node_id).filter(Boolean));
      const matched = DATA.nodes.filter((node) => ids.has(node.node_id));
      if (matched.length) return uniqueBy(matched, (node) => node.node_id);
      const slot = Math.max(0, familyIndex(family));
      return DATA.nodes.filter((_, index) => index % Math.max(1, DATA.skill_families.length) === slot).slice(0, 12);
    }
    function codexTags(items, cls = "green", limit = 10) {
      const tags = (items || []).filter(Boolean).slice(0, limit).map((item) => badge(item, cls)).join("");
      return tags || badge("No pinned signals yet", "cyan");
    }
    function codexFactRow(label, value) {
      return `<div class="game-list-row"><span>${esc(label)}</span><strong>${esc(value)}</strong></div>`;
    }
    function setCodexHash() {
      window.location.hash = `presentation-codex&family=${encodeURIComponent(state.codexFamily || "")}&cap=${encodeURIComponent(state.codexCapabilityId || "")}&skill=${encodeURIComponent(state.codexSkillId || "")}`;
    }
    function selectCodexFamily(family) {
      state.codexFamily = family || DATA.skill_families[0]?.label || "";
      const selected = defaultCapabilityForFamily(state.codexFamily);
      state.codexCapabilityId = selected.node_skill_id || "";
      state.codexSkillId = skillsForFamily(state.codexFamily)[0]?.skill_id || "";
      state.gamePanel = "codex";
      state.view = "presentation";
      setCodexHash();
      render();
    }
    function selectCodexCapability(capabilityId) {
      const selected = DATA.capabilities.find((capability) => capability.node_skill_id === capabilityId) || DATA.capabilities[0] || {};
      state.codexCapabilityId = selected.node_skill_id || "";
      state.codexFamily = capabilityFamilyMatch(selected, state.codexFamily) ? state.codexFamily : familyForCapability(selected);
      const connected = (selected.connected_skills || []).map((label) => String(label || "").toLowerCase());
      const matchedSkill = DATA.skills.find((skill) => skill.skill_family === state.codexFamily && connected.includes(String(skill.label || "").toLowerCase()));
      state.codexSkillId = matchedSkill?.skill_id || skillsForFamily(state.codexFamily)[0]?.skill_id || "";
      state.gamePanel = "codex";
      state.view = "presentation";
      setCodexHash();
      render();
    }
    function selectCodexNode(nodeId) {
      const selected = DATA.capabilities.find((capability) => capability.node_id === nodeId) || DATA.capabilities.find((capability) => capability.node_label === nodeId) || DATA.capabilities[0] || {};
      state.codexCapabilityId = selected.node_skill_id || "";
      state.codexFamily = capabilityFamilyMatch(selected, state.codexFamily) ? state.codexFamily : familyForCapability(selected);
      state.codexSkillId = skillsForFamily(state.codexFamily)[0]?.skill_id || "";
      state.gamePanel = "codex";
      state.view = "presentation";
      setCodexHash();
      render();
    }
    function selectCodexSkill(skillId) {
      const selected = DATA.skills.find((skill) => skill.skill_id === skillId) || DATA.skills[0] || {};
      state.codexSkillId = selected.skill_id || "";
      state.codexFamily = selected.skill_family || state.codexFamily || DATA.skill_families[0]?.label || "";
      const cap = defaultCapabilityForFamily(state.codexFamily);
      state.codexCapabilityId = cap.node_skill_id || state.codexCapabilityId || "";
      state.gamePanel = "codex";
      state.view = "presentation";
      setCodexHash();
      render();
    }
    function codexSkillInventory(selectedFamily) {
      return DATA.skill_families.map((family) => {
        const rows = skillsForFamily(family.label).map((skill) => {
          const selected = skill.skill_id === state.codexSkillId ? " selected" : "";
          return `<button type="button" class="inventory-item interactive${selected}" data-codex-family="${esc(family.label)}" data-codex-skill-id="${esc(skill.skill_id)}" aria-selected="${selected ? "true" : "false"}">
            ${familyThumb(skill.skill_family, "small")}
            <span><strong>${esc(skill.label)}</strong><span>${fmt(skill.evidence_count)} XP / ${fmt(skill.artifact_count)} artifacts</span></span>
            <em>${esc(skill.rank)}</em>
          </button>`;
        }).join("");
        return `<div class="inventory-group">
          <div class="inventory-group-title"><span>${esc(prettyFamily(family.label))}</span><span>${fmt(family.skill_count)} skills</span></div>
          ${rows}
        </div>`;
      }).join("");
    }
    function codexNodeInventory(selectedCapability) {
      const grouped = new Map();
      for (const node of DATA.nodes) {
        const key = node.node_type || "node";
        if (!grouped.has(key)) grouped.set(key, []);
        grouped.get(key).push(node);
      }
      return [...grouped.entries()].map(([type, nodes]) => {
        const rows = nodes.map((node) => {
          const selected = selectedCapability?.node_id === node.node_id ? " selected" : "";
          return `<button type="button" class="inventory-item interactive${selected}" data-codex-node-id="${esc(node.node_id)}" aria-selected="${selected ? "true" : "false"}">
            ${nodeThumb(node, "small")}
            <span><strong>${esc(node.label)}</strong><span>${fmt(node.topic_count)} topics / ${fmt(node.card_count)} cards</span></span>
            <em>${esc(node.node_type || "node")}</em>
          </button>`;
        }).join("");
        return `<div class="inventory-group">
          <div class="inventory-group-title"><span>${esc(type.replaceAll("_", " "))}</span><span>${fmt(nodes.length)} nodes</span></div>
          ${rows}
        </div>`;
      }).join("");
    }
    function timelineLayers() {
      return [{ key: "all", label: "All Canon", count: DATA.timeline?.summary?.timeline_events || 0 }, ...(DATA.timeline?.layers || [])];
    }
    function timelineLayerMeta(key) {
      return timelineLayers().find((layer) => layer.key === key) || timelineLayers()[0] || { key: "all", label: "All Canon", count: 0 };
    }
    function timelineLayerCode(key) {
      return { all: "ALL", knowledge: "KN", turns: "AI", skills: "SK", nodes: "ND", capabilities: "CP" }[key] || initials(key);
    }
    function timelineLayerClass(key) {
      return `timeline-layer-${String(key || "all").replace(/[^a-z0-9]+/g, "-")}`;
    }
    function timelineScales() {
      const summary = DATA.timeline?.summary || {};
      return [
        { key: "day", label: "Daily", count: summary.daily_buckets || 0, body: "Day-by-day canon: exact workdays, unlocks, turns, nodes, and knowledge intake." },
        { key: "week", label: "Weekly", count: summary.weekly_buckets || 0, body: "Sprint-scale view for clusters of practice and build momentum." },
        { key: "month", label: "Monthly", count: summary.monthly_buckets || 0, body: "Campaign-scale history across eras, skill growth, and source waves." },
        { key: "year", label: "Yearly", count: summary.yearly_buckets || 0, body: "Long-arc canon, roots, and professional evolution." }
      ];
    }
    function timelineScaleMeta(key) {
      return timelineScales().find((scale) => scale.key === key) || timelineScales()[2];
    }
    function timelineSeriesRows() {
      const scale = timelineScaleMeta(state.timelineScale).key;
      return (DATA.timeline?.series_by_scale || {})[scale] || DATA.timeline?.series || [];
    }
    function timelineSeriesLimit() {
      return { day: 180, week: 156, month: 96, year: 120 }[timelineScaleMeta(state.timelineScale).key] || 96;
    }
    function timelineDateLabel(value) {
      if (!value) return "Undated";
      return String(value).slice(0, 10);
    }
    function timelineEraById(id) {
      return (DATA.timeline?.eras || []).find((era) => era.id === id) || null;
    }
    function setTimelineHash() {
      window.location.hash = `presentation-timeline&scale=${encodeURIComponent(state.timelineScale || "month")}&era=${encodeURIComponent(state.timelineEra || "all")}&layer=${encodeURIComponent(state.timelineLayer || "all")}&beat=${encodeURIComponent(state.timelineBeatId || "")}`;
    }
    function timelineFilteredBeats() {
      let beats = DATA.timeline?.beats || [];
      if (state.timelineLayer && state.timelineLayer !== "all") beats = beats.filter((beat) => beat.layer === state.timelineLayer);
      if (state.timelineEra && state.timelineEra !== "all") beats = beats.filter((beat) => beat.era_id === state.timelineEra);
      return beats;
    }
    function selectedTimelineBeat() {
      const filtered = timelineFilteredBeats();
      let selected = filtered.find((beat) => beat.id === state.timelineBeatId) || (DATA.timeline?.beats || []).find((beat) => beat.id === state.timelineBeatId);
      if (!selected) selected = filtered[0] || (DATA.timeline?.beats || [])[0] || {};
      state.timelineBeatId = selected.id || "";
      return selected;
    }
    function selectTimelineBeat(beatId) {
      state.timelineBeatId = beatId || "";
      state.gamePanel = "timeline";
      state.view = "presentation";
      setTimelineHash();
      render();
    }
    function selectTimelineLayer(layer) {
      state.timelineLayer = layer || "all";
      const filtered = timelineFilteredBeats();
      if (!filtered.some((beat) => beat.id === state.timelineBeatId)) state.timelineBeatId = filtered[0]?.id || "";
      state.gamePanel = "timeline";
      state.view = "presentation";
      setTimelineHash();
      render();
    }
    function selectTimelineEra(eraId) {
      state.timelineEra = eraId || "all";
      const filtered = timelineFilteredBeats();
      if (!filtered.some((beat) => beat.id === state.timelineBeatId)) state.timelineBeatId = filtered[0]?.id || "";
      state.gamePanel = "timeline";
      state.view = "presentation";
      setTimelineHash();
      render();
    }
    function selectTimelineScale(scale) {
      state.timelineScale = timelineScaleMeta(scale).key;
      state.gamePanel = "timeline";
      state.view = "presentation";
      setTimelineHash();
      render();
    }
    function timelineScaleRail() {
      return `<div class="timeline-scale-rail">${timelineScales().map((scale) => {
        const selected = timelineScaleMeta(state.timelineScale).key === scale.key ? " selected" : "";
        return `<button type="button" class="timeline-scale-card interactive${selected}" data-timeline-scale="${esc(scale.key)}" aria-selected="${selected ? "true" : "false"}"><strong>${esc(scale.label)}</strong><span>${fmt(scale.count || 0)} buckets</span><p>${esc(scale.body)}</p></button>`;
      }).join("")}</div>`;
    }
    function timelineDailyBrief() {
      const daily = DATA.timeline?.daily_summary || {};
      const active = timelineScaleMeta(state.timelineScale).key === "day";
      return `<div class="timeline-daily-brief${active ? " active" : ""}">
        <div class="timeline-daily-copy"><strong>Daily Recon Layer</strong><span>${esc(daily.protocol || "Switch to Daily to inspect exact canon days and the activity that landed there.")}</span></div>
        <div class="timeline-daily-stat"><strong>${fmt(daily.active_days || 0)}</strong><span>active days</span></div>
        <div class="timeline-daily-stat"><strong>${esc(daily.latest_day || "n/a")}</strong><span>${fmt(daily.latest_day_events || 0)} latest-day events</span></div>
        <div class="timeline-daily-stat"><strong>${esc(daily.peak_day || "n/a")}</strong><span>${fmt(daily.peak_day_events || 0)} peak-day events</span></div>
        <div class="timeline-daily-stat"><strong>${fmt(daily.peak_day_words || 0)}</strong><span>peak-day words</span></div>
      </div>`;
    }
    function timelineEraRail() {
      const allSelected = state.timelineEra === "all";
      const allTotal = (DATA.timeline?.eras || []).reduce((sum, era) => sum + Number(era.total || 0), 0);
      const allCard = `<button type="button" class="timeline-era-card interactive${allSelected ? " selected" : ""}" data-timeline-era="all" aria-selected="${allSelected ? "true" : "false"}"><strong>Whole Canon</strong><span>${fmt(allTotal)} tracked character events</span><p>${esc(DATA.timeline?.summary?.canon_copy || "Complete historical rail.")}</p></button>`;
      const eraCards = (DATA.timeline?.eras || []).map((era) => {
        const selected = state.timelineEra === era.id ? " selected" : "";
        return `<button type="button" class="timeline-era-card interactive${selected}" data-timeline-era="${esc(era.id)}" aria-selected="${selected ? "true" : "false"}"><strong>${esc(era.label)}</strong><span>${esc(timelineDateLabel(era.start))} -> ${esc(era.end ? timelineDateLabel(era.end) : "present")} / ${fmt(era.total)} events</span><p>${esc(era.body)}</p></button>`;
      }).join("");
      return `<div class="timeline-era-rail">${allCard}${eraCards}</div>`;
    }
    function timelineLayerRail() {
      return `<div class="timeline-layer-rail">${timelineLayers().map((layer) => {
        const selected = state.timelineLayer === layer.key ? " selected" : "";
        return `<button type="button" class="timeline-layer-card interactive${selected}" data-timeline-layer="${esc(layer.key)}" aria-selected="${selected ? "true" : "false"}"><strong>${esc(layer.label)}</strong><span>${timelineLayerCode(layer.key)} / ${fmt(layer.count || 0)} events</span></button>`;
      }).join("")}</div>`;
    }
    function timelineBeatCard(beat) {
      const selected = beat.id === state.timelineBeatId ? " selected" : "";
      const meta = [timelineDateLabel(beat.date), prettyFamily(beat.event_type), beat.source_system].filter(Boolean).join(" / ");
      return `<button type="button" class="timeline-beat-card interactive${selected}" data-timeline-beat="${esc(beat.id)}" aria-selected="${selected ? "true" : "false"}">
        <span class="timeline-beat-icon ${esc(timelineLayerClass(beat.layer))}">${esc(timelineLayerCode(beat.layer))}</span>
        <span><strong>${esc(beat.title || "Timeline Beat")}</strong><span>${esc(meta)}</span></span>
        <em>${esc(timelineLayerMeta(beat.layer).label || beat.layer)}</em>
      </button>`;
    }
    function timelineBeatList() {
      const beats = timelineFilteredBeats();
      return `<div class="timeline-beat-list">${beats.map(timelineBeatCard).join("") || `<div class="empty">No canon beats match this era/layer filter.</div>`}</div>`;
    }
    function timelineChartLayerColor(layer) {
      return {
        knowledge: "#34d399",
        turns: "#22d3ee",
        skills: "#e879f9",
        nodes: "#fbbf24",
        capabilities: "#a78bfa"
      }[layer] || "#bac7da";
    }
    function timelineFilteredSeriesRows() {
      let rows = timelineSeriesRows();
      if (state.timelineLayer && state.timelineLayer !== "all") rows = rows.filter((row) => row.layer === state.timelineLayer);
      if (state.timelineEra && state.timelineEra !== "all") rows = rows.filter((row) => row.era_id === state.timelineEra);
      return rows;
    }
    function timelineBucketGroups() {
      const rows = timelineFilteredSeriesRows();
      const bucketMap = new Map();
      for (const row of rows) {
        if (!row.bucket) continue;
        const bucket = bucketMap.get(row.bucket) || { bucket: row.bucket, layers: [], values: {}, words: 0, total: 0 };
        const layer = row.layer || "knowledge";
        const events = Number(row.events || 0);
        if (!bucket.values[layer]) {
          bucket.values[layer] = 0;
          bucket.layers.push({ layer, events: 0 });
        }
        bucket.values[layer] += events;
        const layerEntry = bucket.layers.find((item) => item.layer === layer);
        if (layerEntry) layerEntry.events += events;
        bucket.words += Number(row.words || 0);
        bucket.total += events;
        bucketMap.set(row.bucket, bucket);
      }
      return [...bucketMap.values()].sort((a, b) => String(a.bucket).localeCompare(String(b.bucket))).slice(-timelineSeriesLimit());
    }
    function timelineChartLayers(buckets) {
      const preferred = ["knowledge", "turns", "skills", "nodes", "capabilities"];
      if (state.timelineLayer && state.timelineLayer !== "all") return [state.timelineLayer];
      const present = new Set();
      for (const bucket of buckets) {
        for (const layer of Object.keys(bucket.values || {})) {
          if (Number(bucket.values[layer] || 0) > 0) present.add(layer);
        }
      }
      return preferred.filter((layer) => present.has(layer));
    }
    function timelineStackedLineChart() {
      const buckets = timelineBucketGroups();
      if (!buckets.length) return `<div class="timeline-chart-wrap"><div class="empty">No linechart data matches this filter.</div></div>`;
      const layers = timelineChartLayers(buckets);
      if (!layers.length) return `<div class="timeline-chart-wrap"><div class="empty">No stacked layers are available for this filter.</div></div>`;
      const width = 920;
      const height = 300;
      const pad = { l: 58, r: 20, t: 20, b: 48 };
      const chartW = width - pad.l - pad.r;
      const chartH = height - pad.t - pad.b;
      const maxTotal = Math.max(1, ...buckets.map((bucket) => bucket.total));
      const xFor = (index) => pad.l + (buckets.length === 1 ? chartW / 2 : (index / Math.max(1, buckets.length - 1)) * chartW);
      const yFor = (value) => pad.t + (1 - (value / maxTotal)) * chartH;
      const pointPath = (points) => points.map((point, index) => `${index ? "L" : "M"}${point.x.toFixed(1)} ${point.y.toFixed(1)}`).join(" ");
      const grid = [0, 0.25, 0.5, 0.75, 1].map((ratio) => {
        const value = maxTotal * ratio;
        const y = yFor(value);
        return `<line class="timeline-chart-grid" x1="${pad.l}" y1="${y.toFixed(1)}" x2="${width - pad.r}" y2="${y.toFixed(1)}"></line><text class="timeline-chart-label" x="${pad.l - 8}" y="${(y + 3).toFixed(1)}" text-anchor="end">${esc(fmt(Math.round(value)))}</text>`;
      }).join("");
      const labelIndexes = [...new Set([0, Math.floor((buckets.length - 1) * 0.25), Math.floor((buckets.length - 1) * 0.5), Math.floor((buckets.length - 1) * 0.75), buckets.length - 1])].filter((index) => index >= 0);
      const xLabels = labelIndexes.map((index) => {
        const x = xFor(index);
        const label = buckets[index]?.bucket || "";
        return `<line class="timeline-chart-grid" x1="${x.toFixed(1)}" y1="${pad.t}" x2="${x.toFixed(1)}" y2="${height - pad.b}"></line><text class="timeline-chart-label" x="${x.toFixed(1)}" y="${height - 20}" text-anchor="middle">${esc(label)}</text>`;
      }).join("");
      let cumulative = buckets.map(() => 0);
      const bands = layers.map((layer, layerIndex) => {
        const color = timelineChartLayerColor(layer);
        const lower = buckets.map((bucket, index) => ({ x: xFor(index), y: yFor(cumulative[index]) }));
        const upper = buckets.map((bucket, index) => {
          cumulative[index] += Number(bucket.values[layer] || 0);
          return { x: xFor(index), y: yFor(cumulative[index]) };
        });
        const areaPath = `${pointPath(upper)} ${pointPath([...lower].reverse()).replace(/^M/, "L")} Z`;
        const linePath = pointPath(upper);
        const peak = Math.max(...buckets.map((bucket) => Number(bucket.values[layer] || 0)));
        const peakIndex = buckets.findIndex((bucket) => Number(bucket.values[layer] || 0) === peak);
        const dot = peak > 0 && peakIndex >= 0 ? `<circle class="timeline-chart-dot" cx="${xFor(peakIndex).toFixed(1)}" cy="${yFor(upper[peakIndex] ? cumulative[peakIndex] : peak).toFixed(1)}" r="3.4" fill="${color}" style="color:${color}"><title>${esc(`${timelineLayerMeta(layer).label}: ${fmt(peak)} events at ${buckets[peakIndex]?.bucket}`)}</title></circle>` : "";
        return `<path class="timeline-chart-area" d="${areaPath}" fill="${color}" style="animation-delay:${(layerIndex * 70).toFixed(0)}ms"><title>${esc(`${timelineLayerMeta(layer).label} stacked area`)}</title></path><path class="timeline-chart-line" d="${linePath}" stroke="${color}" pathLength="1" style="color:${color};animation-delay:${(120 + layerIndex * 80).toFixed(0)}ms"><title>${esc(`${timelineLayerMeta(layer).label} stacked boundary`)}</title></path>${dot}`;
      }).join("");
      const legend = layers.map((layer) => `<span style="color:${timelineChartLayerColor(layer)}"><i></i>${esc(timelineLayerMeta(layer).label)}</span>`).join("");
      const peakBuckets = [...buckets].sort((a, b) => b.total - a.total).slice(0, 3);
      const readout = peakBuckets.map((bucket) => `<div><strong>${esc(bucket.bucket)}</strong><span>${fmt(bucket.total)} events / ${fmt(bucket.words || 0)} words</span></div>`).join("");
      return `<div class="timeline-chart-wrap">
        <div class="timeline-chart-head"><strong>X-axis stacked linechart</strong><span>${fmt(buckets.length)} buckets / max ${fmt(maxTotal)} events</span></div>
        <div class="timeline-linechart"><svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(`${timelineScaleMeta(state.timelineScale).label} stacked timeline linechart`)}">
          <rect x="0" y="0" width="${width}" height="${height}" rx="10" fill="rgba(2,6,23,0.2)"></rect>
          ${grid}${xLabels}
          <line class="timeline-chart-axis" x1="${pad.l}" y1="${height - pad.b}" x2="${width - pad.r}" y2="${height - pad.b}"></line>
          <line class="timeline-chart-axis" x1="${pad.l}" y1="${pad.t}" x2="${pad.l}" y2="${height - pad.b}"></line>
          ${bands}
        </svg></div>
        <div class="timeline-chart-legend">${legend}</div>
        <div class="timeline-chart-readout">${readout}</div>
      </div>`;
    }
    function timelineSeries() {
      const buckets = timelineBucketGroups();
      const maxTotal = Math.max(1, ...buckets.map((bucket) => bucket.total));
      return `<div class="timeline-series-list">${buckets.map((bucket) => {
        const bars = bucket.layers.map((layer) => {
          const width = Math.max(4, (Number(layer.events || 0) / maxTotal) * 100);
          return `<i class="${esc(timelineLayerClass(layer.layer))}" style="--w:${width.toFixed(2)}%" title="${esc(`${timelineLayerMeta(layer.layer).label}: ${fmt(layer.events)} events`)}"></i>`;
        }).join("");
        return `<div class="timeline-series-row"><span>${esc(bucket.bucket)}</span><div class="timeline-track">${bars}</div><strong>${fmt(bucket.total)} ev</strong></div>`;
      }).join("") || `<div class="empty">No timeline series matches this filter.</div>`}</div>`;
    }
    function timelineInspector(beat) {
      const metrics = beat.metrics || {};
      const linkedSkill = beat.target_type === "skill" ? DATA.skills.find((skill) => skill.skill_id === beat.target_id) : null;
      const linkedNode = DATA.nodes.find((node) => node.node_id === beat.target_id || node.label === beat.title);
      const linkedCapability = DATA.capabilities.find((capability) => capability.node_skill_id === beat.target_id || capability.label === beat.title);
      const examples = [linkedSkill, linkedNode, linkedCapability].filter(Boolean).map((item) => ({
        title: item.label || item.title,
        meta: item.skill_family || item.node_type || item.mode || "linked record",
        body: item.summary || item.description || "Linked Character Sheet record."
      }));
      return `<aside class="game-card timeline-inspector"><h4>Canon Inspector</h4>
        <div class="record-title"><strong>${esc(beat.title || "Timeline Beat")}</strong><span class="rank s">${esc(timelineLayerCode(beat.layer))}</span></div>
        <p>${esc(beat.body || "Selected historical beat from the Character Sheet canon timeline.")}</p>
        <div class="game-list" style="margin-top:12px">
          ${codexFactRow("Date", timelineDateLabel(beat.date))}
          ${codexFactRow("Era", timelineEraById(beat.era_id)?.label || "Whole Canon")}
          ${codexFactRow("Layer", timelineLayerMeta(beat.layer).label || beat.layer)}
          ${codexFactRow("Event Type", prettyFamily(beat.event_type))}
          ${codexFactRow("Source", beat.source_system || "Second Brain")}
          ${codexFactRow("Confidence", beat.confidence ? String(beat.confidence) : "projection")}
          ${codexFactRow("Target", beat.target_id || "n/a")}
        </div>
        <div class="section-kicker">Activity Metrics</div>
        ${lowerTiles([
          { label: "Events", value: fmt(metrics.event_count || 1) },
          { label: "Content XP", value: fmt(metrics.content_words || 0) },
          { label: "Code Lines", value: fmt(metrics.code_lines || 0) },
          { label: "Caps", value: fmt(metrics.capability_count || 0) }
        ])}
        <div class="section-kicker">Linked Sheet Records</div>
        ${exampleList(examples.length ? examples : [{ title: "Second Brain Timeline", meta: beat.target_type || "event", body: "Open the source timeline route or raw data view to inspect this target in full." }])}
      </aside>`;
    }
    function timelineSourcePanels() {
      const rows = (DATA.timeline?.source_mix || []).slice(0, 24);
      const grouped = new Map();
      for (const row of rows) {
        const key = row.source_system || "unknown";
        const entry = grouped.get(key) || { source_system: key, count: 0, events: [] };
        entry.count += Number(row.count || 0);
        entry.events.push(row);
        grouped.set(key, entry);
      }
      return `<div class="timeline-source-grid">${[...grouped.values()].slice(0, 4).map((source) => `<aside class="game-card proof-mini-panel"><h4>${esc(source.source_system)}</h4><div class="game-list">${source.events.slice(0, 6).map((item) => gameListRow(prettyFamily(item.event_type), fmt(item.count))).join("")}</div></aside>`).join("")}</div>`;
    }
    function detailCard(title, kind, body, lower, examples) {
      return `<div class="game-card passport-detail">
        <div class="detail-kicker">${esc(kind)}</div>
        <h4>${esc(title)}${badge("Inspect", "gold")}</h4>
        <p>${esc(body)}</p>
        <div class="section-kicker" style="margin-top:14px">Next aggregation lower</div>
        ${lowerTiles(lower)}
        <div class="section-kicker" style="margin-top:14px">Examples</div>
        ${exampleList(examples)}
      </div>`;
    }
    function statIconClass(label) {
      return `stat-${String(label || "").toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;
    }
    function skillHighlightRow(skill) {
      return `<div class="skill-highlight-row interactive">
        ${familyThumb(skill.skill_family, "small animated")}
        <span><strong>${esc(skill.label)}</strong><span>${esc(prettyFamily(skill.skill_family))} / ${fmt(skill.evidence_count)} XP</span></span>
        <em>${esc(skill.rank)} ${fmt(skill.level)}</em>
      </div>`;
    }
    function gameStats() {
      return `<div class="game-stats">${DATA.stats.map((stat) => `<article class="game-stat">
        <div class="game-stat-head">
          <span class="stat-icon ${esc(statIconClass(stat.label))}" aria-hidden="true"><i></i></span>
          <div><div class="game-stat-top"><span>${esc(stat.label)}</span><span>${fmt(stat.value)}</span></div><div class="bar"><div class="fill" style="--value:${pct(stat.value)}"></div></div></div>
        </div>
        <div class="record-meta">${esc(stat.detail)}</div>
      </article>`).join("")}</div>`;
    }
    function miniSecondBrainConsole() {
      const sources = DATA.source_systems.slice(0, 5);
      const sourceMax = Math.max(1, ...sources.map((source) => Number(source.items || 0)));
      const sourceRows = sources.map((source) => `<div class="sb-source-row" style="--value:${pct((Number(source.items || 0) / sourceMax) * 100)}">
        <span><strong>${esc(source.source_system || "unknown")}</strong><em>${esc(source.mediums || "source")} / ${fmt(source.exposures)} exposures</em></span>
        <b>${fmt(source.items)}</b>
        <i aria-hidden="true"></i>
      </div>`).join("");
      const radarNodes = [
        ["Sources", DATA.summary.items, 50, 10],
        ["Topics", DATA.summary.topics, 84, 34],
        ["Turns", DATA.summary.turns, 76, 78],
        ["Skills", DATA.skills.length, 24, 78],
        ["Nodes", DATA.nodes.length, 16, 34],
        ["Media", DATA.summary.media_jobs, 50, 91]
      ].map(([label, value, x, y], index) => `<span class="sb-node" style="--x:${x}%;--y:${y}%;animation-delay:${index * 120}ms"><strong>${esc(label)}</strong><em>${fmt(value)}</em></span>`).join("");
      const topicCloud = DATA.topics.slice(0, 8).map((topic) => `<span class="sb-topic-chip">
        <strong>${esc(topic.label)}</strong>
        <em>${fmt(topic.evidence_count)} XP / ${fmt(topic.skill_count)} skills</em>
      </span>`).join("");
      const layerRows = (DATA.timeline?.layers || []).slice(0, 5).map((layer) => `<div class="sb-layer-row">
        <span><i class="timeline-layer-${esc(layer.key)}" aria-hidden="true"></i>${esc(layer.label)}</span>
        <strong>${fmt(layer.count)}</strong>
      </div>`).join("");
      const footer = [
        [DATA.summary.chunks, "Chunks"],
        [DATA.summary.entities, "Entities"],
        [DATA.summary.edges, "Edges"],
        [DATA.timeline?.summary?.timeline_events || 0, "Timeline Events"]
      ].map(([value, label]) => `<div><strong>${fmt(value)}</strong><span>${esc(label)}</span></div>`).join("");
      return `<section class="second-brain-mini" aria-label="Hapa Second Brain mini console">
        <div class="sb-head">
          <div><div class="section-kicker">Hapa Second Brain</div><h4>Memory Console</h4></div>
          <div class="sb-status"><span>SQLite Core</span><span>Local First</span><span>Canon Feed</span></div>
        </div>
        <div class="sb-grid">
          <div class="sb-pane">
            <div class="sb-pane-title"><span>Source Matrix</span><span>${fmt(DATA.mediums.length)} mediums</span></div>
            <div class="sb-source-list">${sourceRows}</div>
          </div>
          <div class="sb-radar" aria-hidden="true">
            <div class="sb-radar-core">Second<br>Brain</div>
            ${radarNodes}
          </div>
          <div class="sb-pane">
            <div class="sb-pane-title"><span>Topic Bloom</span><span>${fmt(DATA.topics.length)} profiles</span></div>
            <div class="sb-topic-cloud">${topicCloud}</div>
            <div class="sb-pane-title" style="margin-top:4px"><span>Canon Layers</span><span>${fmt(DATA.timeline?.summary?.activity_metrics || 0)} metrics</span></div>
            <div class="sb-layer-list">${layerRows}</div>
          </div>
        </div>
        <div class="sb-footer">${footer}</div>
      </section>`;
    }
    function skillQualityData() {
      return DATA.skill_quality || { summary: {}, skill_quality: [], avatar_skill_experience: [], top_pairs: [], family_summary: [], method: {} };
    }
    function skillQualityRow(row, selected = false) {
      const active = selected || row.skill_id === state.codexSkillId ? " selected" : "";
      return `<button type="button" class="quality-row interactive${active}" data-codex-skill-id="${esc(row.skill_id || "")}" aria-selected="${active ? "true" : "false"}">
        <span class="quality-rank-token">${esc(row.quality_band || "S")}</span>
        <span><strong>${esc(row.label || "Skill")}</strong><span>${esc(prettyFamily(row.skill_family))} / #${fmt(row.quality_rank || 0)} / ${fmt(row.capability_count || 0)} caps / ${fmt(row.node_count || 0)} nodes</span></span>
        <em class="quality-score-pill">Q ${fmt(Math.round(row.quality_score || 0))}</em>
        <span class="quality-meter" aria-hidden="true"><i style="--value:${pct(row.quality_score || 0)}"></i></span>
      </button>`;
    }
    function avatarSkillPairRow(pair) {
      return `<button type="button" class="quality-pair-row interactive" data-codex-skill-id="${esc(pair.skill_id || "")}">
        <span class="quality-rank-token">${esc(initials(pair.avatar_label || "AV"))}</span>
        <span><strong>${esc(pair.avatar_label || "Avatar")} -> ${esc(pair.skill_label || "Skill")}</strong><span>${esc(prettyFamily(pair.skill_family))} / observed ${fmt(pair.observed_uses || 0)} / avatar rel ${fmt(Math.round(pair.avatar_relative_score || 0))}</span></span>
        <em class="quality-score-pill">EXP ${fmt(Math.round(pair.experience_score || 0))}</em>
        <span class="quality-meter" aria-hidden="true"><i style="--value:${pct(pair.experience_score || 0)}"></i></span>
      </button>`;
    }
    function skillQualityPreview() {
      const quality = skillQualityData();
      const topQuality = quality.skill_quality?.[0] || {};
      const topPair = quality.top_pairs?.[0] || {};
      return `<section class="quality-preview" aria-label="Skill quality and avatar experience preview">
        <div class="sb-head">
          <div><div class="section-kicker">Skill Quality / Avatar EXP</div><h4>Rank Engine</h4></div>
          <div class="sb-status"><span>${fmt(quality.summary?.skills_ranked || 0)} Skills</span><span>${fmt(quality.summary?.avatars_ranked || 0)} Avatars</span><span>${fmt(quality.summary?.avatar_skill_pairs || 0)} Pairs</span></div>
        </div>
        <div class="quality-preview-grid">
          <div class="quality-preview-tile"><strong>${esc(topQuality.quality_band || "S")}</strong><span>Top quality: ${esc(topQuality.label || "No ranked skill")}</span></div>
          <div class="quality-preview-tile"><strong>${fmt(Math.round(topQuality.quality_score || 0))}</strong><span>Skill quality score</span></div>
          <div class="quality-preview-tile"><strong>${fmt(Math.round(topPair.experience_score || 0))}</strong><span>${esc(topPair.avatar_label || "Avatar")} exp with ${esc(topPair.skill_label || "skill")}</span></div>
        </div>
      </section>`;
    }
    function characterRankConsole() {
      const quality = skillQualityData();
      const topQuality = quality.skill_quality?.[0] || {};
      const topPair = quality.top_pairs?.[0] || {};
      const rows = (quality.skill_quality || []).slice(0, 2).map((row) => `<button type="button" class="character-rank-row interactive" data-codex-skill-id="${esc(row.skill_id || "")}">
        <span><strong>${esc(row.label || "Skill")}</strong><span>${esc(prettyFamily(row.skill_family))} / #${fmt(row.quality_rank || 0)} quality</span></span>
        <em>${esc(row.quality_band || "S")} ${fmt(Math.round(row.quality_score || 0))}</em>
      </button>`).join("");
      return `<div class="character-rank-console" aria-label="Character rank engine">
        <div class="character-rank-head">
          <span><strong>Rank Engine</strong><span>${fmt(quality.summary?.skills_ranked || 0)} skills / ${fmt(quality.summary?.avatars_ranked || 0)} avatars / ${fmt(quality.summary?.avatar_skill_pairs || 0)} pairs</span></span>
          <b class="character-rank-seal">${esc(topQuality.quality_band || "S")}</b>
        </div>
        <div class="character-rank-grid">
          <div class="character-rank-stat">
            <strong>${fmt(Math.round(topQuality.quality_score || 0))}</strong>
            <span>Top Skill Quality / ${esc(topQuality.label || "No ranked skill")}</span>
            <div class="character-rank-meter" aria-hidden="true"><i style="--value:${pct(topQuality.quality_score || 0)}"></i></div>
          </div>
          <div class="character-rank-stat">
            <strong>${fmt(Math.round(topPair.experience_score || 0))}</strong>
            <span>${esc(topPair.avatar_label || "Avatar")} EXP / ${esc(topPair.skill_label || "Skill")}</span>
            <div class="character-rank-meter" aria-hidden="true"><i style="--value:${pct(topPair.experience_score || 0)}"></i></div>
          </div>
        </div>
        ${rows}
      </div>`;
    }
    function renderSkillQualityPanel(selectedFamily = state.codexFamily) {
      const quality = skillQualityData();
      const rows = quality.skill_quality || [];
      const pairs = quality.avatar_skill_experience || [];
      const familyRows = rows.filter((row) => row.skill_family === selectedFamily);
      const ladder = (familyRows.length ? familyRows.slice(0, 8) : rows.slice(0, 8)).map((row) => skillQualityRow(row)).join("");
      const visiblePairs = pairs.filter((pair) => !selectedFamily || pair.skill_family === selectedFamily).slice(0, 20);
      const pairRows = (visiblePairs.length ? visiblePairs : pairs.slice(0, 20)).slice(0, 8).map(avatarSkillPairRow).join("");
      const scatterPairs = (visiblePairs.length ? visiblePairs : pairs.slice(0, 24)).slice(0, 24);
      const dots = scatterPairs.map((pair, index) => {
        const x = Math.max(8, Math.min(92, Number(pair.quality_score || 0)));
        const y = Math.max(8, Math.min(88, 100 - Number(pair.experience_score || 0)));
        const size = Math.max(24, Math.min(52, 22 + Number(pair.observed_uses || 0) * 0.55));
        const selected = pair.skill_id === state.codexSkillId ? " selected" : "";
        return `<button type="button" class="quality-dot interactive${selected}" style="--x:${x}%;--y:${y}%;--s:${size}px;animation-delay:${index * 70}ms" data-codex-skill-id="${esc(pair.skill_id || "")}" title="${esc(`${pair.avatar_label} / ${pair.skill_label} / EXP ${Math.round(pair.experience_score || 0)}`)}">${esc(initials(pair.avatar_label || "AV"))}</button>`;
      }).join("");
      const family = (quality.family_summary || []).find((item) => item.skill_family === selectedFamily) || {};
      return `<section class="game-card quality-panel">
        <div class="quality-head">
          <div>
            <h4>Skill Quality / Avatar Experience Matrix</h4>
            <p>${esc("Skill Quality ranks how powerful/useful a skill is relative to other skills. Avatar Experience ranks how much each avatar appears to have used or embodied that skill relative to its own dossier and the rest of the avatar roster.")}</p>
          </div>
          <div class="tag-row">${badge(`Formula ${quality.formula_version || "projection"}`, "cyan")}${badge(`Reassessed ${quality.summary?.last_reassessed_at || DATA.generated_at}`, "green")}</div>
        </div>
        <div class="quality-grid">
          <aside>
            <div class="inventory-head"><h4>${esc(prettyFamily(selectedFamily || "Top Skills"))}</h4>${badge(`${fmt(family.skill_count || familyRows.length || rows.length)} skills`, "cyan")}</div>
            <div class="quality-ladder">${ladder || `<div class="empty">No quality rows available.</div>`}</div>
          </aside>
          <section>
            <div class="inventory-head"><h4>Avatar x Skill Plot</h4>${badge(`Q x EXP / ${fmt(scatterPairs.length)} pairs`, "gold")}</div>
            <div class="quality-scatter">
              <div class="quality-crosshair"></div>
              <div class="quality-axis y">Avatar Experience</div>
              <div class="quality-axis x"><span>Lower Quality</span><span>Higher Quality</span></div>
              ${dots || `<div class="empty" style="margin:90px 18px">No avatar-skill matches for this family yet.</div>`}
            </div>
          </section>
          <aside>
            <div class="inventory-head"><h4>Top Avatar EXP</h4>${badge(`${fmt(quality.summary?.avatar_skill_pairs || 0)} pairs`, "pink")}</div>
            <div class="quality-pair-list">${pairRows || `<div class="empty">No avatar experience rows available.</div>`}</div>
            <div class="section-kicker" style="margin-top:12px">Method</div>
            <p class="record-meta">${esc(quality.method?.avatar_experience || "Avatar experience is a projection over avatar evidence.")}</p>
          </aside>
        </div>
      </section>`;
    }
    function renderPresentationHero() {
      const topSkills = DATA.skills.slice(0, 8).map((skill) => skillHighlightRow(skill)).join("");
      const proof = [
        [DATA.summary.items, "Source Items"],
        [DATA.summary.skill_evidence, "Evidence XP"],
        [DATA.summary.turns, "Turns"],
        [DATA.summary.media_jobs, "Media Jobs"],
        [DATA.summary.capability_bridges, "Bridges"]
      ].map(([value, label]) => `<div class="proof-chip-big"><strong>${fmt(value)}</strong><span>${esc(label)}</span></div>`).join("");
      const chain = [
        ["Read", DATA.summary.items, "source items"],
        ["Learn", DATA.skills.length, "skills"],
        ["Practice", DATA.summary.turns, "AI turns"],
        ["Build", DATA.nodes.length, "Hapa nodes"],
        ["Prove", DATA.summary.skill_evidence, "evidence XP"],
        ["Publish", DATA.summary.media_jobs, "media jobs"]
      ].map(([label, value, unit]) => `<div class="proof-step"><strong>${esc(label)}</strong><span>${fmt(value)}</span><em>${esc(unit)}</em></div>`).join("");
      return `<div class="game-frame"><div class="game-panel game-hero-grid">
        <aside class="portrait-card model-card">
          ${characterModelStage()}
          <div class="class-plate"><strong>Knowledge Architect</strong><span>Looping Character Model</span></div>
          <div class="identity-strip">
            <div><span class="record-meta">Status</span><br>${badge("Operational", "green")}</div>
            <div><span class="record-meta">Mode</span><br>${badge("Signal / Proof", "gold")}</div>
          </div>
          ${characterRankConsole()}
        </aside>
        <section>
          <div class="game-title">
            <div>
              <div class="section-kicker">Professional RPG Dossier</div>
              <h3>${esc(DATA.profile.name)}</h3>
              <p>${esc(DATA.profile.resume_summary)}</p>
              <div class="tag-row">${chips(DATA.profile.roles, "cyan")}</div>
            </div>
            <div class="rank-medal">S</div>
          </div>
          ${gameStats()}
          <div class="game-proof-strip">${proof}</div>
          <div class="proof-chain">${chain}</div>
          ${miniSecondBrainConsole()}
          ${skillQualityPreview()}
        </section>
        <aside class="game-side-stack">
          ${characterModelCard()}
          <div class="game-card"><h4>Skill Highlights</h4><div class="game-list">${topSkills}</div></div>
          ${imageManager()}
          <div class="game-card"><h4>Visual Layers</h4>${mockGallery()}</div>
        </aside>
      </div></div>`;
    }
    function renderPresentationCodex() {
      const families = DATA.skill_families.slice(0, 8);
      if (!DATA.skill_families.some((family) => family.label === state.codexFamily)) state.codexFamily = DATA.skill_families[0]?.label || "";
      const selectedFamily = state.codexFamily;
      const familyRecord = DATA.skill_families.find((family) => family.label === selectedFamily) || DATA.skill_families[0] || {};
      const familySkills = skillsForFamily(selectedFamily);
      const familyCaps = capabilitiesForFamily(selectedFamily);
      const familyNodes = nodesForFamily(selectedFamily);
      const selected = selectedCodexCapability(selectedFamily);
      const selectedSkill = selectedCodexSkill(selectedFamily);
      state.codexCapabilityId = selected.node_skill_id || "";
      const branches = families.map((family) => {
        const active = family.label === selectedFamily ? " selected" : "";
        return `<button type="button" class="tree-branch interactive${active}" data-codex-family="${esc(family.label)}" aria-selected="${active ? "true" : "false"}">
          ${familyThumb(family.label)}
          <span><strong>${esc(prettyFamily(family.label))}</strong><span>${fmt(family.evidence_count)} XP / ${fmt(family.skill_count)} skills</span></span>
        </button>`;
      }).join("");
      const classRows = DATA.profile.roles.slice(0, 4).map((role, index) => gameListRow(role, `Rank ${91 - index * 4}`)).join("");
      const capabilityRows = familyCaps.slice(0, 10).map((capability) => {
        const active = capability.node_skill_id === selected.node_skill_id ? " selected" : "";
        const marker = capability.mode === "enhancing" ? "Enhance" : "Use";
        return `<div class="game-list-row interactive${active}" role="button" tabindex="0" data-codex-capability="${esc(capability.node_skill_id)}" aria-selected="${active ? "true" : "false"}">
          <span>${esc(capability.label)}</span><strong>${esc(marker)}</strong>
        </div>`;
      }).join("");
      const familySkillRows = familySkills.slice(0, 9).map((skill) => `<div class="game-list-row compact interactive${state.codexSkillId === skill.skill_id ? " selected" : ""}" role="button" tabindex="0" data-codex-family="${esc(skill.skill_family)}" data-codex-skill-id="${esc(skill.skill_id)}" aria-selected="${state.codexSkillId === skill.skill_id ? "true" : "false"}">
        ${familyThumb(skill.skill_family, "small")}
        <span><strong>${esc(skill.label)}</strong><span>${fmt(skill.evidence_count)} XP / ${fmt(skill.source_count)} sources</span></span>
        <strong>${esc(skill.rank)}</strong>
      </div>`).join("");
      const linkedNodeRows = familyNodes.slice(0, 8).map((node) => `<div class="game-list-row compact interactive${selected.node_id === node.node_id ? " selected" : ""}" role="button" tabindex="0" data-codex-node-id="${esc(node.node_id)}" aria-selected="${selected.node_id === node.node_id ? "true" : "false"}">
        ${nodeThumb(node, "small")}
        <span><strong>${esc(node.label)}</strong><span>${esc(node.node_type || "node")} / ${fmt(node.card_count)} proof cards</span></span>
        <strong>${fmt(node.topic_count)}</strong>
      </div>`).join("");
      const connectedSkills = uniqueBy([...(selected.connected_skills || []), ...familySkills.map((skill) => skill.label)], (item) => String(item).toLowerCase()).slice(0, 12);
      return `<div class="game-frame"><div class="game-panel codex-shell">
        <div class="codex-grid">
        <aside class="game-card"><h4>Class And Specializations</h4><div class="game-list">${classRows}</div><div class="codex-meta-strip">${[
          [DATA.skills.length, "Skills"], [DATA.capabilities.length, "Capabilities"], [DATA.nodes.length, "Nodes"], [DATA.summary.skill_evidence, "Evidence XP"]
        ].map(([v,l]) => `<div class="proof-chip-big"><strong>${fmt(v)}</strong><span>${esc(l)}</span></div>`).join("")}</div></aside>
        <section class="skill-tree game-card">
          ${skillLoopStage(selectedFamily, selected, selectedSkill)}
          ${branches}
        </section>
        <aside class="game-card codex-inspector"><h4>Selected Capability</h4>
          <div class="record-title"><strong>${esc(selected.label || "Capability")}</strong><span class="rank ${rankClass(familyRecord.rank || "S")}">${esc(familyRecord.rank || "S")}</span></div>
          <p>${esc(selected.description || "Evidence-backed node capability.")}</p>
          <div class="game-list" style="margin-top:12px">
            ${codexFactRow("Mode", selected.mode || "using")}
            ${codexFactRow("Skill Family", prettyFamily(selectedFamily))}
            ${codexFactRow("Selected Skill", selectedSkill.label || "Skill")}
            ${codexFactRow("Linked Node", selected.node_label || "Hapa Node")}
            ${codexFactRow("Bridge Count", fmt(selected.link_count || 0))}
            ${codexFactRow("Proof Cards", fmt(selected.card_count || 0))}
          </div>
          <div class="section-kicker">Success Signals</div>
          <div class="codex-tags">${codexTags(selected.success_signals || [], "green", 8)}</div>
          <div class="section-kicker">Connected Skills</div>
          <div class="codex-tags">${codexTags(connectedSkills, "pink", 12)}</div>
        </aside>
        </div>
        <div class="codex-inventory-grid">
          <aside class="game-card inventory-panel">
            <div class="inventory-head"><h4>Family Loadout</h4>${badge(`${fmt(familyRecord.skill_count || familySkills.length)} skills`, "cyan")}</div>
            <div class="game-list codex-mini-list">${familySkillRows || `<div class="empty">No skills indexed for this family.</div>`}</div>
            <div class="section-kicker" style="margin-top:12px">Capability Unlocks</div>
            <div class="game-list codex-mini-list">${capabilityRows || `<div class="empty">No linked node capabilities found for this family yet.</div>`}</div>
          </aside>
          <aside class="game-card inventory-panel">
            <div class="inventory-head"><h4>Linked Hapa Nodes</h4>${badge(`${fmt(familyNodes.length)} examples`, "gold")}</div>
            <div class="game-list codex-mini-list">${linkedNodeRows || `<div class="empty">No linked nodes indexed for this family yet.</div>`}</div>
          </aside>
        </div>
        ${renderSkillQualityPanel(selectedFamily)}
        <div class="codex-inventory-grid">
          <aside class="game-card inventory-panel">
            <div class="inventory-head"><h4>All Skills</h4>${badge(`${fmt(DATA.skills.length)} indexed`, "cyan")}</div>
            <div class="inventory-scroll">${codexSkillInventory(selectedFamily)}</div>
          </aside>
          <aside class="game-card inventory-panel">
            <div class="inventory-head"><h4>All Hapa Nodes</h4>${badge(`${fmt(DATA.nodes.length)} indexed`, "gold")}</div>
            <div class="inventory-scroll">${codexNodeInventory(selected)}</div>
          </aside>
        </div>
      </div></div>`;
    }
    function renderPresentationProof() {
      const layers = proofLayers();
      if (!layers.some((layer) => layer.key === state.proofFocus)) state.proofFocus = "skills";
      const selected = proofLayerByKey(state.proofFocus);
      const graphNodes = layers.map((layer) => `<button type="button" class="graph-node ${esc(layer.cls)} interactive${state.proofFocus === layer.key ? " selected" : ""}" style="--x:${layer.x}%;--y:${layer.y}%;" data-proof-focus="${esc(layer.key)}" aria-selected="${state.proofFocus === layer.key ? "true" : "false"}">${esc(layer.label)}<strong>${fmt(layer.value)}</strong></button>`).join("");
      return `<div class="game-frame"><div class="game-panel proof-shell">
        <div class="proof-map-grid">
          <aside class="game-card"><h4>Proof Layers</h4><p>${esc("Click any layer to inspect how the Character Sheet moves from source intake to practice, skills, nodes, capability bridges, media, agents, and reusable protocols.")}</p><div class="proof-layer-list" style="margin-top:12px">${layers.map(proofLayerRow).join("")}</div></aside>
          <section class="constellation">
            ${proofEdges(layers)}
            <span class="proof-spark"></span><span class="proof-spark"></span><span class="proof-spark"></span><span class="proof-spark"></span>
            <div class="graph-core">Proof<br>Map</div>
            ${graphNodes}
          </section>
          <aside class="game-card proof-inspector"><h4>Layer Inspector</h4>
            <div class="record-title"><strong>${esc(selected.label)}</strong><span class="rank s">${esc(selected.code)}</span></div>
            <p>${esc(selected.body)}</p>
            ${proofFactRows(selected)}
            <div class="section-kicker">Next Aggregation Lower</div>
            ${lowerTiles(selected.lower || [])}
            <div class="section-kicker">Examples</div>
            ${exampleList(selected.examples || [])}
          </aside>
        </div>
        ${proofFlowSteps()}
        <div class="proof-comprehensive-grid">
          ${proofMiniPanel("Source Systems", DATA.source_systems.slice(0, 8).map((item) => ({ label: item.source_system || "unknown", value: fmt(item.items) })))}
          ${proofMiniPanel("Skill Families", DATA.skill_families.slice(0, 8).map((item) => ({ label: prettyFamily(item.label), value: `${fmt(item.skill_count)} skills` })))}
          ${proofMiniPanel("Node Types", DATA.node_type_summary.slice(0, 8).map((item) => ({ label: prettyFamily(item.label), value: fmt(item.count) })))}
          ${proofMiniPanel("Operations", [
            { label: "Capabilities", value: fmt(DATA.capabilities.length) },
            { label: "Media Jobs", value: fmt(DATA.media.length) },
            { label: "Agents + Harnesses", value: fmt(DATA.agents.length + DATA.harnesses.length) },
            { label: "Protocols + Docs", value: fmt(DATA.protocols.length + DATA.docs.length + DATA.contracts.length) },
            { label: "Board Tasks", value: fmt(DATA.board.tasks.length) }
          ])}
        </div>
      </div></div>`;
    }
    function nodeScorePct(node) {
      return `${Math.max(4, Math.min(100, (Number(node?.score || 0) / NODE_SCORE_MAX) * 100))}%`;
    }
    function nodeScoreRank(score) {
      const value = Number(score || 0);
      if (value >= 1000) return "SS";
      if (value >= 700) return "S";
      if (value >= 400) return "A";
      if (value >= 160) return "B";
      if (value >= 50) return "C";
      return "D";
    }
    function loadoutNodes() {
      const type = state.loadoutType || "all";
      const nodes = type === "all" ? DATA.nodes : DATA.nodes.filter((node) => node.node_type === type);
      return nodes.slice().sort((a, b) => Number(b.score || 0) - Number(a.score || 0) || String(a.label || "").localeCompare(String(b.label || "")));
    }
    function selectedLoadoutNode() {
      const visible = loadoutNodes();
      let selected = DATA.nodes.find((node) => node.node_id === state.loadoutNodeId);
      if (!selected || (state.loadoutType !== "all" && selected.node_type !== state.loadoutType)) selected = visible[0] || DATA.nodes[0] || {};
      state.loadoutNodeId = selected.node_id || "";
      return selected;
    }
    function setLoadoutHash() {
      window.location.hash = `presentation-loadout&node=${encodeURIComponent(state.loadoutNodeId || "")}&loadoutType=${encodeURIComponent(state.loadoutType || "all")}`;
    }
    function selectLoadoutNode(nodeId) {
      const selected = DATA.nodes.find((node) => node.node_id === nodeId) || DATA.nodes[0] || {};
      state.loadoutNodeId = selected.node_id || "";
      state.gamePanel = "loadout";
      state.view = "presentation";
      setLoadoutHash();
      render();
    }
    function selectLoadoutType(type) {
      state.loadoutType = type || "all";
      const visible = loadoutNodes();
      if (!visible.some((node) => node.node_id === state.loadoutNodeId)) state.loadoutNodeId = visible[0]?.node_id || "";
      state.gamePanel = "loadout";
      state.view = "presentation";
      setLoadoutHash();
      render();
    }
    function loadoutCapabilitiesForNode(node) {
      const label = String(node?.label || "").toLowerCase();
      return uniqueBy(DATA.capabilities.filter((capability) => {
        const capNodeId = String(capability.node_id || "");
        const capNodeLabel = String(capability.node_label || "").toLowerCase();
        return capNodeId === node?.node_id || capNodeLabel === label;
      }), (capability) => capability.node_skill_id).slice(0, 8);
    }
    function loadoutMediaForNode(node) {
      const label = String(node?.label || "").toLowerCase();
      if (!label) return [];
      return DATA.media.filter((media) => {
        const fields = [media.node_label, media.target_label, media.visual_label, media.prompt_text, media.direction_prompt].map((value) => String(value || "").toLowerCase()).filter(Boolean);
        return fields.some((value) => value === label || value.includes(label) || label.includes(value));
      }).slice(0, 8);
    }
    function loadoutTypeFilters() {
      const filters = [{ label: "all known", key: "all", count: DATA.nodes.length }, ...DATA.node_type_summary.map((item) => ({ label: item.label, key: item.label, count: item.count }))];
      return `<div class="loadout-type-filters">${filters.map((item) => `<button type="button" class="loadout-type-filter interactive${state.loadoutType === item.key ? " selected" : ""}" data-loadout-type="${esc(item.key)}" aria-selected="${state.loadoutType === item.key ? "true" : "false"}">${esc(prettyFamily(item.label))} ${fmt(item.count)}</button>`).join("")}</div>`;
    }
    function loadoutNodeCard(node) {
      const selected = node.node_id === state.loadoutNodeId ? " selected" : "";
      return `<button type="button" class="slot-card node-slot interactive${selected}" style="${nodeThemeStyle(node)}" data-loadout-node-id="${esc(node.node_id)}" aria-selected="${selected ? "true" : "false"}" aria-label="Inspect ${esc(node.label)}">
        <div class="node-slot-top">
          ${nodeThumb(node, "large animated")}
          <span class="rank ${rankClass(nodeScoreRank(node.score))}">${esc(nodeScoreRank(node.score))}</span>
        </div>
        <div class="node-slot-body">
          <strong>${esc(node.label)}</strong>
          <div class="record-meta">${esc(nodeTypeLabel(node.node_type))} / ${fmt(node.score)} score</div>
          <div class="node-slot-meter"><span style="--value:${nodeScorePct(node)}"></span></div>
        </div>
        <div class="node-slot-meta">
          <span><strong>${fmt(node.topic_count)}</strong> topics</span>
          <span><strong>${fmt(node.card_count)}</strong> cards</span>
        </div>
      </button>`;
    }
    function loadoutInspector(node) {
      const caps = loadoutCapabilitiesForNode(node);
      const media = loadoutMediaForNode(node);
      const capRows = caps.map((capability) => gameListRow(capability.label, `${capability.mode || "use"} / ${fmt(capability.link_count)} links`)).join("");
      const mediaRows = media.map((item) => gameListRow(item.target_label || item.visual_label || item.job_id, `${item.status || "media"} / ${item.media_type || "artifact"}`)).join("");
      return `<div class="game-card loadout-inspector"><h4>Selected Node</h4>
        <div class="node-inspector-hero">
          ${nodeThumb(node, "large animated")}
          <div><strong>${esc(node.label || "Hapa Node")}</strong><span>${esc(nodeTypeLabel(node.node_type))} / ${fmt(node.score)} score / ${fmt(node.card_count)} cards</span></div>
        </div>
        <p>${esc(node.description || "Indexed Hapa node with generated character-sheet thumbnail and linked proof metadata.")}</p>
        <div class="game-list" style="margin-top:12px">
          ${codexFactRow("Node Type", nodeTypeLabel(node.node_type))}
          ${codexFactRow("Topics", fmt(node.topic_count))}
          ${codexFactRow("Bodies", fmt(node.body_count))}
          ${codexFactRow("Proof Cards", fmt(node.card_count))}
          ${codexFactRow("Thumbnail", "generated node icon")}
        </div>
        <div class="section-kicker">Linked Capabilities</div>
        <div class="game-list loadout-side-list">${capRows || `<div class="empty">No direct capability bridge registered for this node yet.</div>`}</div>
        <div class="section-kicker">Related Media</div>
        <div class="game-list loadout-side-list">${mediaRows || `<div class="empty">No direct media artifact matched; using generated node thumbnail.</div>`}</div>
        <div class="section-kicker">Source Path</div>
        <div class="source-link">${esc(node.source_path || node.node_id || "")}</div>
      </div>`;
    }
    function renderPresentationLoadout() {
      if (!["all", ...DATA.node_type_summary.map((item) => item.label)].includes(state.loadoutType)) state.loadoutType = "all";
      const visibleNodes = loadoutNodes();
      const selected = selectedLoadoutNode();
      const relatedCaps = loadoutCapabilitiesForNode(selected);
      const nodeSlots = visibleNodes.map((node) => loadoutNodeCard(node)).join("");
      const agentSlots = DATA.agents.slice(0, 8).map((agent) => gameListRow(agent.label, agent.agent_kind || "agent")).join("");
      const protocolSlots = DATA.protocols.slice(0, 8).map((protocol) => gameListRow(protocol.title, protocol.article_type || "protocol")).join("");
      const mediaSlots = DATA.media.slice(0, 8).map((media) => gameListRow(media.target_label || media.visual_label || media.job_id, media.status || "media")).join("");
      const summary = [
        [visibleNodes.length, "visible nodes"],
        [DATA.nodes.length, "known nodes"],
        [visibleNodes.reduce((sum, node) => sum + Number(node.card_count || 0), 0), "proof cards"],
        [relatedCaps.length, "selected links"]
      ].map(([value, label]) => `<div class="proof-chip-big"><strong>${fmt(value)}</strong><span>${esc(label)}</span></div>`).join("");
      return `<div class="game-frame"><div class="game-panel loadout-grid">
        <section class="game-card loadout-armory">
          <div class="loadout-head">
            <div><h4>All Known Hapa Nodes</h4><p>${esc("Every indexed Hapa node is represented as equipment. Use the type filters to scan the armory, then select any node to inspect its proof, score, capabilities, media, and source path.")}</p></div>
            ${badge(`${fmt(DATA.nodes.length)} nodes`, "gold")}
          </div>
          ${loadoutTypeFilters()}
          <div class="loadout-summary-strip">${summary}</div>
          <div class="slot-grid loadout-node-grid">${nodeSlots || `<div class="empty">No nodes match this loadout filter.</div>`}</div>
        </section>
        <aside class="game-side-stack">
          ${loadoutInspector(selected)}
          <div class="game-card"><h4>Agent Companions</h4><div class="game-list">${agentSlots}</div></div>
          <div class="game-card"><h4>Protocol Runes</h4><div class="game-list">${protocolSlots}</div></div>
          <div class="game-card"><h4>Media Artifacts</h4><div class="game-list">${mediaSlots}</div></div>
        </aside>
      </div></div>`;
    }
    function renderPresentationTimeline() {
      if (!timelineLayers().some((layer) => layer.key === state.timelineLayer)) state.timelineLayer = "all";
      if (state.timelineEra !== "all" && !(DATA.timeline?.eras || []).some((era) => era.id === state.timelineEra)) state.timelineEra = "all";
      if (!timelineScales().some((scale) => scale.key === state.timelineScale)) state.timelineScale = "month";
      const selected = selectedTimelineBeat();
      const summary = DATA.timeline?.summary || {};
      const scaleMeta = timelineScaleMeta(state.timelineScale);
      const kpis = [
        [summary.timeline_events, "Timeline Events"],
        [summary.turn_events, "AI Turn Events"],
        [summary.skill_events, "Skill Unlocks"],
        [summary.node_events + summary.capability_events, "Node/Caps"],
        [summary.daily_buckets, "Active Days"],
        [summary.peak_day_events, "Peak Day Events"]
      ].map(([value, label]) => `<div class="proof-chip-big"><strong>${fmt(value)}</strong><span>${esc(label)}</span></div>`).join("");
      const beats = timelineFilteredBeats();
      return `<div class="game-frame"><div class="game-panel timeline-shell">
        <div class="timeline-brief">
          <section class="game-card timeline-title-card">
            <div class="section-kicker">Lore / Canon Timeline</div>
            <h3>Chronicle Rail</h3>
            <p>${esc("A playable history of how source material, AI turns, skill consolidation, Hapa nodes, and capability unlocks became the Character Sheet's professional canon.")}</p>
            <div class="tag-row" style="margin-top:12px">${chips(["knowledge acquired", "turn forge", "skill unlocks", "node creation", "capability canon"], "cyan")}</div>
          </section>
          <aside class="game-card"><h4>Timeline Scope</h4><div class="timeline-kpi-grid">${kpis}</div><div class="source-link" style="margin-top:10px">${esc(timelineDateLabel(summary.first_event_at))} -> ${esc(timelineDateLabel(summary.latest_event_at))}</div></aside>
        </div>
        ${timelineScaleRail()}
        ${timelineDailyBrief()}
        ${timelineEraRail()}
        ${timelineLayerRail()}
        <div class="timeline-layout">
          <aside class="game-card"><h4>Canon Beats</h4><p>${esc(`${fmt(beats.length)} representative beats in the current filter. Select one to inspect proof, source, metrics, and linked sheet records.`)}</p>${timelineBeatList()}</aside>
          <section class="game-card timeline-series-panel"><h4>${esc(scaleMeta.label)} Activity</h4><p>${esc(`${scaleMeta.body} Series is compressed from Second Brain metrics, with skill creation synthesized from the skill inventory projection.`)}</p>${timelineStackedLineChart()}${timelineSeries()}</section>
          ${timelineInspector(selected)}
        </div>
        ${timelineSourcePanels()}
      </div></div>`;
    }
    function profileData() {
      return DATA.character_profile || { foundation: {}, runs: {}, profile_runs: [], ledger: { observations: [], total: 0 }, voice_model: [], evidence_examples: [], sharpened_observations: [] };
    }
    function profileStatusBadge(value) {
      const text = String(value || "observed").toLowerCase();
      const cls = text.includes("hyp") ? "rose" : text.includes("infer") ? "pink" : text.includes("sharp") ? "gold" : "cyan";
      return badge(text || "observed", cls);
    }
    function profileRunCard(run, index) {
      const takeaways = (run.takeaways || []).slice(0, 4).map((item) => `<div class="game-list-row"><span>${esc(item)}</span><strong>${index + 1}</strong></div>`).join("");
      return `<article class="profile-run-card">
        <div class="record-title"><strong>${esc(run.label || run.id || "Profile Run")}</strong>${profileStatusBadge(run.status)}</div>
        <div class="record-meta">${esc(run.executed_at || "")}</div>
        <p>${esc(run.method || "Profile mining pass")}</p>
        <div class="section-kicker" style="margin-top:12px">Takeaways</div>
        <div class="game-list">${takeaways}</div>
      </article>`;
    }
    function profileSectionCard([key, items]) {
      const list = Array.isArray(items) ? items : [];
      const top = list[0] || {};
      return `<article class="profile-section-card">
        <div>
          <em>${esc(String(key).replaceAll("_", " "))}</em>
          <strong>${esc(top.label || prettyFamily(key))}</strong>
          <p>${esc(top.claim || "Profile section ready for deeper mining.")}</p>
        </div>
        <div class="profile-status-strip">${profileStatusBadge(top.status)}${badge(`${Math.round(Number(top.confidence || 0) * 100)}%`, "gold")}${badge(`${fmt(list.length)} cards`, "cyan")}</div>
      </article>`;
    }
    function profileObservationCard(obs) {
      const support = (obs.support || []).slice(0, 3).map((item) => item.label || item.id || item.type).filter(Boolean);
      const safe = obs.public_safe === false ? badge("Owner Review", "rose") : badge("Public Safe", "green");
      return `<article class="profile-observation-card">
        <div class="record-title"><strong>${esc(obs.claim || obs.label || obs.id)}</strong>${safe}</div>
        <div class="record-meta">${esc(obs.id || "")} / ${esc(obs.category || "observation")} / ${esc(obs.ts || "")}</div>
        <div class="profile-status-strip">${profileStatusBadge(obs.status)}${badge(`${Math.round(Number(obs.confidence || 0) * 100)}%`, "gold")}${chips(support, "cyan")}</div>
        ${obs.agent_use ? `<p>${esc(obs.agent_use)}</p>` : ""}
      </article>`;
    }
    function profileVoiceCard(item) {
      const examples = (item.examples || []).slice(0, 4).map((example) => badge(example, "cyan")).join("");
      return `<article class="profile-voice-card">
        <em>${esc(item.label || "Voice")}</em>
        <strong>${esc(item.agent_move || "Apply this voice layer.")}</strong>
        <div class="tag-row" style="margin-top:10px">${examples}</div>
      </article>`;
    }
    function profileBackgroundVideos() {
      const videos = DATA.profile_background_videos?.items || [];
      if (!videos.length) return "";
      const poster = videos[0]?.poster || "";
      return `<div class="profile-video-backdrop" aria-hidden="true">
        ${poster ? `<div class="profile-video-poster" style="background-image:url('${esc(poster)}')"></div>` : ""}
        ${videos.slice(0, 2).map((item, index) => `<video class="profile-bg-video ${index === 0 ? "is-primary" : "is-secondary"}" autoplay muted loop playsinline preload="auto" poster="${esc(item.poster || "")}"><source src="${esc(item.url)}" type="video/mp4"></video>`).join("")}
      </div>`;
    }
    function renderPresentationProfile() {
      const profile = profileData();
      const foundation = profile.foundation || {};
      const runs = profile.profile_runs || [];
      const ledger = profile.ledger || { observations: [], total: 0, category_counts: [], status_counts: [] };
      const runCards = runs.map(profileRunCard).join("");
      const sections = Object.entries(foundation.sections || {}).map(profileSectionCard).join("");
      const observations = (ledger.observations || []).map(profileObservationCard).join("");
      const voice = (profile.voice_model || []).map(profileVoiceCard).join("");
      const adapter = (profile.runs?.persona_adapter_delta || []).map((item, index) => gameListRow(item, `Rule ${index + 1}`)).join("");
      const evidence = (profile.evidence_examples || []).map((item) => gameListRow(item.label || item.id, item.signal || "evidence")).join("");
      const categoryRows = (ledger.category_counts || []).slice(0, 8).map((item) => gameListRow(prettyFamily(item.label), fmt(item.count))).join("");
      const kpis = [
        [runs.length, "Profile Runs"],
        [ledger.total || 0, "Observation Cards"],
        [ledger.public_safe_count || 0, "Public Safe"],
        [ledger.owner_review_count || 0, "Owner Review"],
        [profile.flow?.step_count || 0, "Protocol Steps"],
        [Object.keys(foundation.sections || {}).length, "Dossier Sections"]
      ].map(([value, label]) => `<div class="proof-chip-big"><strong>${fmt(value)}</strong><span>${esc(label)}</span></div>`).join("");
      return `<div class="game-frame"><div class="game-panel profile-shell">
        <div class="profile-brief">
          <section class="game-card profile-title-card">
            ${profileBackgroundVideos()}
            <div class="section-kicker">Character Profile / Lore Dossier</div>
            <h3>Persona Codex</h3>
            <p>${esc("A mined personality, voice, lore, motive, relationship, value, and agent-adapter layer generated from Hapa turns, skills, nodes, protocols, timeline, and board evidence.")}</p>
            <div class="tag-row" style="margin-top:14px">${chips(["human dossier", "agent adapter", "append-only ledger", "public/owner split", "profile refresh"], "cyan")}</div>
          </section>
          <aside class="game-card">
            <h4>Profile Scope</h4>
            <div class="profile-kpi-grid">${kpis}</div>
            <div class="section-kicker" style="margin-top:12px">Observation Mix</div>
            <div class="game-list">${categoryRows}</div>
          </aside>
        </div>
        <section class="game-card">
          <div class="record-title"><h4>Mining Runs</h4>${badge(profile.runs?.latest_pass || "run_2_sharpen", "gold")}</div>
          <div class="profile-run-grid">${runCards}</div>
        </section>
        <section class="game-card">
          <h4>Dossier Sections</h4>
          <div class="profile-section-grid">${sections}</div>
        </section>
        <section class="game-card">
          <h4>Voice Model</h4>
          <div class="profile-voice-grid">${voice}</div>
        </section>
        <div class="profile-lower-grid">
          <aside class="game-card profile-adapter">
            <h4>Agent Persona Adapter Delta</h4>
            <p>${esc("Second pass guidance for agents that need to collaborate in Calder's style without claiming to be Calder or leaking private raw turns.")}</p>
            <div class="game-list" style="margin-top:12px">${adapter}</div>
            <div class="section-kicker" style="margin-top:12px">Evidence Examples</div>
            <div class="game-list">${evidence}</div>
          </aside>
          <section class="game-card">
            <h4>Latest Observation Cards</h4>
            <div class="profile-ledger-scroll">${observations}</div>
          </section>
          <aside class="game-card">
            <h4>Open Questions</h4>
            <div class="game-list">${(foundation.open_questions || []).map((item, index) => gameListRow(item, `Q${index + 1}`)).join("")}</div>
            <div class="section-kicker" style="margin-top:12px">Files</div>
            <div class="game-list">${Object.entries(profile.files || {}).slice(0, 8).map(([key, path]) => gameListRow(prettyFamily(key), String(path).split("/").pop())).join("")}</div>
          </aside>
        </div>
      </div></div>`;
    }
    function passportDetail() {
      const focus = state.passportFocus || "metric:evidence";
      const statDescriptions = {
        Systems: "Systems compresses data modeling, architecture, runtime, product, simulation, and engineering capability into one character-sheet attribute.",
        Signal: "Signal describes retrieval, attribution, privacy, source quality, and relationship traversal: the ability to find the right proof at the right time.",
        Forge: "Forge is the production stat: media pipelines, video/audio, artifacts, cards, and visual outputs created from the knowledge system.",
        Stewardship: "Stewardship covers validation, hygiene, integrity, testing, attachment management, and keeping the Second Brain trustworthy over time.",
        Lore: "Lore represents Hapa curation, worldbuilding, taxonomies, writing, and the knowledge memory that gives the system continuity.",
        Tempo: "Tempo is orchestration speed: tools, agents, runtime flows, and automation that move work from idea to shipped artifact.",
        Craft: "Craft is implementation quality across product engineering, APIs, CLI flows, design systems, Unity/3D guidance, and usable surfaces.",
        Communion: "Communion is the bridge layer between people, agents, protocols, and shared operating memory."
      };
      if (focus.startsWith("metric:")) {
        const key = focus.split(":")[1];
        const metricMap = {
          evidence: {
            title: "Evidence XP",
            kind: "Metric",
            body: "Evidence XP is the compressed proof layer: skill-evidence records showing where abilities are supported by sources, turns, artifacts, topics, and Hapa outputs.",
            lower: DATA.skill_families.slice(0, 8).map((family) => ({ label: family.label.replaceAll("_", " "), value: fmt(family.evidence_count) })),
            examples: DATA.skills.slice(0, 6).map((skill) => ({ title: skill.label, meta: `${fmt(skill.evidence_count)} evidence / ${skill.rank} rank`, body: skill.summary }))
          },
          skills: {
            title: "Skills",
            kind: "Metric",
            body: "Skills are the professional capabilities consolidated from consumed material, AI turns, Hapa outputs, and enrichment passes.",
            lower: DATA.skill_families.slice(0, 8).map((family) => ({ label: family.label.replaceAll("_", " "), value: `${fmt(family.skill_count)} skills` })),
            examples: DATA.skills.slice(0, 6).map((skill) => ({ title: skill.label, meta: `${skill.skill_family} / ${skill.rank} / ${fmt(skill.source_count)} sources`, body: skill.summary }))
          },
          nodes: {
            title: "Hapa Nodes",
            kind: "Metric",
            body: "Nodes are portfolio artifacts and operating surfaces: apps, workflows, docs, protocols, and tools produced or managed inside Hapa.",
            lower: DATA.node_type_summary.slice(0, 8).map((item) => ({ label: item.label.replaceAll("_", " "), value: fmt(item.count) })),
            examples: DATA.nodes.slice(0, 6).map((node) => ({ title: node.label, meta: `${node.node_type} / ${fmt(node.topic_count)} topics`, body: node.description }))
          },
          turns: {
            title: "AI Turns",
            kind: "Metric",
            body: "Turns are applied practice records: conversations where knowledge was used, artifacts were produced, and skill/result lineage can be traced.",
            lower: aggregateBy(DATA.turns, "platform").slice(0, 8),
            examples: DATA.turns.slice(0, 6).map((turn) => ({ title: turn.objective || turn.thread_title || turn.turn_id, meta: `${turn.platform} / ${fmt(turn.learning_link_count)} learning / ${fmt(turn.result_link_count)} result`, body: turn.model_response_summary || turn.user_excerpt }))
          }
        };
        const item = metricMap[key] || metricMap.evidence;
        return detailCard(item.title, item.kind, item.body, item.lower, item.examples);
      }
      if (focus.startsWith("stat:")) {
        const label = decodeURIComponent(focus.slice(5));
        const stat = DATA.stats.find((item) => item.label === label) || DATA.stats[0];
        const skillExamples = (stat.top_skills || []).map((name) => DATA.skills.find((skill) => skill.label === name)).filter(Boolean);
        return detailCard(
          stat.label,
          "Core Attribute",
          statDescriptions[stat.label] || "A compressed character-sheet stat backed by skill evidence and source/result lineage.",
          [
            { label: "Skill Count", value: fmt(stat.skill_count) },
            { label: "Evidence Links", value: fmt(stat.evidence) },
            { label: "Source Count", value: fmt(stat.source_count) },
            { label: "Attribute Value", value: fmt(stat.value) }
          ],
          skillExamples.map((skill) => ({ title: skill.label, meta: `${skill.skill_family} / ${skill.rank} / ${fmt(skill.evidence_count)} evidence`, body: skill.summary }))
        );
      }
      if (focus.startsWith("skill:")) {
        const id = decodeURIComponent(focus.slice(6));
        const skill = DATA.skills.find((item) => item.skill_id === id) || DATA.skills[0];
        const relatedCaps = DATA.capabilities.filter((cap) => cap.skill_family === skill.skill_family || cap.label.toLowerCase().includes(skill.label.toLowerCase().split(" ")[0])).slice(0, 6);
        const relatedLinks = DATA.learning_links.filter((link) => link.skill_label === skill.label || link.skill_family === skill.skill_family).slice(0, 4);
        return detailCard(
          skill.label,
          "Skill",
          skill.summary || "A consolidated professional skill backed by Second Brain evidence, turns, and artifacts.",
          [
            { label: "Evidence Links", value: fmt(skill.evidence_count) },
            { label: "Sources", value: fmt(skill.source_count) },
            { label: "Artifacts", value: fmt(skill.artifact_count) },
            { label: "Family", value: skill.skill_family.replaceAll("_", " ") }
          ],
          [
            ...relatedCaps.map((cap) => ({ title: cap.label, meta: `${cap.mode} / ${cap.node_label}`, body: cap.description })),
            ...relatedLinks.map((link) => ({ title: link.source_title || link.thread_title || link.link_id, meta: `${link.source_type} / score ${fmt(link.score)}`, body: link.evidence_text }))
          ]
        );
      }
      if (focus.startsWith("proof:")) {
        const key = focus.split(":")[1];
        const proofMap = {
          read: {
            title: "Read",
            body: "Read is the intake layer: source systems and media objects that seeded knowledge, taste, references, and operating patterns.",
            lower: DATA.source_systems.slice(0, 8).map((source) => ({ label: source.source_system || "unknown", value: fmt(source.items) })),
            examples: DATA.mediums.slice(0, 6).map((medium) => ({ title: medium.medium || "medium", meta: `${fmt(medium.items)} items / ${fmt(medium.exposures)} exposures`, body: "Media/source category feeding the Second Brain." }))
          },
          learn: {
            title: "Learn",
            body: "Learn is consolidation: sources, topics, and evidence are grouped into skills and skill families.",
            lower: DATA.skill_families.slice(0, 8).map((family) => ({ label: family.label.replaceAll("_", " "), value: fmt(family.skill_count) })),
            examples: DATA.topics.slice(0, 6).map((topic) => ({ title: topic.label, meta: `${fmt(topic.evidence_count)} evidence / ${fmt(topic.skill_count)} skills`, body: topic.definition || topic.scope_note }))
          },
          practice: {
            title: "Practice",
            body: "Practice is where AI turns demonstrate skills in use: planning, building, validating, explaining, and refining outputs.",
            lower: aggregateBy(DATA.turns, "turn_type").slice(0, 8),
            examples: DATA.turns.slice(0, 6).map((turn) => ({ title: turn.objective || turn.thread_title || turn.turn_id, meta: `${turn.turn_type} / ${turn.platform}`, body: turn.model_response_summary || turn.user_excerpt }))
          },
          build: {
            title: "Build",
            body: "Build is the Hapa output layer: nodes, apps, protocols, media, cards, and workflows created from learning and practice.",
            lower: DATA.node_type_summary.slice(0, 8).map((item) => ({ label: item.label.replaceAll("_", " "), value: fmt(item.count) })),
            examples: DATA.nodes.slice(0, 6).map((node) => ({ title: node.label, meta: `${node.node_type} / ${fmt(node.card_count)} cards`, body: node.description }))
          },
          prove: {
            title: "Prove",
            body: "Prove is the evidence trail: links that justify claims by connecting skills, sources, turns, cards, artifacts, and lineage.",
            lower: DATA.skills.slice(0, 8).map((skill) => ({ label: skill.label, value: fmt(skill.evidence_count) })),
            examples: DATA.learning_links.slice(0, 6).map((link) => ({ title: link.source_title || link.skill_label || link.link_id, meta: `${link.source_type} / score ${fmt(link.score)}`, body: link.evidence_text }))
          },
          publish: {
            title: "Publish",
            body: "Publish is the outward-facing layer: media, screenshots, generated artifacts, protocol cards, and portfolio-ready presentation assets.",
            lower: aggregateBy(DATA.media, "status").slice(0, 8),
            examples: DATA.media.slice(0, 6).map((media) => ({ title: media.target_label || media.visual_label || media.job_id, meta: `${media.status} / ${media.asset_role}`, body: media.prompt_text || media.direction_prompt }))
          }
        };
        const item = proofMap[key] || proofMap.read;
        return detailCard(item.title, "Proof Trail", item.body, item.lower, item.examples);
      }
      if (focus.startsWith("node:")) {
        const id = decodeURIComponent(focus.slice(5));
        const node = DATA.nodes.find((item) => item.node_id === id) || DATA.nodes[0];
        const caps = DATA.capabilities.filter((cap) => cap.node_id === node.node_id || cap.node_label === node.label).slice(0, 6);
        return detailCard(
          node.label,
          "Portfolio Node",
          node.description || "A Hapa node is a portfolio artifact and operating surface backed by topics, bodies, cards, and capabilities.",
          [
            { label: "Type", value: node.node_type.replaceAll("_", " ") },
            { label: "Topics", value: fmt(node.topic_count) },
            { label: "Bodies", value: fmt(node.body_count) },
            { label: "Cards", value: fmt(node.card_count) }
          ],
          caps.map((cap) => ({ title: cap.label, meta: `${cap.mode} / ${cap.skill_family}`, body: cap.description }))
        );
      }
      return passportDetailForDefault();
    }
    function passportDetailForDefault() {
      return detailCard(
        "Evidence XP",
        "Metric",
        "Evidence XP is the compressed proof layer behind the character sheet.",
        DATA.skill_families.slice(0, 8).map((family) => ({ label: family.label.replaceAll("_", " "), value: fmt(family.evidence_count) })),
        DATA.skills.slice(0, 6).map((skill) => ({ title: skill.label, meta: `${fmt(skill.evidence_count)} evidence / ${skill.rank} rank`, body: skill.summary }))
      );
    }
    function renderPresentationPassport() {
      const phoneStats = DATA.stats.map((stat) => gameListRow(stat.label, fmt(stat.value), "", `stat:${encodeURIComponent(stat.label)}`)).join("");
      const featureSkills = DATA.skills.slice(0, 5).map((skill) => gameListRow(skill.label, skill.rank, "", `skill:${encodeURIComponent(skill.skill_id)}`)).join("");
      const proofSteps = [["Read", DATA.summary.items, "proof:read"], ["Learn", DATA.skills.length, "proof:learn"], ["Practice", DATA.summary.turns, "proof:practice"], ["Build", DATA.nodes.length, "proof:build"], ["Prove", DATA.summary.skill_evidence, "proof:prove"], ["Publish", DATA.summary.media_jobs, "proof:publish"]].map(([label, value, key]) => gameListRow(label, fmt(value), "", key)).join("");
      const portfolioNodes = DATA.nodes.slice(0, 4).map((node) => gameListRow(node.label, node.node_type, "", `node:${encodeURIComponent(node.node_id)}`)).join("");
      return `<div class="game-frame"><div class="game-panel passport-wrap">
        <section class="phone-frame"><div class="phone-screen">
          <div class="phone-hero"><div class="section-kicker">Hapa Passport</div><h3>${esc(DATA.profile.name)}</h3>${badge("Rank S", "gold")} ${badge("Knowledge Architect", "cyan")}</div>
          <div class="phone-body">
            <div class="game-proof-strip" style="grid-template-columns:1fr 1fr">${[
              [DATA.summary.skill_evidence, "Evidence", "metric:evidence"],
              [DATA.skills.length, "Skills", "metric:skills"],
              [DATA.nodes.length, "Nodes", "metric:nodes"],
              [DATA.summary.turns, "Turns", "metric:turns"]
            ].map(([v,l,key]) => passportChip(v, l, key)).join("")}</div>
            <div class="game-card"><h4>Core Attributes</h4><div class="game-list">${phoneStats}</div></div>
            <div class="game-card"><h4>Featured Skills</h4><div class="game-list">${featureSkills}</div></div>
            <div class="game-card"><h4>Portfolio Nodes</h4><div class="game-list">${portfolioNodes}</div></div>
          </div>
        </div></section>
        <aside class="game-side-stack">
          ${passportDetail()}
          <div class="game-card"><h4>Proof Trail</h4><div class="game-list">${proofSteps}</div></div>
          <div class="game-card"><h4>Presentation Intent</h4><p>${esc("This mode is for human show-and-tell: tighter hierarchy, game affordances, animation-ready panels, and quick routes back to proof.")}</p>${mockGallery()}</div>
        </aside>
      </div></div>`;
    }
    function renderPresentation() {
      const renderers = { hero: renderPresentationHero, codex: renderPresentationCodex, proof: renderPresentationProof, loadout: renderPresentationLoadout, timeline: renderPresentationTimeline, profile: renderPresentationProfile, passport: renderPresentationPassport };
      return `<div class="presentation-shell">${gameTabs()}${renderers[state.gamePanel]()}</div>`;
    }
    function render() {
      applyCharacterImage();
      setHeader();
      renderNav();
      renderSideStats();
      document.querySelector(".app").classList.toggle("presentation", state.view === "presentation");
      const renderers = { sheet: renderSheet, resume: renderResume, skills: renderSkills, nodes: renderNodes, capabilities: renderCapabilities, lineage: renderLineage, sources: renderSources, media: renderMedia, agents: renderAgents, protocols: renderProtocols, board: renderBoard };
      document.getElementById("content").innerHTML = state.view === "presentation" ? renderPresentation() : renderers[state.panel]();
      document.querySelectorAll("[data-show-more]").forEach((button) => button.addEventListener("click", () => { playTone("select"); state.limit += 120; render(); }));
    }
    document.addEventListener("click", (event) => {
      const soundToggle = event.target.closest("[data-sound-toggle]");
      if (soundToggle) {
        state.sound = !state.sound;
        localStorage.setItem("hapaCharacterSheetSfx", state.sound ? "on" : "off");
        if (state.sound) playTone("toggle");
        render();
      }
      const viewButton = event.target.closest("[data-view]");
      if (viewButton) {
        playTone("select");
        state.view = viewButton.dataset.view;
        window.location.hash = state.view === "presentation" ? `presentation-${state.gamePanel}` : "data";
        render();
      }
      const gameButton = event.target.closest("[data-game-panel]");
      if (gameButton) {
        playTone("select");
        state.gamePanel = gameButton.dataset.gamePanel;
        state.view = "presentation";
        window.location.hash = `presentation-${state.gamePanel}`;
        render();
      }
      const proofFocusButton = event.target.closest("[data-proof-focus]");
      if (proofFocusButton) {
        setProofFocus(proofFocusButton.dataset.proofFocus);
      }
      const loadoutTypeButton = event.target.closest("[data-loadout-type]");
      if (loadoutTypeButton) {
        playTone("change");
        selectLoadoutType(loadoutTypeButton.dataset.loadoutType);
      }
      const loadoutNodeButton = event.target.closest("[data-loadout-node-id]");
      if (loadoutNodeButton) {
        playTone("select");
        selectLoadoutNode(loadoutNodeButton.dataset.loadoutNodeId);
      }
      const timelineEraButton = event.target.closest("[data-timeline-era]");
      if (timelineEraButton) {
        playTone("change");
        selectTimelineEra(timelineEraButton.dataset.timelineEra);
      }
      const timelineLayerButton = event.target.closest("[data-timeline-layer]");
      if (timelineLayerButton) {
        playTone("change");
        selectTimelineLayer(timelineLayerButton.dataset.timelineLayer);
      }
      const timelineScaleButton = event.target.closest("[data-timeline-scale]");
      if (timelineScaleButton) {
        playTone("change");
        selectTimelineScale(timelineScaleButton.dataset.timelineScale);
      }
      const timelineBeatButton = event.target.closest("[data-timeline-beat]");
      if (timelineBeatButton) {
        playTone("select");
        selectTimelineBeat(timelineBeatButton.dataset.timelineBeat);
      }
      const imageSourceButton = event.target.closest("[data-image-source]");
      if (imageSourceButton) {
        const item = (DATA.image_sources?.items || []).find((source) => source.id === imageSourceButton.dataset.imageSource);
        if (item) setCharacterImage(item.url, item.label, item.kind);
      }
      const imageFilterButton = event.target.closest("[data-image-filter]");
      if (imageFilterButton) {
        playTone("change");
        state.imageFilter = imageFilterButton.dataset.imageFilter;
        try { localStorage.setItem("hapaCharacterSheetImageFilter", state.imageFilter); } catch (err) {}
        render();
      }
      const imageResetButton = event.target.closest("[data-image-reset]");
      if (imageResetButton) {
        resetCharacterImage();
      }
      const imageUrlButton = event.target.closest("[data-image-url-apply]");
      if (imageUrlButton) {
        const input = document.querySelector("[data-image-url-input]");
        const value = input?.value?.trim();
        if (value) setCharacterImage(value, "Custom URL", "character_sheet");
      }
      const codexCapabilityButton = event.target.closest("[data-codex-capability]");
      if (codexCapabilityButton) {
        playTone("select");
        selectCodexCapability(codexCapabilityButton.dataset.codexCapability);
        return;
      }
      const codexNodeButton = event.target.closest("[data-codex-node-id]");
      if (codexNodeButton) {
        playTone("select");
        selectCodexNode(codexNodeButton.dataset.codexNodeId);
        return;
      }
      const codexSkillButton = event.target.closest("[data-codex-skill-id]");
      if (codexSkillButton) {
        playTone("select");
        selectCodexSkill(codexSkillButton.dataset.codexSkillId);
        return;
      }
      const codexFamilyButton = event.target.closest("[data-codex-family]");
      if (codexFamilyButton) {
        playTone("select");
        selectCodexFamily(codexFamilyButton.dataset.codexFamily);
        return;
      }
      const passportButton = event.target.closest("[data-passport-detail]");
      if (passportButton) {
        playTone("select");
        state.passportFocus = passportButton.dataset.passportDetail;
        state.gamePanel = "passport";
        state.view = "presentation";
        window.location.hash = `presentation-passport&focus=${encodeURIComponent(state.passportFocus)}`;
        render();
      }
      const panelButton = event.target.closest("[data-panel]");
      if (panelButton) {
        playTone("select");
        state.view = "data";
        state.panel = panelButton.dataset.panel;
        state.limit = 120;
        window.location.hash = "data";
        render();
      }
      const levelButton = event.target.closest("[data-level]");
      if (levelButton) {
        playTone("change");
        state.level = levelButton.dataset.level;
        document.querySelectorAll("[data-level]").forEach((button) => button.classList.toggle("active", button.dataset.level === state.level));
        render();
      }
    });
    document.addEventListener("mouseover", (event) => {
      const target = event.target.closest(".game-list-row, .proof-chip-big, .proof-step, .proof-layer-row, .proof-flow-step, .tree-branch, .graph-node, .slot-card, .loadout-type-filter, .timeline-era-card, .timeline-layer-card, .timeline-scale-card, .timeline-beat-card, .profile-run-card, .profile-section-card, .profile-observation-card, .profile-voice-card, .inventory-item, .quality-row, .quality-pair-row, .quality-dot, .character-rank-row, .skill-highlight-row, .image-source-row, .image-source-filters button, .image-actions button, .image-file-label, .game-tabs button, .mode-switch button, .sound-toggle");
      if (!target || target === lastHoverTarget) return;
      const now = performance.now();
      if (now - lastHoverTone < 90) return;
      lastHoverTarget = target;
      lastHoverTone = now;
      playTone("hover");
    });
    document.addEventListener("change", (event) => {
      const input = event.target.closest("[data-image-file]");
      if (!input || !input.files || !input.files[0]) return;
      const file = input.files[0];
      const reader = new FileReader();
      reader.onload = () => setCharacterImage(String(reader.result || ""), file.name, "character_sheet");
      reader.readAsDataURL(file);
    });
    document.addEventListener("keydown", (event) => {
      const target = event.target.closest(".interactive");
      if (target && (event.key === "Enter" || event.key === " ")) {
        event.preventDefault();
        playTone("select");
        if (target.dataset.passportDetail) {
          state.passportFocus = target.dataset.passportDetail;
          state.gamePanel = "passport";
          state.view = "presentation";
          window.location.hash = `presentation-passport&focus=${encodeURIComponent(state.passportFocus)}`;
          render();
        } else if (target.dataset.codexCapability) {
          selectCodexCapability(target.dataset.codexCapability);
        } else if (target.dataset.codexNodeId) {
          selectCodexNode(target.dataset.codexNodeId);
        } else if (target.dataset.codexSkillId) {
          selectCodexSkill(target.dataset.codexSkillId);
        } else if (target.dataset.codexFamily) {
          selectCodexFamily(target.dataset.codexFamily);
        } else if (target.dataset.proofFocus) {
          setProofFocus(target.dataset.proofFocus);
        } else if (target.dataset.loadoutNodeId) {
          selectLoadoutNode(target.dataset.loadoutNodeId);
        } else if (target.dataset.loadoutType) {
          selectLoadoutType(target.dataset.loadoutType);
        } else if (target.dataset.timelineBeat) {
          selectTimelineBeat(target.dataset.timelineBeat);
        } else if (target.dataset.timelineLayer) {
          selectTimelineLayer(target.dataset.timelineLayer);
        } else if (target.dataset.timelineScale) {
          selectTimelineScale(target.dataset.timelineScale);
        } else if (target.dataset.timelineEra) {
          selectTimelineEra(target.dataset.timelineEra);
        } else if (target.dataset.imageSource) {
          const item = (DATA.image_sources?.items || []).find((source) => source.id === target.dataset.imageSource);
          if (item) setCharacterImage(item.url, item.label, item.kind);
        }
      }
    });
    document.getElementById("q").addEventListener("input", (event) => { state.q = event.target.value.trim(); state.limit = 120; render(); });
    document.getElementById("family-filter").addEventListener("change", (event) => { playTone("change"); state.family = event.target.value; state.limit = 120; render(); });
    document.getElementById("rank-filter").addEventListener("change", (event) => { playTone("change"); state.rank = event.target.value; state.limit = 120; render(); });
    document.getElementById("type-filter").addEventListener("change", (event) => { playTone("change"); state.type = event.target.value; state.limit = 120; render(); });
    document.getElementById("mode-filter").addEventListener("change", (event) => { playTone("change"); state.mode = event.target.value; state.limit = 120; render(); });
    document.getElementById("sort-filter").addEventListener("change", (event) => { playTone("change"); state.sort = event.target.value; render(); });
    fillOptions();
    applyCharacterImage();
    render();
  </script>
</body>
</html>
"""


def clean_text(value: Any, limit: int | None = None) -> str:
    if value is None:
        return ""
    text = str(value)
    replacements = {
        "\u2014": "-",
        "\u2013": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2026": "...",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    text = re.sub(r"\s+", " ", text).strip()
    if limit and len(text) > limit:
        text = text[: max(0, limit - 3)].rstrip() + "..."
    return text


def parse_json(value: Any, default: Any) -> Any:
    if value in (None, ""):
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def read_json_file(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def read_ndjson(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not path.exists():
        return records
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return records
    for line in lines:
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except ValueError:
            continue
        if isinstance(item, dict):
            records.append(item)
    if limit is not None:
        return records[-limit:]
    return records


def label_from_json_item(item: Any) -> str:
    if isinstance(item, dict):
        for key in ("label", "title", "name", "body_label", "skill_label", "topic_label", "article_title"):
            if item.get(key):
                return clean_text(item.get(key), 90)
        if item.get("id"):
            return clean_text(item.get("id"), 90)
    return clean_text(item, 90)


def json_labels(value: Any, limit: int = 8) -> list[str]:
    data = parse_json(value, [])
    if isinstance(data, dict):
        data = list(data.values())
    if not isinstance(data, list):
        return []
    labels: list[str] = []
    for item in data:
        label = label_from_json_item(item)
        if label and label not in labels:
            labels.append(label)
        if len(labels) >= limit:
            break
    return labels


def count_table(conn: sqlite3.Connection, table: str) -> int:
    try:
        row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
        return int(row[0]) if row else 0
    except sqlite3.Error:
        return 0


def rows(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    try:
        return [dict(row) for row in conn.execute(sql, params).fetchall()]
    except sqlite3.Error as exc:
        print(f"query skipped: {exc}")
        return []


def skill_rank(evidence_count: int, source_count: int, artifact_count: int, raw_score: float) -> tuple[str, int]:
    evidence = max(0, int(evidence_count or 0))
    sources = max(0, int(source_count or 0))
    artifacts = max(0, int(artifact_count or 0))
    score = (
        25
        + math.log10(evidence + 1) * 12.0
        + min(18, sources * 1.9)
        + min(16, math.log10(artifacts + 1) * 5.4)
        + min(8, float(raw_score or 0) / 18.0)
    )
    value = max(1, min(99, round(score)))
    if value >= 96:
        return "SS", value
    if value >= 88:
        return "S", value
    if value >= 78:
        return "A", value
    if value >= 66:
        return "B", value
    if value >= 52:
        return "C", value
    return "D", value


STAT_RULES = {
    "Systems": ("data", "architecture", "runtime", "product", "simulation", "unity", "engineering"),
    "Signal": ("retrieval", "knowledge", "curation", "integrity", "topic", "source"),
    "Forge": ("media", "production", "music", "3d", "design", "artifact"),
    "Stewardship": ("quality", "protocol", "integrity", "operations", "data_operations"),
    "Lore": ("knowledge", "hapa", "curation", "music", "media", "body"),
    "Tempo": ("runtime", "agent", "simulation", "music", "flow", "automation"),
    "Craft": ("product", "unity", "design", "media", "engineering", "3d"),
    "Communion": ("agent", "hapa", "retrieval", "knowledge", "protocol", "bridge"),
}


def stat_bucket(skill: dict[str, Any]) -> str:
    haystack = f"{skill.get('skill_family', '')} {skill.get('label', '')}".lower()
    best = ("Craft", 0)
    for label, words in STAT_RULES.items():
        hits = sum(1 for word in words if word in haystack)
        if hits > best[1]:
            best = (label, hits)
    return best[0]


def summarize_board() -> dict[str, Any]:
    events = []
    tasks: dict[str, dict[str, Any]] = {}
    if BOARD_EVENTS.exists():
        for line in BOARD_EVENTS.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except ValueError:
                continue
            payload = event.get("payload") or {}
            flat_event = {
                "id": event.get("id"),
                "ts": clean_text(event.get("ts")),
                "actor": clean_text(event.get("actor")),
                "type": clean_text(event.get("type")),
                "task_id": clean_text(event.get("task_id") or payload.get("taskId")),
                "payload_title": clean_text(payload.get("title"), 140),
                "payload_body": clean_text(payload.get("body") or payload.get("description"), 220),
            }
            events.append(flat_event)
            if event.get("type") == "task_created":
                task_id = payload.get("taskId") or event.get("task_id")
                if not task_id:
                    continue
                tasks[task_id] = {
                    "task_id": clean_text(task_id),
                    "title": clean_text(payload.get("title"), 160),
                    "description": clean_text(payload.get("description"), 320),
                    "column": clean_text(payload.get("column") or "ready"),
                    "owner": clean_text(payload.get("owner")),
                    "priority": clean_text(payload.get("priority")),
                    "node": clean_text(payload.get("node")),
                    "lane": clean_text(payload.get("lane")),
                    "tags": [clean_text(tag, 48) for tag in payload.get("tags", [])],
                    "acceptance": [clean_text(item, 90) for item in payload.get("acceptance", [])],
                }
            elif event.get("type") in {"task_moved", "task_updated"}:
                task_id = payload.get("taskId") or event.get("task_id")
                if task_id and task_id in tasks:
                    if payload.get("column"):
                        tasks[task_id]["column"] = clean_text(payload.get("column"))
    task_list = list(tasks.values())
    counts = Counter(task.get("column") or "ready" for task in task_list)
    preferred = ["done", "active", "ready", "backlog", "blocked"]
    columns = [
        {
            "label": label,
            "count": counts.get(label, 0),
            "description": {
                "done": "Completed or verified design/development card.",
                "active": "In-flight implementation work.",
                "ready": "Ready to pick up as the next build slice.",
                "backlog": "Parked future iteration.",
                "blocked": "Needs external input or missing dependency.",
            }.get(label, "Kanban column"),
        }
        for label in preferred
        if label in counts or label in {"done", "ready", "blocked"}
    ]
    for label, count in counts.items():
        if label not in preferred:
            columns.append({"label": label, "count": count, "description": "Custom board column"})
    return {
        "tasks": task_list,
        "events": events,
        "columns": columns,
        "counts": dict(counts),
    }


def summarize_refresh_log() -> dict[str, Any]:
    events = []
    if REFRESH_LOG.exists():
        for line in REFRESH_LOG.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except ValueError:
                continue
            payload = event.get("payload") or {}
            events.append(
                {
                    "id": clean_text(event.get("id"), 120),
                    "ts": clean_text(event.get("ts"), 80),
                    "actor": clean_text(event.get("actor") or "unknown", 80),
                    "type": clean_text(event.get("type"), 80),
                    "run_id": clean_text(event.get("run_id") or payload.get("run_id"), 120),
                    "status": clean_text(payload.get("status") or event.get("status"), 40),
                    "trigger": clean_text(payload.get("trigger"), 80),
                    "source": clean_text(payload.get("source"), 180),
                    "summary": payload.get("summary") or {},
                    "validation": payload.get("validation") or [],
                }
            )
    last_event = events[-1] if events else {}
    last_success = next((event for event in reversed(events) if event.get("status") == "success" or event.get("type") == "refresh_completed"), {})
    last_failure = next((event for event in reversed(events) if event.get("status") == "failed" or event.get("type") == "refresh_failed"), {})
    return {
        "protocol_id": "hapa-character-sheet-refresh-protocol",
        "protocol_doc": str(REFRESH_PROTOCOL),
        "log_path": str(REFRESH_LOG),
        "last_event": last_event,
        "last_success": last_success,
        "last_failure": last_failure,
        "events": events[-20:],
        "event_count": len(events),
        "record_rule": "Refreshes are append-only events. Second Brain remains source truth; Character Sheet rebuilds projections; board events track implementation/protocol changes.",
    }


def doc_summary(path_str: str) -> dict[str, str]:
    path = Path(path_str)
    if not path.exists():
        return {
            "title": path.name,
            "kind": "missing",
            "summary": "Configured path was not present during this projection build.",
            "path": path_str,
        }
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    title = path.stem.replace("-", " ").replace("_", " ")
    for line in lines[:12]:
        if line.startswith("#"):
            title = clean_text(line.lstrip("#").strip(), 90)
            break
    body = " ".join(line.lstrip("#").strip() for line in lines[:24] if not line.startswith("```"))
    return {
        "title": title,
        "kind": "doc" if path.suffix.lower() == ".md" else path.suffix.lower().lstrip("."),
        "summary": clean_text(body, 340),
        "path": path_str,
    }


def summarize_character_profile() -> dict[str, Any]:
    foundation = read_json_file(CHARACTER_PROFILE_STRUCTURED, {})
    runs = read_json_file(CHARACTER_PROFILE_RUNS, {})
    flow = read_json_file(CHARACTER_PROFILE_FLOW, {})
    ledger = read_ndjson(CHARACTER_PROFILE_LEDGER)
    category_counts = Counter(clean_text(item.get("category") or "unknown", 40) for item in ledger)
    status_counts = Counter(clean_text(item.get("status") or "unknown", 40) for item in ledger)
    public_safe_count = sum(1 for item in ledger if item.get("public_safe") is True)
    owner_review_count = sum(1 for item in ledger if item.get("public_safe") is False)
    sections = foundation.get("sections") if isinstance(foundation.get("sections"), dict) else {}
    section_counts = {
        clean_text(key, 80): len(value) if isinstance(value, list) else 0
        for key, value in sections.items()
    }
    latest_observations = sorted(
        ledger,
        key=lambda item: (clean_text(item.get("ts")), clean_text(item.get("id"))),
        reverse=True,
    )[:12]
    profile_runs = runs.get("profile_runs") if isinstance(runs.get("profile_runs"), list) else []
    sharpened = runs.get("sharpened_observations") if isinstance(runs.get("sharpened_observations"), list) else []
    evidence_examples = runs.get("evidence_examples") if isinstance(runs.get("evidence_examples"), list) else []
    voice_model = runs.get("voice_model") if isinstance(runs.get("voice_model"), list) else []
    return {
        "protocol_id": "hapa-character-profile-mining-protocol",
        "foundation": foundation,
        "runs": runs,
        "profile_runs": profile_runs,
        "sharpened_observations": sharpened,
        "voice_model": voice_model,
        "evidence_examples": evidence_examples,
        "ledger": {
            "path": str(CHARACTER_PROFILE_LEDGER),
            "observations": latest_observations,
            "total": len(ledger),
            "category_counts": [{"label": label, "count": count} for label, count in category_counts.most_common()],
            "status_counts": [{"label": label, "count": count} for label, count in status_counts.most_common()],
            "public_safe_count": public_safe_count,
            "owner_review_count": owner_review_count,
        },
        "section_counts": section_counts,
        "flow": {
            "id": clean_text(flow.get("id"), 100),
            "name": clean_text(flow.get("name"), 120),
            "summary": clean_text(flow.get("summary"), 260),
            "step_count": len(flow.get("steps") or []),
        },
        "files": {
            "protocol": str(CHARACTER_PROFILE_PROTOCOL),
            "prompt": str(CHARACTER_PROFILE_PROMPT),
            "foundation_md": str(CHARACTER_PROFILE_DOSSIER),
            "foundation_json": str(CHARACTER_PROFILE_STRUCTURED),
            "sharpened_md": str(CHARACTER_PROFILE_SHARPENED),
            "runs_json": str(CHARACTER_PROFILE_RUNS),
            "ledger": str(CHARACTER_PROFILE_LEDGER),
            "flow": str(CHARACTER_PROFILE_FLOW),
        },
    }


def file_preview_path(path: str) -> str:
    if not path:
        return ""
    p = Path(path)
    if p.exists() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
        return str(p)
    return ""


def file_url(path: str | Path) -> str:
    try:
        p = Path(path)
        if p.exists():
            return p.resolve().as_uri()
    except (TypeError, ValueError):
        return ""
    return ""


def image_source(source_id: str, source_app: str, kind: str, label: str, url: str, path: str = "", meta: str = "", app_link: str = "", rank: int = 0) -> dict[str, Any]:
    return {
        "id": clean_text(source_id, 140),
        "source_app": clean_text(source_app, 80),
        "kind": clean_text(kind, 50),
        "label": clean_text(label, 150),
        "url": clean_text(url, 500),
        "path": clean_text(path, 500),
        "meta": clean_text(meta, 180),
        "app_link": clean_text(app_link, 500),
        "rank": int(rank or 0),
    }


def discover_avatar_image_sources(limit: int = 240) -> list[dict[str, Any]]:
    if not AVATAR_INDEX.exists():
        return []
    try:
        data = json.loads(AVATAR_INDEX.read_text(encoding="utf-8"))
    except ValueError:
        return []
    app_link = file_url(AVATAR_DASHBOARD_LINK) or file_url(AVATAR_INDEX.parent)
    sources = []
    for avatar in data.get("avatars", []):
        avatar_name = clean_text(avatar.get("name") or avatar.get("id"), 80)
        for index, image in enumerate(avatar.get("images", [])):
            path = image.get("path") if isinstance(image, dict) else str(image)
            if not path or not Path(path).exists():
                continue
            url = image.get("url") if isinstance(image, dict) else ""
            if not url:
                url = file_url(path)
            title = image.get("title") if isinstance(image, dict) else Path(path).stem
            rel = image.get("relativePath") if isinstance(image, dict) else Path(path).name
            sources.append(
                image_source(
                    f"avatar:{avatar.get('id') or avatar_name}:{index}",
                    "Hapa Avatar Dashboard",
                    "avatar",
                    f"{avatar_name} - {clean_text(title, 70)}",
                    url,
                    path,
                    rel,
                    app_link,
                    900 - len(sources),
                )
            )
            if len(sources) >= limit:
                return sources
    return sources


def discover_asset_viewer_image_sources(limit: int = 120) -> list[dict[str, Any]]:
    if not ASSET_VIEWER_REGISTRY.exists():
        return []
    try:
        data = json.loads(ASSET_VIEWER_REGISTRY.read_text(encoding="utf-8"))
    except ValueError:
        return []
    app_link = file_url(ASSET_VIEWER_APP) or file_url(ASSET_VIEWER_REGISTRY.parent)
    sources = []
    for run_id, record in (data.get("runs") or {}).items():
        output_dir = Path(record.get("outputDir") or "")
        candidates = []
        if output_dir.exists():
            candidates.extend(sorted(output_dir.glob("*.preview.png")))
            candidates.extend(sorted(output_dir.glob("*.png")))
            candidates.extend(sorted(output_dir.glob("*.jpg")))
            candidates.extend(sorted(output_dir.glob("*.jpeg")))
            candidates.extend(sorted(output_dir.glob("*.webp")))
        seen = set()
        for path in candidates:
            if path in seen or not path.exists():
                continue
            seen.add(path)
            sources.append(
                image_source(
                    f"asset-viewer:{run_id}:{len(sources)}",
                    "Hapa Asset Viewer",
                    "asset_viewer",
                    record.get("name") or run_id,
                    file_url(path),
                    str(path),
                    path.name,
                    app_link,
                    650 - len(sources),
                )
            )
            break
        if len(sources) >= limit:
            break
    return sources


def build_character_image_sources(media: list[dict[str, Any]]) -> dict[str, Any]:
    app_links = {
        "avatar_dashboard": file_url(AVATAR_DASHBOARD_LINK) or file_url(AVATAR_INDEX.parent),
        "asset_viewer": file_url(ASSET_VIEWER_APP) or file_url(ASSET_VIEWER_REGISTRY.parent),
        "media_registry": file_url(MEDIA_REGISTRY_INDEX),
    }
    defaults = [
        image_source("character-model:calder-loop-poster", "Character Sheet", "character_model", "Calder Character Model Poster", "assets/calder-character-model-poster.jpg", str(CHARACTER_MODEL_POSTER), "looping model poster", "", 1030),
        image_source("character-sheet:passport", "Character Sheet", "character_sheet", "Mobile Passport Mock", "hapa-character-sheet-game-mock-04-mobile-passport.png", str(OUT / "hapa-character-sheet-game-mock-04-mobile-passport.png"), "presentation mock", "", 1000),
        image_source("character-sheet:avatar-lineage", "Character Sheet", "character_sheet", "Avatar Lineage Thumbnail", "assets/avatar-lineage-thumbnail.png", str(OUT / "assets/avatar-lineage-thumbnail.png"), "protocol card", "", 990),
        image_source("character-sheet:hero", "Character Sheet", "character_sheet", "Hero Detail Mock", "hapa-character-sheet-game-mock-01-hero-detail.png", str(OUT / "hapa-character-sheet-game-mock-01-hero-detail.png"), "presentation mock", "", 980),
    ]
    media_sources = []
    for item in media:
        preview = item.get("preview_path") or ""
        if not preview:
            continue
        url = file_url(preview) if Path(preview).exists() else preview
        label = item.get("target_label") or item.get("visual_label") or item.get("job_id")
        media_sources.append(
            image_source(
                f"media:{item.get('job_id') or len(media_sources)}",
                "Hapa Media Registry",
                "media_registry",
                label,
                url,
                item.get("output_local_path") or preview,
                " / ".join(filter(None, [item.get("asset_role"), item.get("status"), item.get("media_type")])),
                app_links["media_registry"],
                500 - len(media_sources),
            )
        )
        if len(media_sources) >= 160:
            break
    items = defaults + discover_avatar_image_sources() + discover_asset_viewer_image_sources() + media_sources
    return {
        "default_url": defaults[0]["url"],
        "default_label": defaults[0]["label"],
        "app_links": app_links,
        "items": sorted(items, key=lambda item: item.get("rank", 0), reverse=True),
    }


def build_character_models() -> dict[str, Any]:
    items = []
    if CHARACTER_MODEL_VIDEO.exists():
        items.append(
            {
                "id": "character-model:calder-loop",
                "label": "Calder Character Model Loop",
                "kind": "looping_video",
                "display_role": "Hero Character Model",
                "url": "assets/calder-character-video-loop.mp4",
                "poster": "assets/calder-character-model-poster.jpg" if CHARACTER_MODEL_POSTER.exists() else "",
                "source_path": str(CHARACTER_MODEL_VIDEO),
                "poster_path": str(CHARACTER_MODEL_POSTER) if CHARACTER_MODEL_POSTER.exists() else "",
                "resolution": "720 x 1280",
                "duration": "10s",
                "loop": "Muted Autoplay Loop",
                "status": "active",
                "meta": "10s vertical MP4 / video-game character sheet model",
                "tags": ["character-model", "presentation-hero", "video-loop", "portfolio-media"],
            }
        )
    return {
        "default_model_id": items[0]["id"] if items else "",
        "items": items,
    }


def build_profile_background_videos() -> dict[str, Any]:
    items = []
    for asset in PROFILE_BACKGROUND_VIDEO_ASSETS:
        source = asset["source"]
        if not source.exists():
            continue
        poster_source = asset["poster_source"]
        items.append(
            {
                "id": asset["id"],
                "label": asset["label"],
                "kind": "profile_background_video",
                "display_role": "Persona Codex Hero Background",
                "url": asset["url"],
                "poster": asset["poster"] if poster_source.exists() else "",
                "source_path": str(source),
                "poster_path": str(poster_source) if poster_source.exists() else "",
                "resolution": "1280 x 720",
                "duration": "10s",
                "loop": "Muted Autoplay Background Cycle",
                "status": "active",
                "meta": asset["meta"],
                "tags": ["profile", "persona-codex", "presentation-profile", "video-loop", "background-media"],
            }
        )
    return {
        "default_video_id": items[0]["id"] if items else "",
        "cycle_seconds": 10,
        "count": len(items),
        "items": items,
        "record_rule": "Profile background videos are local-first presentation media for the Persona Codex top card.",
    }


def build_skill_video_loops() -> dict[str, Any]:
    items = []
    for asset in SKILL_VIDEO_LOOP_ASSETS:
        source = asset["source"]
        if not source.exists():
            continue
        poster_source = asset["poster_source"]
        items.append(
            {
                "id": asset["id"],
                "label": asset["label"],
                "verb": asset["verb"],
                "kind": "skill_loop_video",
                "display_role": "Skill Codex Preview Loop",
                "url": asset["url"],
                "poster": asset["poster"] if poster_source.exists() else "",
                "source_path": str(source),
                "poster_path": str(poster_source) if poster_source.exists() else "",
                "resolution": "720 x 1280",
                "duration": "8s",
                "loop": "Muted Autoplay Loop",
                "status": "active",
                "meta": asset["meta"],
                "tags": ["skill-loop", "presentation-codex", "video-loop", "skill-preview"],
            }
        )
    return {
        "default_loop_id": items[0]["id"] if items else "",
        "items": items,
    }


TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9+/_-]{2,}")
SKILL_RANKING_STOPWORDS = {
    "about",
    "across",
    "after",
    "agent",
    "agents",
    "also",
    "and",
    "are",
    "asset",
    "assets",
    "avatar",
    "avatars",
    "body",
    "build",
    "built",
    "card",
    "cards",
    "character",
    "codex",
    "data",
    "does",
    "each",
    "evidence",
    "from",
    "hapa",
    "including",
    "into",
    "local",
    "make",
    "media",
    "node",
    "nodes",
    "over",
    "pairs",
    "proof",
    "protocol",
    "protocols",
    "records",
    "sheet",
    "skill",
    "skills",
    "source",
    "sources",
    "system",
    "systems",
    "that",
    "the",
    "their",
    "this",
    "turn",
    "turns",
    "using",
    "with",
    "work",
}


def rank_band(score: float) -> str:
    if score >= 96:
        return "SS"
    if score >= 88:
        return "S"
    if score >= 74:
        return "A"
    if score >= 58:
        return "B"
    if score >= 42:
        return "C"
    return "D"


def log_norm(value: float, max_value: float) -> float:
    if max_value <= 0:
        return 0.0
    return max(0.0, min(1.0, math.log10(max(0.0, value) + 1) / max_value))


def ranking_tokens(text: Any) -> list[str]:
    tokens = []
    for token in TOKEN_RE.findall(clean_text(text).lower()):
        token = token.strip("_-/")
        if len(token) < 4 or token.isdigit() or "/" in token or token in SKILL_RANKING_STOPWORDS:
            continue
        tokens.append(token)
    return tokens


def ranking_text_fragments(value: Any, depth: int = 0) -> list[str]:
    if depth > 4 or value in (None, ""):
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (int, float)):
        return [str(value)]
    if isinstance(value, list):
        fragments: list[str] = []
        for item in value[:80]:
            fragments.extend(ranking_text_fragments(item, depth + 1))
        return fragments
    if isinstance(value, dict):
        fragments = []
        for key in (
            "name",
            "title",
            "summary",
            "conceptText",
            "dossierText",
            "lookbookText",
            "imageTextSummary",
            "plainText",
            "imageKind",
            "relativePath",
            "images",
            "imageTextRecords",
            "cardProfile",
            "documents",
            "visualExtraction",
            "relatedNames",
            "role",
            "description",
            "body",
        ):
            if key in value:
                fragments.extend(ranking_text_fragments(value.get(key), depth + 1))
        return fragments
    return []


def build_avatar_profiles_for_ranking() -> list[dict[str, Any]]:
    if not AVATAR_INDEX.exists():
        return []
    try:
        data = json.loads(AVATAR_INDEX.read_text(encoding="utf-8"))
    except ValueError:
        return []
    profiles = []
    for avatar in data.get("avatars", []):
        images = avatar.get("images") if isinstance(avatar.get("images"), list) else []
        fragments = ranking_text_fragments(avatar)
        image_kinds = Counter()
        latest = clean_text(avatar.get("latestModifiedAt"), 80)
        thumbnail_url = ""
        for image in images:
            if not isinstance(image, dict):
                continue
            image_kinds[clean_text(image.get("imageKind") or "image", 50)] += 1
            modified = clean_text(image.get("modifiedAt"), 80)
            if modified and modified > latest:
                latest = modified
            if not thumbnail_url:
                thumbnail_url = clean_text(image.get("url"), 500)
                if not thumbnail_url and image.get("path"):
                    thumbnail_url = file_url(image.get("path"))
        text = clean_text(" ".join(fragments))
        tokens = Counter(ranking_tokens(text))
        profiles.append(
            {
                "avatar_id": clean_text(avatar.get("id") or avatar.get("name"), 100),
                "label": clean_text(avatar.get("name") or avatar.get("id"), 120),
                "image_count": len(images),
                "dossier_count": int(image_kinds.get("dossier", 0)),
                "model_count": len(avatar.get("models") or []),
                "video_count": len(avatar.get("videos") or []),
                "text_item_count": len(fragments),
                "text_char_count": len(text),
                "updated_at": latest,
                "thumbnail_url": thumbnail_url,
                "_corpus": text.lower(),
                "_tokens": tokens,
            }
        )
    return profiles


def build_skill_quality_projection(skills: list[dict[str, Any]], capabilities: list[dict[str, Any]], nodes: list[dict[str, Any]]) -> dict[str, Any]:
    capabilities_by_skill: dict[str, list[dict[str, Any]]] = defaultdict(list)
    nodes_by_skill: dict[str, set[str]] = defaultdict(set)
    for capability in capabilities:
        connected = {str(item).lower() for item in capability.get("connected_skills", [])}
        capability_family = capability.get("skill_family")
        for skill in skills:
            label = str(skill.get("label", "")).lower()
            if not label:
                continue
            if label in connected or capability_family == skill.get("skill_family"):
                capabilities_by_skill[skill["skill_id"]].append(capability)
                if capability.get("node_id"):
                    nodes_by_skill[skill["skill_id"]].add(str(capability.get("node_id")))
    max_evidence = max([math.log10(int(skill.get("evidence_count") or 0) + 1) for skill in skills] or [1])
    max_sources = max([math.log10(int(skill.get("source_count") or 0) + 1) for skill in skills] or [1])
    max_artifacts = max([math.log10(int(skill.get("artifact_count") or 0) + 1) for skill in skills] or [1])
    max_score = max([math.log10(float(skill.get("score") or 0) + 1) for skill in skills] or [1])
    max_caps = max([math.log10(len(capabilities_by_skill.get(skill.get("skill_id"), [])) + 1) for skill in skills] or [1])
    max_nodes = max([math.log10(len(nodes_by_skill.get(skill.get("skill_id"), set())) + 1) for skill in skills] or [1])
    quality_rows = []
    for skill in skills:
        skill_id = skill.get("skill_id")
        cap_count = len(capabilities_by_skill.get(skill_id, []))
        node_count = len(nodes_by_skill.get(skill_id, set()))
        components = {
            "evidence_power": round(log_norm(skill.get("evidence_count") or 0, max_evidence), 4),
            "source_diversity": round(log_norm(skill.get("source_count") or 0, max_sources), 4),
            "artifact_output": round(log_norm(skill.get("artifact_count") or 0, max_artifacts), 4),
            "raw_score": round(log_norm(skill.get("score") or 0, max_score), 4),
            "capability_reach": round(log_norm(cap_count, max_caps), 4),
            "node_reach": round(log_norm(node_count, max_nodes), 4),
        }
        quality_score = round(
            100
            * (
                components["evidence_power"] * 0.30
                + components["source_diversity"] * 0.13
                + components["artifact_output"] * 0.12
                + components["raw_score"] * 0.12
                + components["capability_reach"] * 0.21
                + components["node_reach"] * 0.12
            ),
            2,
        )
        quality_rows.append(
            {
                "skill_id": skill_id,
                "label": skill.get("label"),
                "skill_family": skill.get("skill_family"),
                "quality_score": quality_score,
                "quality_band": rank_band(quality_score),
                "evidence_count": int(skill.get("evidence_count") or 0),
                "source_count": int(skill.get("source_count") or 0),
                "artifact_count": int(skill.get("artifact_count") or 0),
                "capability_count": cap_count,
                "node_count": node_count,
                "current_rank": skill.get("rank"),
                "current_level": skill.get("level"),
                "summary": skill.get("summary"),
                "related_bodies": skill.get("related_bodies", [])[:5],
                "components": components,
            }
        )
    quality_rows.sort(key=lambda item: (-item["quality_score"], -item["evidence_count"], item.get("label") or ""))
    for index, row in enumerate(quality_rows, start=1):
        row["quality_rank"] = index
        row["relative_percentile"] = round(100 * (1 - ((index - 1) / max(1, len(quality_rows) - 1))), 2)
    quality_by_skill = {row["skill_id"]: row for row in quality_rows}

    avatar_profiles = build_avatar_profiles_for_ranking()
    avatar_experience = []
    for avatar in avatar_profiles:
        corpus = avatar.get("_corpus", "")
        token_counter = avatar.get("_tokens", Counter())
        avatar_max_observed = 0.0
        avatar_pairs = []
        for skill in skills:
            skill_id = skill.get("skill_id")
            quality = quality_by_skill.get(skill_id, {})
            label = clean_text(skill.get("label"), 140)
            family = clean_text(skill.get("skill_family"), 80)
            phrase_parts = [part.strip().lower() for part in re.split(r"[/|:+-]", label) if len(part.strip()) >= 4]
            label_tokens = ranking_tokens(label)
            body_tokens = ranking_tokens(" ".join([family, skill.get("summary") or "", " ".join(skill.get("related_bodies") or [])]))
            important_tokens = [token for token, _ in Counter(label_tokens + body_tokens).most_common(12)]
            phrase_hits = sum(corpus.count(part) for part in phrase_parts)
            token_hits = sum(token_counter.get(token, 0) for token in important_tokens)
            family_hits = sum(token_counter.get(token, 0) for token in ranking_tokens(family))
            observed_uses = round((phrase_hits * 5.0) + token_hits + (family_hits * 1.5), 2)
            if observed_uses <= 0:
                continue
            avatar_max_observed = max(avatar_max_observed, observed_uses)
            avatar_pairs.append(
                {
                    "avatar_id": avatar.get("avatar_id"),
                    "avatar_label": avatar.get("label"),
                    "skill_id": skill_id,
                    "skill_label": label,
                    "skill_family": family,
                    "observed_uses": observed_uses,
                    "quality_score": quality.get("quality_score", 0),
                    "quality_band": quality.get("quality_band", "D"),
                    "matched_terms": important_tokens[:6],
                    "evidence_basis": "avatar dossier OCR, image titles, image kinds, related profile text",
                }
            )
        for pair in avatar_pairs:
            pair["avatar_relative_score"] = round(100 * pair["observed_uses"] / max(1.0, avatar_max_observed), 2)
        avatar_experience.extend(avatar_pairs)
    max_observed = max([pair["observed_uses"] for pair in avatar_experience] or [1.0])
    for pair in avatar_experience:
        pair["global_relative_score"] = round(100 * pair["observed_uses"] / max(1.0, max_observed), 2)
        pair["experience_score"] = round(
            pair["avatar_relative_score"] * 0.58
            + pair["global_relative_score"] * 0.27
            + float(pair.get("quality_score") or 0) * 0.15,
            2,
        )
        pair["experience_band"] = rank_band(pair["experience_score"])
    avatar_experience.sort(
        key=lambda item: (-item["experience_score"], -item["observed_uses"], -float(item.get("quality_score") or 0), item.get("avatar_label") or "")
    )
    for index, row in enumerate(avatar_experience, start=1):
        row["experience_rank"] = index

    public_avatar_profiles = [
        {key: value for key, value in profile.items() if not key.startswith("_")}
        for profile in sorted(avatar_profiles, key=lambda item: (-item.get("image_count", 0), item.get("label") or ""))
    ]
    family_summary = []
    for family in sorted({skill.get("skill_family") for skill in skills if skill.get("skill_family")}):
        family_quality = [row for row in quality_rows if row.get("skill_family") == family]
        family_pairs = [row for row in avatar_experience if row.get("skill_family") == family]
        if not family_quality:
            continue
        family_summary.append(
            {
                "skill_family": family,
                "skill_count": len(family_quality),
                "avg_quality_score": round(sum(row["quality_score"] for row in family_quality) / max(1, len(family_quality)), 2),
                "top_skill": family_quality[0]["label"],
                "top_skill_quality": family_quality[0]["quality_score"],
                "avatar_pair_count": len(family_pairs),
                "top_avatar": family_pairs[0]["avatar_label"] if family_pairs else "",
                "top_experience_score": family_pairs[0]["experience_score"] if family_pairs else 0,
            }
        )
    family_summary.sort(key=lambda item: (-item["avg_quality_score"], -item["top_experience_score"], item["skill_family"]))
    return {
        "protocol_id": "hapa-character-sheet-skill-ranking-protocol",
        "protocol_doc": str(SKILL_RANKING_PROTOCOL),
        "formula_version": "hcs-skill-quality-avatar-experience/2026-06-03",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "summary": {
            "skills_ranked": len(quality_rows),
            "avatars_ranked": len(public_avatar_profiles),
            "avatar_skill_pairs": len(avatar_experience),
            "top_quality_skill": quality_rows[0]["label"] if quality_rows else "",
            "top_avatar_skill_pair": f"{avatar_experience[0]['avatar_label']} / {avatar_experience[0]['skill_label']}" if avatar_experience else "",
            "direct_use_logs_available": False,
            "last_reassessed_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        },
        "skill_quality": quality_rows,
        "family_summary": family_summary,
        "avatar_profiles": public_avatar_profiles,
        "avatar_skill_experience": avatar_experience[:600],
        "top_pairs": avatar_experience[:48],
        "method": {
            "skill_quality": "Relative score from evidence volume, source diversity, artifact output, existing skill score, capability reach, and node reach.",
            "avatar_experience": "First-pass relative score from avatar dossier OCR/profile text matches against skill labels, families, summaries, and related bodies. Replace or augment with direct avatar-use telemetry when available.",
            "refresh_rule": "Recompute on every Character Sheet refresh. Treat scores as projection state, not hand-authored canon.",
        },
    }


TIMELINE_LAYER_MAP = {
    "content_consumed": "knowledge",
    "hapa_turn": "turns",
    "hapa_node": "nodes",
    "node_capability": "capabilities",
}


TIMELINE_LAYER_LABELS = {
    "knowledge": "Knowledge Acquired",
    "turns": "AI Turns",
    "skills": "Skill Creation",
    "nodes": "Node Creation",
    "capabilities": "Capability Creation",
}


TIMELINE_ERAS = [
    {
        "id": "archive-roots",
        "label": "Archive Roots",
        "start": "1515-01-01T00:00:00+00:00",
        "end": "2022-12-31T23:59:59+00:00",
        "body": "Long-range source ancestry: books, viewed media, owned material, and cultural inputs that became the deep library behind the character.",
    },
    {
        "id": "ai-awakening",
        "label": "AI Awakening",
        "start": "2023-01-01T00:00:00+00:00",
        "end": "2025-06-30T23:59:59+00:00",
        "body": "The first AI collaboration era, where prompts and responses started turning source memory into deliberate practice.",
    },
    {
        "id": "turn-forge",
        "label": "Turn Forge",
        "start": "2025-07-01T00:00:00+00:00",
        "end": "2026-04-30T23:59:59+00:00",
        "body": "High-volume practice cadence: AI turns, source intake, cards, and result links begin forming repeatable professional moves.",
    },
    {
        "id": "codex-activation",
        "label": "Codex Activation",
        "start": "2026-05-01T00:00:00+00:00",
        "end": "",
        "body": "The Hapa Character Sheet era: skills, Hapa nodes, node capabilities, media, and proof surfaces consolidate into visible canon.",
    },
]


def timeline_month(value: Any) -> str:
    text = clean_text(value)
    return text[:7] if len(text) >= 7 else ""


def timeline_day(value: Any) -> str:
    text = clean_text(value)
    return text[:10] if len(text) >= 10 else ""


def timeline_year(value: Any) -> str:
    text = clean_text(value)
    return text[:4] if len(text) >= 4 else ""


def timeline_week(value: Any) -> str:
    day = timeline_day(value)
    if not day:
        return ""
    try:
        parsed = datetime.fromisoformat(day)
    except ValueError:
        return timeline_month(value)
    iso = parsed.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def timeline_bucket(value: Any, scale: str) -> str:
    if scale == "day":
        return timeline_day(value)
    if scale == "week":
        return timeline_week(value)
    if scale == "year":
        return timeline_year(value)
    return timeline_month(value)


def timeline_bucket_event_at(bucket: str, scale: str) -> str:
    if not bucket:
        return ""
    if scale == "day":
        return f"{bucket}T00:00:00+00:00"
    if scale == "year":
        return f"{bucket}-01-01T00:00:00+00:00"
    if scale == "week":
        year = bucket[:4]
        return f"{year}-01-01T00:00:00+00:00" if year else ""
    return f"{bucket}-01T00:00:00+00:00"


def timeline_era_id(value: Any) -> str:
    text = clean_text(value)
    if not text:
        return "undated"
    for era in TIMELINE_ERAS:
        start = era.get("start") or ""
        end = era.get("end") or ""
        if text >= start and (not end or text <= end):
            return era["id"]
    return TIMELINE_ERAS[0]["id"]


def timeline_layer_key(activity_layer: Any, event_type: Any = "") -> str:
    layer = clean_text(activity_layer)
    if layer in TIMELINE_LAYER_MAP:
        return TIMELINE_LAYER_MAP[layer]
    event = clean_text(event_type)
    if event == "content_viewed":
        return "knowledge"
    if event.startswith("ai_turn_"):
        return "turns"
    if event == "hapa_node_created":
        return "nodes"
    if event == "node_capability_added":
        return "capabilities"
    return layer or "knowledge"


def timeline_event_beat(row: dict[str, Any], layer: str | None = None) -> dict[str, Any]:
    event_type = clean_text(row.get("event_type"), 80)
    event_at = clean_text(row.get("event_at"), 80)
    key = layer or timeline_layer_key(row.get("activity_layer"), event_type)
    title = clean_text(row.get("metric_subject_label") or row.get("title") or row.get("objective") or row.get("target_id") or row.get("event_id"), 150)
    actor = clean_text(row.get("actor_alias") or row.get("actor_name"), 90)
    source = clean_text(row.get("source_system"), 80)
    description = clean_text(row.get("description") or row.get("evidence_text") or row.get("objective") or "", 360)
    if not description:
        description = f"{TIMELINE_LAYER_LABELS.get(key, key)} event from {source or 'Second Brain timeline'}."
    return {
        "id": clean_text(row.get("event_id") or row.get("metric_id") or f"{key}:{row.get('target_id')}", 130),
        "layer": key,
        "event_type": event_type,
        "event_action": clean_text(row.get("event_action"), 80),
        "date": event_at,
        "day": timeline_day(event_at),
        "month": timeline_month(event_at),
        "era_id": timeline_era_id(event_at),
        "title": title,
        "body": description,
        "actor": actor,
        "related_actor": clean_text(row.get("related_actor_alias") or row.get("related_actor_name"), 90),
        "source_system": source,
        "target_type": clean_text(row.get("target_type") or row.get("metric_subject_type"), 80),
        "target_id": clean_text(row.get("target_id") or row.get("metric_subject_id"), 130),
        "confidence": round(float(row.get("confidence") or 0), 2),
        "date_precision": clean_text(row.get("date_precision"), 70),
        "metrics": {
            "input_words": int(row.get("input_words") or 0),
            "output_words": int(row.get("output_words") or 0),
            "content_words": int(row.get("content_words") or 0),
            "content_hours": round(float(row.get("content_hours") or 0), 2),
            "code_lines": int(row.get("code_lines") or 0),
            "capability_count": int(row.get("capability_count") or 0),
            "event_count": int(row.get("event_count") or 1),
        },
    }


def build_timeline_projection(conn: sqlite3.Connection, skills: list[dict[str, Any]]) -> dict[str, Any]:
    first_latest = rows(
        conn,
        """
        SELECT COUNT(*) AS timeline_events, MIN(event_at) AS first_event_at, MAX(event_at) AS latest_event_at
        FROM information_timeline_events
        """
    )
    range_row = first_latest[0] if first_latest else {}
    event_counts = rows(
        conn,
        """
        SELECT event_type, COUNT(*) AS count, MIN(event_at) AS first_event_at, MAX(event_at) AS latest_event_at
        FROM information_timeline_events
        GROUP BY event_type
        ORDER BY count DESC
        """
    )
    event_counts = [
        {
            "event_type": clean_text(row.get("event_type"), 80),
            "count": int(row.get("count") or 0),
            "first_event_at": clean_text(row.get("first_event_at"), 80),
            "latest_event_at": clean_text(row.get("latest_event_at"), 80),
        }
        for row in event_counts
    ]
    activity_counts = rows(
        conn,
        """
        SELECT activity_layer, activity_vector, COUNT(*) AS rows, SUM(event_count) AS events,
               SUM(input_words) AS input_words, SUM(output_words) AS output_words,
               SUM(content_words) AS content_words, ROUND(SUM(content_hours), 3) AS content_hours,
               SUM(code_lines) AS code_lines, SUM(capability_count) AS capability_count,
               MIN(event_at) AS first_event_at, MAX(event_at) AS latest_event_at
        FROM timeline_activity_metrics
        GROUP BY activity_layer, activity_vector
        ORDER BY events DESC
        """
    )
    layer_totals: dict[str, dict[str, Any]] = defaultdict(lambda: {"key": "", "label": "", "count": 0, "metric_rows": 0, "first_event_at": "", "latest_event_at": "", "vectors": []})
    for row in activity_counts:
        key = timeline_layer_key(row.get("activity_layer"))
        entry = layer_totals[key]
        entry["key"] = key
        entry["label"] = TIMELINE_LAYER_LABELS.get(key, key.replace("_", " ").title())
        entry["count"] += int(row.get("events") or 0)
        entry["metric_rows"] += int(row.get("rows") or 0)
        first_at = clean_text(row.get("first_event_at"), 80)
        latest_at = clean_text(row.get("latest_event_at"), 80)
        if first_at and (not entry["first_event_at"] or first_at < entry["first_event_at"]):
            entry["first_event_at"] = first_at
        if latest_at and latest_at > entry["latest_event_at"]:
            entry["latest_event_at"] = latest_at
        entry["vectors"].append(
            {
                "activity_vector": clean_text(row.get("activity_vector"), 80),
                "count": int(row.get("events") or 0),
                "metric_rows": int(row.get("rows") or 0),
            }
        )
    skill_buckets_by_scale: dict[str, Counter[str]] = {
        scale: Counter(timeline_bucket(skill.get("created_at") or skill.get("updated_at"), scale) for skill in skills)
        for scale in ("day", "week", "month", "year")
    }
    for bucket_counts in skill_buckets_by_scale.values():
        bucket_counts.pop("", None)
    skill_months = skill_buckets_by_scale["month"]
    skill_total = sum(skill_months.values())
    if skill_total:
        skill_dates = [skill.get("created_at") or skill.get("updated_at") for skill in skills if skill.get("created_at") or skill.get("updated_at")]
        layer_totals["skills"] = {
            "key": "skills",
            "label": TIMELINE_LAYER_LABELS["skills"],
            "count": skill_total,
            "metric_rows": skill_total,
            "first_event_at": min(skill_dates),
            "latest_event_at": max(skill_dates),
            "vectors": [{"activity_vector": "skill_created", "count": skill_total, "metric_rows": skill_total}],
        }
    preferred_layers = ["knowledge", "turns", "skills", "nodes", "capabilities"]
    layers = [layer_totals[key] for key in preferred_layers if key in layer_totals]

    def build_series_for_scale(scale: str, bucket_column: str) -> list[dict[str, Any]]:
        series_rows = rows(
            conn,
            f"""
            SELECT {bucket_column} AS bucket, activity_layer,
                   SUM(event_count) AS events,
                   SUM(input_words + output_words + content_words) AS words,
                   ROUND(SUM(content_hours), 3) AS content_hours,
                   SUM(code_lines) AS code_lines,
                   SUM(capability_count) AS capability_count
            FROM timeline_activity_metrics
            WHERE {bucket_column} IS NOT NULL
            GROUP BY {bucket_column}, activity_layer
            ORDER BY {bucket_column} ASC
            """
        )
        scale_series = [
            {
                "bucket": clean_text(row.get("bucket"), 24),
                "scale": scale,
                "layer": timeline_layer_key(row.get("activity_layer")),
                "events": int(row.get("events") or 0),
                "words": int(row.get("words") or 0),
                "content_hours": round(float(row.get("content_hours") or 0), 2),
                "code_lines": int(row.get("code_lines") or 0),
                "capability_count": int(row.get("capability_count") or 0),
                "era_id": timeline_era_id(timeline_bucket_event_at(clean_text(row.get("bucket")), scale)),
            }
            for row in series_rows
        ]
        skill_buckets = skill_buckets_by_scale[scale]
        for bucket, count in sorted(skill_buckets.items()):
            scale_series.append(
                {
                    "bucket": bucket,
                    "scale": scale,
                    "layer": "skills",
                    "events": int(count),
                    "words": sum(
                        int(skill.get("evidence_count") or 0)
                        for skill in skills
                        if timeline_bucket(skill.get("created_at") or skill.get("updated_at"), scale) == bucket
                    ),
                    "content_hours": 0,
                    "code_lines": 0,
                    "capability_count": 0,
                    "era_id": timeline_era_id(timeline_bucket_event_at(bucket, scale)),
                }
            )
        return sorted(scale_series, key=lambda item: (item["bucket"], item["layer"]))

    series_by_scale = {
        "day": build_series_for_scale("day", "time_bucket_day"),
        "week": build_series_for_scale("week", "time_bucket_week"),
        "month": build_series_for_scale("month", "time_bucket_month"),
        "year": build_series_for_scale("year", "time_bucket_year"),
    }
    series = series_by_scale["month"]

    def bucket_summary(scale: str) -> dict[str, Any]:
        totals: dict[str, int] = defaultdict(int)
        words: dict[str, int] = defaultdict(int)
        code_lines: dict[str, int] = defaultdict(int)
        caps: dict[str, int] = defaultdict(int)
        for item in series_by_scale.get(scale, []):
            bucket = item.get("bucket") or ""
            if not bucket:
                continue
            totals[bucket] += int(item.get("events") or 0)
            words[bucket] += int(item.get("words") or 0)
            code_lines[bucket] += int(item.get("code_lines") or 0)
            caps[bucket] += int(item.get("capability_count") or 0)
        if not totals:
            return {"bucket_count": 0, "first_bucket": "", "latest_bucket": "", "latest_bucket_events": 0, "peak_bucket": "", "peak_bucket_events": 0}
        ordered = sorted(totals)
        peak_bucket = max(totals, key=lambda bucket: (totals[bucket], bucket))
        latest_bucket = ordered[-1]
        return {
            "bucket_count": len(totals),
            "first_bucket": ordered[0],
            "latest_bucket": latest_bucket,
            "latest_bucket_events": totals[latest_bucket],
            "peak_bucket": peak_bucket,
            "peak_bucket_events": totals[peak_bucket],
            "peak_bucket_words": words[peak_bucket],
            "peak_bucket_code_lines": code_lines[peak_bucket],
            "peak_bucket_capabilities": caps[peak_bucket],
        }

    daily_bucket_summary = bucket_summary("day")

    beat_queries = [
        (
            "knowledge",
            """
            SELECT *
            FROM timeline_event_overview
            WHERE event_type='content_viewed'
            ORDER BY event_at DESC, confidence DESC
            LIMIT 70
            """,
        ),
        (
            "turns",
            """
            SELECT *
            FROM timeline_event_overview
            WHERE event_type IN ('ai_turn_prompted','ai_turn_responded')
            ORDER BY event_at DESC, confidence DESC
            LIMIT 90
            """,
        ),
        (
            "nodes",
            """
            SELECT *
            FROM timeline_event_overview
            WHERE event_type='hapa_node_created'
            ORDER BY event_at DESC, confidence DESC
            LIMIT 80
            """,
        ),
        (
            "capabilities",
            """
            SELECT *
            FROM timeline_event_overview
            WHERE event_type='node_capability_added'
            ORDER BY event_at DESC, confidence DESC
            LIMIT 90
            """,
        ),
    ]
    beats: list[dict[str, Any]] = []
    for layer, sql in beat_queries:
        beats.extend(timeline_event_beat(row, layer) for row in rows(conn, sql))
    for skill in sorted(skills, key=lambda item: (int(item.get("evidence_count") or 0), item.get("label") or ""), reverse=True)[:60]:
        date = clean_text(skill.get("created_at") or skill.get("updated_at"), 80)
        beats.append(
            {
                "id": clean_text(f"skill_created:{skill.get('skill_id')}", 150),
                "layer": "skills",
                "event_type": "skill_created",
                "event_action": "skill_inventory_consolidated",
                "date": date,
                "day": timeline_day(date),
                "month": timeline_month(date),
                "era_id": timeline_era_id(date),
                "title": clean_text(skill.get("label"), 150),
                "body": clean_text(skill.get("summary") or f"{skill.get('label')} consolidated into the Character Sheet skill inventory.", 360),
                "actor": "Second Brain",
                "related_actor": "Calder/CJ",
                "source_system": "skill_inventory",
                "target_type": "skill",
                "target_id": clean_text(skill.get("skill_id"), 130),
                "confidence": 0.86,
                "date_precision": "projection_created_at",
                "metrics": {
                    "input_words": 0,
                    "output_words": 0,
                    "content_words": int(skill.get("evidence_count") or 0),
                    "content_hours": 0,
                    "code_lines": 0,
                    "capability_count": 0,
                    "event_count": 1,
                },
            }
        )
    beats = sorted(beats, key=lambda item: (item.get("date") or "", item.get("confidence") or 0), reverse=True)
    seen_beats = set()
    unique_beats = []
    for beat in beats:
        if beat["id"] in seen_beats:
            continue
        seen_beats.add(beat["id"])
        unique_beats.append(beat)
        if len(unique_beats) >= 240:
            break

    source_mix = rows(
        conn,
        """
        SELECT source_system, event_type, COUNT(*) AS count,
               MIN(event_at) AS first_event_at, MAX(event_at) AS latest_event_at
        FROM information_timeline_events
        GROUP BY source_system, event_type
        ORDER BY count DESC
        LIMIT 80
        """
    )
    source_mix = [
        {
            "source_system": clean_text(row.get("source_system"), 80),
            "event_type": clean_text(row.get("event_type"), 80),
            "count": int(row.get("count") or 0),
            "first_event_at": clean_text(row.get("first_event_at"), 80),
            "latest_event_at": clean_text(row.get("latest_event_at"), 80),
        }
        for row in source_mix
    ]

    def era_counts(era: dict[str, str]) -> dict[str, int]:
        counts = {key: 0 for key in preferred_layers}
        for item in series:
            if item.get("era_id") == era["id"]:
                counts[item["layer"]] = counts.get(item["layer"], 0) + int(item.get("events") or 0)
        return counts

    eras = []
    for era in TIMELINE_ERAS:
        counts = era_counts(era)
        eras.append(
            {
                "id": era["id"],
                "label": era["label"],
                "start": era["start"],
                "end": era["end"],
                "body": era["body"],
                "counts": counts,
                "total": sum(counts.values()),
            }
        )

    counts_by_event = {item["event_type"]: item["count"] for item in event_counts}
    return {
        "summary": {
            "timeline_events": int(range_row.get("timeline_events") or 0),
            "activity_metrics": count_table(conn, "timeline_activity_metrics"),
            "first_event_at": clean_text(range_row.get("first_event_at"), 80),
            "latest_event_at": clean_text(range_row.get("latest_event_at"), 80),
            "knowledge_events": counts_by_event.get("content_viewed", 0),
            "turn_events": counts_by_event.get("ai_turn_prompted", 0) + counts_by_event.get("ai_turn_responded", 0),
            "skill_events": len(skills),
            "node_events": counts_by_event.get("hapa_node_created", 0),
            "capability_events": counts_by_event.get("node_capability_added", 0),
            "daily_buckets": daily_bucket_summary.get("bucket_count", 0),
            "weekly_buckets": bucket_summary("week").get("bucket_count", 0),
            "monthly_buckets": bucket_summary("month").get("bucket_count", 0),
            "yearly_buckets": bucket_summary("year").get("bucket_count", 0),
            "latest_day": daily_bucket_summary.get("latest_bucket", ""),
            "latest_day_events": daily_bucket_summary.get("latest_bucket_events", 0),
            "peak_day": daily_bucket_summary.get("peak_bucket", ""),
            "peak_day_events": daily_bucket_summary.get("peak_bucket_events", 0),
            "canon_copy": "Historical canon built from Second Brain timeline events, activity metrics, and synthesized skill consolidation dates.",
        },
        "event_counts": event_counts,
        "layers": layers,
        "eras": eras,
        "series": series,
        "series_by_scale": series_by_scale,
        "daily_summary": {
            "active_days": daily_bucket_summary.get("bucket_count", 0),
            "first_day": daily_bucket_summary.get("first_bucket", ""),
            "latest_day": daily_bucket_summary.get("latest_bucket", ""),
            "latest_day_events": daily_bucket_summary.get("latest_bucket_events", 0),
            "peak_day": daily_bucket_summary.get("peak_bucket", ""),
            "peak_day_events": daily_bucket_summary.get("peak_bucket_events", 0),
            "peak_day_words": daily_bucket_summary.get("peak_bucket_words", 0),
            "peak_day_code_lines": daily_bucket_summary.get("peak_bucket_code_lines", 0),
            "peak_day_capabilities": daily_bucket_summary.get("peak_bucket_capabilities", 0),
            "protocol": "Daily view groups Second Brain time_bucket_day rows plus synthesized skill unlock days. Refresh Character Sheet after refresh-timeline or refresh-timeline-activity so daily canon stays current.",
        },
        "beats": unique_beats,
        "source_mix": source_mix,
        "projection_policy": "Character Sheet Timeline compresses the Second Brain timeline into eras, layers, series, and representative beats. Raw event ledgers remain in Second Brain.",
    }


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    skill_rows = rows(
        conn,
        """
        SELECT skill_id, label, skill_family, score, source_count, artifact_count,
               evidence_count, summary, related_bodies_json, created_at, updated_at
        FROM skill_inventory
        ORDER BY evidence_count DESC, score DESC, label ASC
        """,
    )
    skills = []
    for row in skill_rows:
        rank, level = skill_rank(row.get("evidence_count"), row.get("source_count"), row.get("artifact_count"), row.get("score"))
        skills.append(
            {
                "skill_id": clean_text(row.get("skill_id")),
                "label": clean_text(row.get("label"), 130),
                "skill_family": clean_text(row.get("skill_family"), 80),
                "score": round(float(row.get("score") or 0), 2),
                "source_count": int(row.get("source_count") or 0),
                "artifact_count": int(row.get("artifact_count") or 0),
                "evidence_count": int(row.get("evidence_count") or 0),
                "summary": clean_text(row.get("summary"), 420),
                "related_bodies": json_labels(row.get("related_bodies_json"), 7),
                "rank": rank,
                "level": level,
                "created_at": clean_text(row.get("created_at")),
                "updated_at": clean_text(row.get("updated_at")),
            }
        )

    node_rows = rows(
        conn,
        """
        SELECT node_id, label, node_type, source_path, description, score,
               topic_count, body_count, card_count, created_at, updated_at
        FROM hapa_nodes
        ORDER BY score DESC, label ASC
        """,
    )
    nodes = [
        {
            "node_id": clean_text(row.get("node_id")),
            "label": clean_text(row.get("label"), 130),
            "node_type": clean_text(row.get("node_type"), 80),
            "source_path": clean_text(row.get("source_path"), 260),
            "description": clean_text(row.get("description"), 520),
            "score": round(float(row.get("score") or 0), 2),
            "topic_count": int(row.get("topic_count") or 0),
            "body_count": int(row.get("body_count") or 0),
            "card_count": int(row.get("card_count") or 0),
            "created_at": clean_text(row.get("created_at")),
            "updated_at": clean_text(row.get("updated_at")),
        }
        for row in node_rows
    ]

    cap_rows = rows(
        conn,
        """
        SELECT node_skill_id, node_id, mode, label, skill_family, description,
               practice_steps_json, success_signals_json, connected_general_skills_json,
               score, general_skill_count, body_count, topic_count, card_count,
               node_label, node_type, source_path, link_count, best_link_score,
               created_at, updated_at
        FROM hapa_node_skill_overview
        ORDER BY score DESC, label ASC
        """,
    )
    capabilities = [
        {
            "node_skill_id": clean_text(row.get("node_skill_id")),
            "node_id": clean_text(row.get("node_id")),
            "mode": clean_text(row.get("mode"), 40),
            "label": clean_text(row.get("label"), 150),
            "skill_family": clean_text(row.get("skill_family"), 80),
            "description": clean_text(row.get("description"), 520),
            "practice_steps": json_labels(row.get("practice_steps_json"), 5),
            "success_signals": json_labels(row.get("success_signals_json"), 5),
            "connected_skills": json_labels(row.get("connected_general_skills_json"), 7),
            "score": round(float(row.get("score") or 0), 2),
            "general_skill_count": int(row.get("general_skill_count") or 0),
            "body_count": int(row.get("body_count") or 0),
            "topic_count": int(row.get("topic_count") or 0),
            "card_count": int(row.get("card_count") or 0),
            "node_label": clean_text(row.get("node_label"), 130),
            "node_type": clean_text(row.get("node_type"), 70),
            "source_path": clean_text(row.get("source_path"), 260),
            "link_count": int(row.get("link_count") or 0),
            "best_link_score": round(float(row.get("best_link_score") or 0), 2),
            "created_at": clean_text(row.get("created_at")),
            "updated_at": clean_text(row.get("updated_at")),
        }
        for row in cap_rows
    ]

    topic_rows = rows(
        conn,
        """
        SELECT topic_id, label, topic_type, definition, scope_note,
               evidence_count, item_count, skill_count, source_count, score
        FROM topic_profile_overview
        ORDER BY evidence_count DESC, score DESC, label ASC
        """
    )
    topics = [
        {
            "topic_id": clean_text(row.get("topic_id")),
            "label": clean_text(row.get("label"), 130),
            "topic_type": clean_text(row.get("topic_type"), 70),
            "definition": clean_text(row.get("definition"), 360),
            "scope_note": clean_text(row.get("scope_note"), 360),
            "evidence_count": int(row.get("evidence_count") or 0),
            "item_count": int(row.get("item_count") or 0),
            "skill_count": int(row.get("skill_count") or 0),
            "source_count": int(row.get("source_count") or 0),
            "score": round(float(row.get("score") or 0), 2),
        }
        for row in topic_rows
    ]

    turn_rows = rows(
        conn,
        """
        SELECT turn_id, thread_id, thread_title, platform, model_slug, turn_index,
               turn_started_at, objective, turn_type, hapa_relevance_score,
               user_excerpt, model_response_summary, learning_link_count,
               result_link_count, best_learning_score, best_result_score
        FROM turn_result_lineage_overview
        ORDER BY hapa_relevance_score DESC, best_result_score DESC, turn_started_at DESC
        """
    )
    turns = [
        {
            "turn_id": clean_text(row.get("turn_id")),
            "thread_id": clean_text(row.get("thread_id")),
            "thread_title": clean_text(row.get("thread_title"), 180),
            "platform": clean_text(row.get("platform"), 80),
            "model_slug": clean_text(row.get("model_slug"), 80),
            "turn_index": int(row.get("turn_index") or 0),
            "turn_started_at": clean_text(row.get("turn_started_at"), 80),
            "objective": clean_text(row.get("objective"), 240),
            "turn_type": clean_text(row.get("turn_type"), 80),
            "hapa_relevance_score": round(float(row.get("hapa_relevance_score") or 0), 2),
            "user_excerpt": clean_text(row.get("user_excerpt"), 360),
            "model_response_summary": clean_text(row.get("model_response_summary"), 360),
            "learning_link_count": int(row.get("learning_link_count") or 0),
            "result_link_count": int(row.get("result_link_count") or 0),
            "best_learning_score": round(float(row.get("best_learning_score") or 0), 2),
            "best_result_score": round(float(row.get("best_result_score") or 0), 2),
        }
        for row in turn_rows
    ]

    learning_rows = rows(
        conn,
        """
        SELECT link_id, turn_id, source_type, source_title, source_system, medium,
               relation_type, score, skill_label, skill_family, body_label,
               article_title, evidence_text, platform, turn_type, thread_title
        FROM turn_learning_link_overview
        ORDER BY score DESC, created_at DESC
        LIMIT 1800
        """
    )
    learning_links = [
        {
            "link_id": clean_text(row.get("link_id")),
            "turn_id": clean_text(row.get("turn_id")),
            "source_type": clean_text(row.get("source_type"), 70),
            "source_title": clean_text(row.get("source_title"), 180),
            "source_system": clean_text(row.get("source_system"), 80),
            "medium": clean_text(row.get("medium"), 70),
            "relation_type": clean_text(row.get("relation_type"), 80),
            "score": round(float(row.get("score") or 0), 2),
            "skill_label": clean_text(row.get("skill_label"), 130),
            "skill_family": clean_text(row.get("skill_family"), 80),
            "body_label": clean_text(row.get("body_label"), 130),
            "article_title": clean_text(row.get("article_title"), 130),
            "evidence_text": clean_text(row.get("evidence_text"), 280),
            "platform": clean_text(row.get("platform"), 70),
            "turn_type": clean_text(row.get("turn_type"), 70),
            "thread_title": clean_text(row.get("thread_title"), 160),
        }
        for row in learning_rows
    ]

    source_systems = rows(
        conn,
        """
        SELECT source_system, COUNT(*) AS items, SUM(exposure_count) AS exposures,
               SUM(owned) AS owned, GROUP_CONCAT(DISTINCT medium) AS mediums
        FROM content_items
        GROUP BY source_system
        ORDER BY items DESC
        """
    )
    source_systems = [
        {
            "source_system": clean_text(row.get("source_system"), 90),
            "items": int(row.get("items") or 0),
            "exposures": int(row.get("exposures") or 0),
            "owned": int(row.get("owned") or 0),
            "mediums": clean_text(row.get("mediums"), 160),
        }
        for row in source_systems
    ]
    mediums = rows(
        conn,
        """
        SELECT medium, COUNT(*) AS items, SUM(exposure_count) AS exposures
        FROM content_items
        GROUP BY medium
        ORDER BY items DESC
        """
    )
    mediums = [
        {
            "medium": clean_text(row.get("medium"), 90),
            "items": int(row.get("items") or 0),
            "exposures": int(row.get("exposures") or 0),
        }
        for row in mediums
    ]

    media_rows = rows(
        conn,
        """
        SELECT job_id, target_type, target_id, asset_role, media_type, provider,
               source_model, status, priority, prompt_text, direction_prompt,
               output_url, output_local_path, image_url, local_path, thumbnail_url,
               visual_generation_status, visual_label, target_label, node_label,
               node_skill_mode, node_skill_family, turn_skill_family, updated_at
        FROM media_generation_queue_overview
        ORDER BY updated_at DESC, priority ASC
        """
    )
    media = []
    for row in media_rows:
        preview = file_preview_path(row.get("output_local_path") or "") or file_preview_path(row.get("local_path") or "") or file_preview_path(row.get("thumbnail_url") or "")
        if not preview and row.get("image_url"):
            preview = clean_text(row.get("image_url"), 300)
        media.append(
            {
                "job_id": clean_text(row.get("job_id")),
                "target_type": clean_text(row.get("target_type"), 70),
                "target_id": clean_text(row.get("target_id"), 90),
                "asset_role": clean_text(row.get("asset_role"), 80),
                "media_type": clean_text(row.get("media_type"), 70),
                "provider": clean_text(row.get("provider"), 70),
                "source_model": clean_text(row.get("source_model"), 90),
                "status": clean_text(row.get("status"), 70),
                "priority": int(row.get("priority") or 0),
                "prompt_text": clean_text(row.get("prompt_text"), 320),
                "direction_prompt": clean_text(row.get("direction_prompt"), 320),
                "output_local_path": clean_text(row.get("output_local_path"), 300),
                "preview_path": preview,
                "visual_generation_status": clean_text(row.get("visual_generation_status"), 70),
                "visual_label": clean_text(row.get("visual_label"), 130),
                "target_label": clean_text(row.get("target_label"), 130),
                "node_label": clean_text(row.get("node_label"), 130),
                "node_skill_mode": clean_text(row.get("node_skill_mode"), 70),
                "node_skill_family": clean_text(row.get("node_skill_family"), 80),
                "turn_skill_family": clean_text(row.get("turn_skill_family"), 80),
                "score": max(1, 100 - int(row.get("priority") or 0)),
                "updated_at": clean_text(row.get("updated_at")),
            }
        )

    agent_rows = rows(
        conn,
        """
        SELECT agent_id, label, agent_kind, status, provider, model_profile,
               description, role_summary, score, local_skill_count,
               master_skill_count, harness_count, updated_at
        FROM agent_profiles
        ORDER BY score DESC, label ASC
        """
    )
    agents = [
        {
            "agent_id": clean_text(row.get("agent_id")),
            "label": clean_text(row.get("label"), 120),
            "agent_kind": clean_text(row.get("agent_kind"), 70),
            "status": clean_text(row.get("status"), 50),
            "provider": clean_text(row.get("provider"), 70),
            "model_profile": clean_text(row.get("model_profile"), 90),
            "description": clean_text(row.get("description"), 420),
            "role_summary": clean_text(row.get("role_summary"), 360),
            "score": round(float(row.get("score") or 0), 2),
            "local_skill_count": int(row.get("local_skill_count") or 0),
            "master_skill_count": int(row.get("master_skill_count") or 0),
            "harness_count": int(row.get("harness_count") or 0),
            "updated_at": clean_text(row.get("updated_at")),
        }
        for row in agent_rows
    ]
    harnesses = []
    if count_table(conn, "harness_profiles"):
        harness_rows = rows(
            conn,
            """
            SELECT harness_id, label, harness_type, status, vendor,
                   description, score, updated_at
            FROM harness_profile_overview
            ORDER BY score DESC, label ASC
            """
        )
        harnesses = [
            {
                "harness_id": clean_text(row.get("harness_id")),
                "label": clean_text(row.get("label"), 120),
                "harness_kind": clean_text(row.get("harness_type"), 70),
                "status": clean_text(row.get("status"), 50),
                "provider": clean_text(row.get("vendor"), 70),
                "model_profile": "",
                "description": clean_text(row.get("description"), 420),
                "role_summary": clean_text(row.get("description"), 360),
                "score": round(float(row.get("score") or 0), 2),
                "updated_at": clean_text(row.get("updated_at")),
            }
            for row in harness_rows
        ]

    protocol_rows = rows(
        conn,
        """
        SELECT slug, title, article_type, summary, updated_at
        FROM wiki_articles
        WHERE lower(slug) LIKE '%protocol%'
           OR lower(title) LIKE '%protocol%'
           OR lower(summary) LIKE '%protocol%'
           OR lower(title) LIKE '%registry%'
           OR lower(title) LIKE '%capability%'
        ORDER BY updated_at DESC, title ASC
        """
    )
    protocols = [
        {
            "slug": clean_text(row.get("slug"), 120),
            "title": clean_text(row.get("title"), 160),
            "article_type": clean_text(row.get("article_type"), 70),
            "summary": clean_text(row.get("summary"), 420),
            "updated_at": clean_text(row.get("updated_at"), 80),
        }
        for row in protocol_rows
    ]

    family_map: dict[str, dict[str, Any]] = defaultdict(lambda: {"label": "", "skill_count": 0, "evidence_count": 0, "source_count": 0, "artifact_count": 0, "top_skill": "", "rank": "D"})
    for skill in skills:
        entry = family_map[skill["skill_family"]]
        entry["label"] = skill["skill_family"]
        entry["skill_count"] += 1
        entry["evidence_count"] += skill["evidence_count"]
        entry["source_count"] += skill["source_count"]
        entry["artifact_count"] += skill["artifact_count"]
        if not entry["top_skill"] or skill["evidence_count"] > entry.get("top_evidence", -1):
            entry["top_skill"] = skill["label"]
            entry["top_evidence"] = skill["evidence_count"]
            entry["rank"] = skill["rank"]
    skill_families = sorted((dict(value) for value in family_map.values()), key=lambda item: item["evidence_count"], reverse=True)
    for item in skill_families:
        item.pop("top_evidence", None)

    stat_map: dict[str, dict[str, Any]] = defaultdict(lambda: {"label": "", "evidence": 0, "sources": 0, "skills": 0, "top": []})
    for skill in skills:
        bucket = stat_bucket(skill)
        entry = stat_map[bucket]
        entry["label"] = bucket
        entry["evidence"] += skill["evidence_count"]
        entry["sources"] += skill["source_count"]
        entry["skills"] += 1
        entry["top"].append((skill["evidence_count"], skill["label"]))
    stats = []
    for label in STAT_RULES:
        entry = stat_map[label]
        evidence = entry["evidence"]
        value = min(99, round(38 + math.log10(evidence + 1) * 9 + entry["skills"] * 1.7))
        top_skills = [name for _, name in sorted(entry["top"], reverse=True)[:4]]
        stats.append(
            {
                "label": label,
                "value": value,
                "evidence": evidence,
                "source_count": entry["sources"],
                "skill_count": entry["skills"],
                "top_skills": top_skills,
                "detail": f"{entry['skills']} skills / {evidence:,} evidence links",
            }
        )

    node_type_counter: dict[str, dict[str, Any]] = defaultdict(lambda: {"label": "", "count": 0, "topic_count": 0, "body_count": 0, "card_count": 0})
    for node in nodes:
        entry = node_type_counter[node["node_type"]]
        entry["label"] = node["node_type"]
        entry["count"] += 1
        entry["topic_count"] += node["topic_count"]
        entry["body_count"] += node["body_count"]
        entry["card_count"] += node["card_count"]
    node_type_summary = sorted((dict(item) for item in node_type_counter.values()), key=lambda item: item["count"], reverse=True)

    board = summarize_board()
    refresh = summarize_refresh_log()
    docs = [doc_summary(path) for path in DOC_PATHS]
    image_sources = build_character_image_sources(media)
    character_models = build_character_models()
    profile_background_videos = build_profile_background_videos()
    skill_video_loops = build_skill_video_loops()
    timeline = build_timeline_projection(conn, skills)
    skill_quality = build_skill_quality_projection(skills, capabilities, nodes)
    character_profile = summarize_character_profile()

    summary_counts = {
        "items": count_table(conn, "content_items"),
        "exposures": count_table(conn, "exposures") or count_table(conn, "item_exposures"),
        "entities": count_table(conn, "entities"),
        "topics": count_table(conn, "topic_profiles") or count_table(conn, "topics"),
        "edges": count_table(conn, "graph_edges") or count_table(conn, "knowledge_edges") or count_table(conn, "edges"),
        "chunks": count_table(conn, "content_chunks"),
        "wiki_articles": count_table(conn, "wiki_articles"),
        "skills": len(skills),
        "skill_evidence": count_table(conn, "skill_evidence"),
        "skill_topic_links": count_table(conn, "skill_topic_links"),
        "nodes": len(nodes),
        "node_skills": len(capabilities),
        "capability_bridges": count_table(conn, "capability_bridge_connections") or count_table(conn, "capability_bridges"),
        "turns": len(turns),
        "turn_learning_links": count_table(conn, "turn_learning_links"),
        "turn_result_links": count_table(conn, "turn_result_links"),
        "turn_wisdom_cards": count_table(conn, "turn_wisdom_cards"),
        "agents": len(agents),
        "harnesses": len(harnesses),
        "media_jobs": len(media),
        "image_sources": len(image_sources["items"]),
        "character_models": len(character_models["items"]),
        "profile_background_videos": len(profile_background_videos["items"]),
        "skill_video_loops": len(skill_video_loops["items"]),
        "board_tasks": len(board["tasks"]),
        "refresh_events": refresh["event_count"],
        "timeline_events": timeline["summary"]["timeline_events"],
        "timeline_activity_metrics": timeline["summary"]["activity_metrics"],
        "timeline_daily_buckets": timeline["summary"].get("daily_buckets", 0),
        "skill_quality_ranked": skill_quality["summary"]["skills_ranked"],
        "avatar_skill_pairs": skill_quality["summary"]["avatar_skill_pairs"],
        "avatars_ranked": skill_quality["summary"]["avatars_ranked"],
    }
    summary_counts["total_records"] = sum(
        summary_counts.get(key, 0)
        for key in ("items", "exposures", "entities", "topics", "edges", "chunks", "skill_evidence", "turn_learning_links", "media_jobs")
    )
    summary_counts["generated_label"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    summary_counts["last_refresh_at"] = refresh["last_success"].get("ts") or ""

    contracts = [
        {
            "title": "Web UI",
            "kind": "surface",
            "summary": "Dense local-first app shell with layered filters, public resume mode, game stats, skill codex, lineage, media, character model, skill loop previews, and board state.",
            "files": ["hapa-character-sheet-prototype.html", "hapa-character-sheet-data.json"],
        },
        {
            "title": "API Contract",
            "kind": "OpenAPI",
            "summary": "Read-only projection endpoints for profile, stats, skills, nodes, capabilities, lineage, media, agents, protocols, exports, and refresh.",
            "files": ["hapa-character-sheet.openapi.json"],
        },
        {
            "title": "CLI Contract",
            "kind": "manifest",
            "summary": "Standard Hapa commands for build, serve, export, inspect, refresh, and board registration over the projection data.",
            "files": ["hapa-character-sheet.manifest.json"],
        },
        {
            "title": "Protocol Flow",
            "kind": "flow",
            "summary": "Source truth, projection, privacy tiers, export bundles, Kanban events, and feedback loops wired as a Hapa protocol flow.",
            "files": ["hapa-character-sheet.protocol-flow.json"],
        },
        {
            "title": "Refresh Protocol",
            "kind": "protocol",
            "summary": "Runbook and append-only ledger for rebuilding Character Sheet data from the Hapa Second Brain and recording the last successful refresh.",
            "files": ["HAPA_CHARACTER_SHEET_REFRESH_PROTOCOL.md", "hapa-character-sheet.refresh-log.ndjson"],
        },
        {
            "title": "Skill Ranking Protocol",
            "kind": "protocol",
            "summary": "Continuous enrichment protocol for ranking skill quality and avatar experience with each skill as new skills, avatars, and use evidence arrive.",
            "files": ["HAPA_CHARACTER_SHEET_SKILL_RANKING_PROTOCOL.md", "hapa-character-sheet.skill-ranking-flow.json"],
        },
        {
            "title": "Daily Timeline Protocol",
            "kind": "protocol",
            "summary": "Day-scale canon refresh and presentation protocol for switching the Timeline view from broad campaign history into exact daily activity.",
            "files": ["HAPA_CHARACTER_SHEET_DAILY_TIMELINE_PROTOCOL.md", "hapa-character-sheet.daily-timeline-flow.json"],
        },
        {
            "title": "Character Profile Mining Protocol",
            "kind": "protocol",
            "summary": "Repeatable process for mining turns, skills, language, lore, relationships, and protocols into appendable human and agent personality dossiers.",
            "files": [
                "HAPA_CHARACTER_PROFILE_MINING_PROTOCOL.md",
                "HAPA_CHARACTER_PROFILE_MINING_PROMPT.md",
                "HAPA_CHARACTER_PROFILE_CALDER_FOUNDATION.md",
                "HAPA_CHARACTER_PROFILE_CALDER_SHARPENED.md",
                "hapa-character-profile-calder-foundation.json",
                "hapa-character-profile-calder-runs.json",
                "hapa-character-profile.observations.ndjson",
                "hapa-character-profile-mining-flow.json",
            ],
        },
        {
            "title": "Desktop/Web Packaging",
            "kind": "happ",
            "summary": "The design keeps the UI deployable as static web, desktop shell, and protocol-aware local node without mutating raw Second Brain state.",
            "files": ["HAPA_CHARACTER_SHEET_NODE_SPEC.md"],
        },
        {
            "title": "Kanban Tracking",
            "kind": "overwatch",
            "summary": "Append-only board state captures the implementation backlog and current project truth for humans and agents.",
            "files": ["hapa-character-sheet.board.config.json", "hapa-character-sheet.board.events.ndjson"],
        },
    ]

    top_skill_labels = [skill["label"] for skill in skills[:8]]
    resume = {
        "claims": [
            {
                "title": "Turns lived as applied skill evidence",
                "meta": f"{summary_counts['turns']:,} turns / {summary_counts['turn_learning_links']:,} learning links",
                "body": "AI collaboration turns are not treated as chat debris. They are indexed as proof of practice, result lineage, and reusable capability.",
                "proof": ["turn lineage", "result links", "wisdom cards"],
            },
            {
                "title": "Knowledge intake becomes operational memory",
                "meta": f"{summary_counts['items']:,} items / {summary_counts['exposures']:,} exposures",
                "body": "Books, media, references, tools, and source systems are normalized into topic, entity, and skill projections for retrieval.",
                "proof": ["source systems", "topic profiles", "content chunks"],
            },
            {
                "title": "Hapa nodes convert learning into apps",
                "meta": f"{summary_counts['nodes']:,} nodes / {summary_counts['node_skills']:,} node skills",
                "body": "Capabilities are framed as using and enhancing node skills, then linked back to general skill evidence, cards, topics, and artifacts.",
                "proof": ["nodes", "capabilities", "bridges"],
            },
        ],
        "outcomes": [
            {
                "title": "Built a Second Brain projection stack",
                "meta": "SQLite, CLI, API, wiki, node maps",
                "body": "A local-first memory system that turns consumed material, AI turns, Hapa apps, media, and protocols into queryable skill and result lineage.",
                "tags": ["data operations", "retrieval", "schema design"],
            },
            {
                "title": "Designed protocol-aware Hapa apps",
                "meta": "Manifest, API, CLI, board, docs",
                "body": "Hapa nodes carry standard contracts so humans and agents can inspect, run, extend, and track them with predictable surfaces.",
                "tags": ["happ contract", "protocol", "kanban"],
            },
            {
                "title": "Compressed professional proof into game UX",
                "meta": "Resume + stats + evidence",
                "body": "The Character Sheet reframes portfolio proof as RPG-readable stats without losing the evidence trail a professional evaluator needs.",
                "tags": ["resume", "portfolio", "skill codex"],
            },
            {
                "title": "Mapped agents and harnesses to work",
                "meta": f"{summary_counts['agents']:,} agents / {summary_counts['harnesses']:,} harness profiles",
                "body": "Agents are represented as operating profiles with skills, runtime affordances, memory policy, and node-level capability bridges.",
                "tags": ["agents", "harnesses", "routing"],
            },
            {
                "title": "Created media lineage for protocol artifacts",
                "meta": f"{summary_counts['media_jobs']:,} media jobs",
                "body": "Generated images, cards, avatars, and queue records are connected to node skills, turn skills, targets, and protocol presentation roles.",
                "tags": ["media registry", "cards", "avatars"],
            },
            {
                "title": "Tracked implementation as board state",
                "meta": f"{summary_counts['board_tasks']:,} seeded cards",
                "body": "The Character Sheet is already represented as an Overwatch Kanban board with source-labeled tasks and acceptance criteria.",
                "tags": ["quest keeper", "overwatch", "delivery"],
            },
        ],
        "proof_lanes": [
            {
                "label": "Knowledge",
                "body": "Source systems, content items, exposures, topic profiles, chunks, and entities explain where capability came from.",
                "metrics": [f"{summary_counts['items']:,} items", f"{summary_counts['topics']:,} topics", f"{summary_counts['chunks']:,} chunks"],
            },
            {
                "label": "Practice",
                "body": "Turns, learning links, result links, and wisdom cards show how knowledge was applied during AI collaboration.",
                "metrics": [f"{summary_counts['turns']:,} turns", f"{summary_counts['turn_learning_links']:,} learning links", f"{summary_counts['turn_result_links']:,} result links"],
            },
            {
                "label": "Output",
                "body": "Nodes, capabilities, bridges, protocol docs, media records, and board cards show what the work produced.",
                "metrics": [f"{summary_counts['nodes']:,} nodes", f"{summary_counts['capability_bridges']:,} bridges", f"{summary_counts['media_jobs']:,} media jobs"],
            },
        ],
    }

    profile = {
        "name": "Calder Wong / CJ",
        "handle": "Hapa",
        "title": "AI Systems Builder, Knowledge Architect, and Hapa Operator",
        "roles": ["Second Brain Architect", "Protocol Designer", "AI Collaboration Lead", "Media Systems Builder", "Node Operator"],
        "summary": "A professional character sheet that turns what was consumed, learned, practiced, built, and routed through agents into a fast, evidence-backed portfolio.",
        "resume_summary": f"Builds local-first AI knowledge systems that convert source material, AI turns, Hapa nodes, media artifacts, protocols, and board state into inspectable professional capability. Strongest indexed families include {', '.join(top_skill_labels[:5])}.",
    }

    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_database": str(DB),
        "profile": profile,
        "summary": summary_counts,
        "stats": stats,
        "resume": resume,
        "skill_families": skill_families,
        "node_type_summary": node_type_summary,
        "skills": skills,
        "nodes": nodes,
        "capabilities": capabilities,
        "topics": topics,
        "turns": turns,
        "learning_links": learning_links,
        "source_systems": source_systems,
        "mediums": mediums,
        "media": media,
        "image_sources": image_sources,
        "character_models": character_models,
        "profile_background_videos": profile_background_videos,
        "skill_video_loops": skill_video_loops,
        "timeline": timeline,
        "skill_quality": skill_quality,
        "character_profile": character_profile,
        "agents": agents,
        "harnesses": harnesses,
        "protocols": protocols,
        "docs": docs,
        "contracts": contracts,
        "board": board,
        "refresh": refresh,
        "projection_notes": {
            "learning_links_loaded": len(learning_links),
            "learning_links_total": summary_counts["turn_learning_links"],
            "timeline_beats_loaded": len(timeline["beats"]),
            "timeline_series_loaded": len(timeline["series"]),
            "skill_quality_rows_loaded": len(skill_quality["skill_quality"]),
            "avatar_skill_pairs_loaded": len(skill_quality["avatar_skill_experience"]),
            "character_models_loaded": len(character_models["items"]),
            "profile_background_videos_loaded": len(profile_background_videos["items"]),
            "skill_video_loops_loaded": len(skill_video_loops["items"]),
            "last_refresh_at": summary_counts["last_refresh_at"],
            "refresh_events_loaded": refresh["event_count"],
            "abstraction_policy": "Load every first-class skill, node, node skill, topic, turn, media job, character model, agent, harness, protocol article, board task, and source breakdown. Keep raw million-scale evidence as counts plus top lineage samples for browser usability.",
        },
    }
    conn.close()
    return data


def main() -> None:
    data = build()
    json_text = json.dumps(data, ensure_ascii=True, indent=2)
    (OUT / "hapa-character-sheet-data.json").write_text(json_text + "\n", encoding="utf-8")
    js_text = "window.HAPA_CHARACTER_SHEET_DATA = " + json.dumps(data, ensure_ascii=True, separators=(",", ":")) + ";\n"
    (OUT / "hapa-character-sheet-data.js").write_text(js_text, encoding="utf-8")
    (OUT / "hapa-character-sheet-prototype.html").write_text(HTML_STATIC, encoding="utf-8")
    print(
        json.dumps(
            {
                "skills": len(data["skills"]),
                "nodes": len(data["nodes"]),
                "capabilities": len(data["capabilities"]),
                "topics": len(data["topics"]),
                "turns": len(data["turns"]),
                "learning_links_loaded": len(data["learning_links"]),
                "media": len(data["media"]),
                "image_sources": len(data["image_sources"]["items"]),
                "profile_background_videos": len(data["profile_background_videos"]["items"]),
                "skill_video_loops": len(data["skill_video_loops"]["items"]),
                "timeline_beats": len(data["timeline"]["beats"]),
                "skill_quality_rows": len(data["skill_quality"]["skill_quality"]),
                "avatar_skill_pairs": len(data["skill_quality"]["avatar_skill_experience"]),
                "agents": len(data["agents"]),
                "board_tasks": len(data["board"]["tasks"]),
                "last_refresh_at": data["summary"].get("last_refresh_at", ""),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
