-- A user is an identity only. How they log in lives in auth_identities, so a user
-- can start without one (anonymous) and link a login method later.
CREATE TABLE users (
    id         TEXT PRIMARY KEY,
    timezone   TEXT NOT NULL,
    created_at TEXT NOT NULL
);

-- provider: 'password' (identifier = normalized email, secret_hash = argon2 hash).
-- Future providers (e.g. social login) add rows with their own provider name.
CREATE TABLE auth_identities (
    provider    TEXT NOT NULL,
    identifier  TEXT NOT NULL,
    user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    secret_hash TEXT,
    created_at  TEXT NOT NULL,
    PRIMARY KEY (provider, identifier)
);
CREATE INDEX idx_auth_identities_user ON auth_identities(user_id);

CREATE TABLE sessions (
    token_hash TEXT PRIMARY KEY,
    user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
CREATE INDEX idx_sessions_user ON sessions(user_id);

-- meal_type / portion have no CHECK constraint on purpose: the value sets may
-- change (PRD Q8) and are validated in the application layer.
CREATE TABLE meals (
    id              TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    description     TEXT NOT NULL,
    meal_date       TEXT NOT NULL,
    meal_type       TEXT,
    portion         TEXT,
    memo            TEXT,
    idempotency_key TEXT,
    request_hash    TEXT,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);
CREATE INDEX idx_meals_user_date ON meals(user_id, meal_date, created_at);
CREATE INDEX idx_meals_user_created ON meals(user_id, created_at);
CREATE UNIQUE INDEX uq_meals_user_idem ON meals(user_id, idempotency_key)
    WHERE idempotency_key IS NOT NULL;
