-- The database users and the test database for the package's database tests: the same users an
-- application has (the template's specs/11-local-development.md#services), so the tests prove the
-- platform tables work under them.
--
-- Run as the superuser with psql variables for the prefix and the users' throwaway passwords: by CI
-- (.github/workflows/python-checks.yml), or by hand against a local container (README). Safe to rerun.
--
--   {prefix}_migrator  owns the schema; creates the platform tables
--   {prefix}_runtime   reads and writes data; granted its privileges by create_platform_tables
--   {prefix}_test      the database for the tests, owned by {prefix}_migrator

\set ON_ERROR_STOP on
\set migrator :prefix '_migrator'
\set runtime :prefix '_runtime'
\set test_database :prefix '_test'

SELECT format('CREATE ROLE %I LOGIN', :'migrator') WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = :'migrator')
\gexec
SELECT format('CREATE ROLE %I LOGIN', :'runtime') WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = :'runtime')
\gexec
ALTER ROLE :"migrator" PASSWORD :'migrator_password';
ALTER ROLE :"runtime" PASSWORD :'runtime_password';

-- The database owner owns the public schema (PostgreSQL 15 and later), so the migrator can create in it.
ALTER DATABASE :"DBNAME" OWNER TO :"migrator";

-- Tables made before the users existed belong to the superuser; the migrator takes them over.
-- psql variables do not reach inside a DO block, so the migrator's name is passed as a setting.
SELECT set_config('db_users.migrator', :'migrator', false) AS migrator_setting \gset
DO $$
DECLARE
    migrator text := current_setting('db_users.migrator');
    rel record;
BEGIN
    FOR rel IN
        SELECT c.relname, c.relkind
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public'
          AND c.relkind IN ('r', 'p', 'v', 'm', 'S')
          AND pg_get_userbyid(c.relowner) <> migrator
          -- A sequence owned by a column follows its table.
          AND NOT (c.relkind = 'S' AND EXISTS (
              SELECT FROM pg_depend d WHERE d.objid = c.oid AND d.deptype IN ('a', 'i')))
    LOOP
        EXECUTE format(
            'ALTER %s public.%I OWNER TO %I',
            CASE rel.relkind WHEN 'v' THEN 'VIEW' WHEN 'm' THEN 'MATERIALIZED VIEW' WHEN 'S' THEN 'SEQUENCE' ELSE 'TABLE' END,
            rel.relname,
            migrator);
    END LOOP;
END
$$;

SELECT format('CREATE DATABASE %I OWNER %I', :'test_database', :'migrator')
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = :'test_database')
\gexec
