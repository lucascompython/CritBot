DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_type WHERE typname = 'Locale'
    ) THEN
        CREATE TYPE "Locale" AS ENUM ('Pt', 'En');
    END IF;
END$$;

CREATE TABLE IF NOT EXISTS guilds(
    id BIGINT PRIMARY KEY,
    prefix CHAR DEFAULT ',',
    locale "Locale",
    sponsorblock_categories TEXT[] DEFAULT '{"sponsor","selfpromo","intro","outro","music_offtopic"}',
    sponsorblock_print_segment_skipped BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_guilds_id ON guilds(id);
