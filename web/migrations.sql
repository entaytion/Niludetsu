-- Run this in Supabase SQL Editor before using the dashboard.

CREATE TABLE IF NOT EXISTS premium_guilds (
    guild_id TEXT PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT now(),
    expires_at TIMESTAMPTZ  -- NULL = lifetime premium
);

-- Example: grant lifetime premium to a guild
-- INSERT INTO premium_guilds (guild_id) VALUES ('1253442215875748666');
