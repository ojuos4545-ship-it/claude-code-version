-- When the user agreed to the collection of their meal records (PRD Q6).
-- Existing rows stay NULL: they were created before consent was collected.
ALTER TABLE users ADD COLUMN consented_at TEXT;
