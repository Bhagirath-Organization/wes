-- Deployment fix for origin/main bug: revision id
-- '0007_organizational_knowledge_engine' (36 chars) exceeds Alembic's default
-- alembic_version.version_num VARCHAR(32). Pre-create the table wider so Alembic
-- reuses it instead of creating a 32-char column. Runs once on fresh DB init.
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(128) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);
