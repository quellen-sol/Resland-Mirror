-- Scratch database for the destructive test suites (see shared.testing
-- .destructive_db_ok and AGENTS.md). The live-Postgres fixtures refuse to run
-- against anything that isn't recognisably a test database.
--
-- Note: docker-entrypoint-initdb.d only runs on an empty data directory — an
-- existing `db-data` volume will not pick this up; recreate it or create the
-- database by hand.
CREATE DATABASE resland_test OWNER resland;
