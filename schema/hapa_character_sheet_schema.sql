-- Hapa Character Sheet app-owned schema.
-- Raw Second Brain memory remains read-only and external to this schema.

CREATE TABLE IF NOT EXISTS hcs_profile (
  profile_id TEXT PRIMARY KEY,
  display_name TEXT NOT NULL,
  handle TEXT,
  title TEXT,
  summary TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS hcs_section (
  section_id TEXT PRIMARY KEY,
  profile_id TEXT NOT NULL REFERENCES hcs_profile(profile_id),
  section_key TEXT NOT NULL,
  title TEXT NOT NULL,
  body TEXT,
  visibility TEXT NOT NULL DEFAULT 'owner',
  sort_order INTEGER NOT NULL DEFAULT 0,
  source_ref TEXT,
  reviewed_at TEXT
);

CREATE TABLE IF NOT EXISTS hcs_stat_snapshot (
  snapshot_id TEXT PRIMARY KEY,
  profile_id TEXT NOT NULL REFERENCES hcs_profile(profile_id),
  formula_version TEXT NOT NULL,
  stat_key TEXT NOT NULL,
  label TEXT NOT NULL,
  value INTEGER NOT NULL CHECK (value >= 0 AND value <= 99),
  rank_band TEXT NOT NULL,
  evidence_count INTEGER NOT NULL DEFAULT 0,
  source_count INTEGER NOT NULL DEFAULT 0,
  confidence REAL NOT NULL DEFAULT 0.0,
  explanation_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS hcs_pin (
  pin_id TEXT PRIMARY KEY,
  profile_id TEXT NOT NULL REFERENCES hcs_profile(profile_id),
  target_type TEXT NOT NULL,
  target_id TEXT NOT NULL,
  surface TEXT NOT NULL,
  visibility TEXT NOT NULL DEFAULT 'public',
  title_override TEXT,
  caption_override TEXT,
  sort_order INTEGER NOT NULL DEFAULT 0,
  reviewed_at TEXT
);

CREATE TABLE IF NOT EXISTS hcs_privacy_rule (
  rule_id TEXT PRIMARY KEY,
  profile_id TEXT NOT NULL REFERENCES hcs_profile(profile_id),
  visibility TEXT NOT NULL,
  target_type TEXT NOT NULL,
  target_id TEXT,
  field_path TEXT,
  action TEXT NOT NULL CHECK (action IN ('allow', 'redact', 'omit', 'summarize')),
  reason TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS hcs_export_manifest (
  manifest_id TEXT PRIMARY KEY,
  profile_id TEXT NOT NULL REFERENCES hcs_profile(profile_id),
  export_format TEXT NOT NULL,
  visibility TEXT NOT NULL,
  output_path TEXT NOT NULL,
  projection_hash TEXT,
  redaction_manifest_json TEXT NOT NULL DEFAULT '{}',
  provenance_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE VIEW IF NOT EXISTS hcs_public_claims AS
SELECT
  p.pin_id,
  p.profile_id,
  p.target_type,
  p.target_id,
  p.surface,
  p.title_override,
  p.caption_override,
  p.reviewed_at
FROM hcs_pin p
WHERE p.visibility = 'public'
  AND p.reviewed_at IS NOT NULL;
