-- One login method of each provider per user (e.g. at most one email + password).
-- The service checks this inside the same transaction as the insert; this index is
-- the backstop in the database.
-- Rows that broke the rule before this migration (concurrent link requests) keep the
-- first one linked and drop the rest, otherwise the index cannot be created.
DELETE FROM auth_identities
WHERE rowid NOT IN (
    SELECT MIN(rowid) FROM auth_identities GROUP BY user_id, provider
);
CREATE UNIQUE INDEX uq_auth_identities_user_provider ON auth_identities(user_id, provider);
