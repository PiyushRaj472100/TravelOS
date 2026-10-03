-- =============================================================================
-- TravelOS Analytics Data Warehouse
-- Migration 003: Create Tableau Read-Only SQL Server User
-- Engine: Microsoft SQL Server | Language: T-SQL
-- IMPORTANT: Run against MASTER first to create login, then switch to TravelOS_Analytics
-- =============================================================================

-- -----------------------------------------------------------------------
-- Step 1: Create SQL Server login (run in master database context)
-- -----------------------------------------------------------------------

USE master;
GO

IF NOT EXISTS (SELECT 1 FROM sys.server_principals WHERE name = 'travelos_tableau_reader')
BEGIN
    -- Replace the password below with your actual secure password
    -- Store in environment variables, never in source control
    CREATE LOGIN travelos_tableau_reader
        WITH PASSWORD = N'$(TABLEAU_SQLSERVER_PASSWORD)',
             CHECK_POLICY = ON,
             CHECK_EXPIRATION = OFF;
    PRINT 'Login travelos_tableau_reader created.';
END
ELSE
BEGIN
    PRINT 'Login travelos_tableau_reader already exists.';
END
GO

-- -----------------------------------------------------------------------
-- Step 2: Create database user mapped to the login
-- -----------------------------------------------------------------------

USE TravelOS_Analytics;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.database_principals WHERE name = 'travelos_tableau_reader'
)
BEGIN
    CREATE USER travelos_tableau_reader FOR LOGIN travelos_tableau_reader;
    PRINT 'Database user travelos_tableau_reader created.';
END
ELSE
BEGIN
    PRINT 'Database user travelos_tableau_reader already exists.';
END
GO

-- -----------------------------------------------------------------------
-- Step 3: Grant SELECT-only on analytics schema
-- The Tableau reader can only SELECT, never INSERT/UPDATE/DELETE/DROP
-- -----------------------------------------------------------------------

GRANT SELECT ON SCHEMA::analytics TO travelos_tableau_reader;
PRINT 'SELECT on schema analytics granted to travelos_tableau_reader.';
GO

-- -----------------------------------------------------------------------
-- Step 4: Explicitly DENY all write operations
-- Defense-in-depth: even if roles change, writes are denied
-- -----------------------------------------------------------------------

DENY INSERT ON SCHEMA::analytics TO travelos_tableau_reader;
DENY UPDATE ON SCHEMA::analytics TO travelos_tableau_reader;
DENY DELETE ON SCHEMA::analytics TO travelos_tableau_reader;
DENY ALTER  ON SCHEMA::analytics TO travelos_tableau_reader;
PRINT 'Write operations DENIED for travelos_tableau_reader.';
GO

-- -----------------------------------------------------------------------
-- Step 5: Verify
-- -----------------------------------------------------------------------

SELECT
    dp.name              AS principal_name,
    o.name               AS object_name,
    p.permission_name    AS permission,
    p.state_desc         AS state
FROM sys.database_permissions p
JOIN sys.database_principals dp ON p.grantee_principal_id = dp.principal_id
LEFT JOIN sys.objects o ON p.major_id = o.object_id
WHERE dp.name = 'travelos_tableau_reader'
ORDER BY p.permission_name;
GO

PRINT 'Migration 003 complete: travelos_tableau_reader created with SELECT-only access.';
GO

/*
=============================================================================
TABLEAU CONNECTION INSTRUCTIONS
=============================================================================

In Tableau Desktop:
  Connect > Microsoft SQL Server
  Server:   <your_sql_server_host>
  Database: TravelOS_Analytics
  Username: travelos_tableau_reader
  Password: (from TABLEAU_SQLSERVER_PASSWORD env var)
  Authentication: SQL Server Authentication

Tables/Views to use:
  analytics.v_user_trip_summary        -- Dashboard 2: User & Trip
  analytics.v_destination_popularity   -- Dashboard 3: Destinations
  analytics.v_monthly_trip_growth      -- Dashboard 1: Executive
  analytics.v_agent_performance        -- Dashboard 4: AI / Agents
  analytics.v_api_usage                -- Dashboard 5: Infrastructure
  analytics.v_trip_conversion          -- Dashboard 6: User Journey
  analytics.v_user_engagement          -- Dashboard 2 & 6
  analytics.v_error_summary            -- Dashboard 5
  analytics.v_user_retention           -- Dashboard 2

Filter for demo-only data:   WHERE is_demo = 1
Filter for production data:  WHERE is_demo = 0
Show all:                    (no filter)

=============================================================================
*/
