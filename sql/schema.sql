CREATE TABLE IF NOT EXISTS guilds(
    id BIGINT PRIMARY KEY,
    prefix CHAR DEFAULT ',',
    locale VARCHAR(2) DEFAULT 'en',
    sponsorblock_categories TEXT [] DEFAULT '{"sponsor","selfpromo","intro","outro","music_offtopic"}',
    sponsorblock_print_segment_skipped BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_guilds_id ON guilds(id);
