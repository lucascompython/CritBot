CREATE TABLE IF NOT EXISTS commands(
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE,
    number INT
);
CREATE TABLE IF NOT EXISTS guilds(
    id BIGINT PRIMARY KEY,
    prefix CHAR DEFAULT '.',
    lang VARCHAR(2) DEFAULT 'en',
    sponsorblock_categories TEXT [] DEFAULT '{"sponsor","selfpromo","intro","outro","music_offtopic"}',
    sponsorblock_print_segment_skipped BOOLEAN DEFAULT FALSE
);
CREATE TABLE IF NOT EXISTS top_commands(
    guild_id BIGINT REFERENCES guilds(id) ON DELETE CASCADE,
    command_name VARCHAR(50),
    usage_count INT,
    PRIMARY KEY(guild_id, command_name)
);