-- =============================================================================
-- TravelOS Analytics Data Warehouse
-- Automated Data Quality & Integrity Validation Test Suite
-- Engine: Microsoft SQL Server (T-SQL)
-- Database: TravelOS_Analytics
-- =============================================================================

USE TravelOS_Analytics;
GO

SET NOCOUNT ON;

PRINT '=============================================================================';
PRINT 'Starting TravelOS Analytics Data Warehouse Quality & Integrity Audit...';
PRINT 'Timestamp: ' + CONVERT(VARCHAR(30), SYSDATETIME(), 120);
PRINT '=============================================================================';

DECLARE @TotalTests INT = 0;
DECLARE @FailedTests INT = 0;

-- -----------------------------------------------------------------------------
-- TEST 1: Check Required Tables in Analytics Schema
-- -----------------------------------------------------------------------------
SET @TotalTests = @TotalTests + 1;
DECLARE @MissingTables INT;
SELECT @MissingTables = COUNT(*)
FROM (
    VALUES 
        ('dim_date'), ('dim_user'), ('dim_destination'), ('dim_agent'), ('dim_provider'), ('dim_trip'),
        ('fact_session'), ('fact_chat'), ('fact_flight_search'), ('fact_hotel_search'),
        ('fact_place_search'), ('fact_weather_search'), ('fact_itinerary'),
        ('fact_agent_execution'), ('fact_api_usage'), ('fact_error')
) AS Required(TableName)
WHERE NOT EXISTS (
    SELECT 1 FROM sys.tables t
    JOIN sys.schemas s ON t.schema_id = s.schema_id
    WHERE s.name = 'analytics' AND t.name = Required.TableName
);

IF @MissingTables = 0
    PRINT '[PASS] Test 1: All 16 dimension and fact tables exist in schema [analytics].';
ELSE
BEGIN
    SET @FailedTests = @FailedTests + 1;
    PRINT '[FAIL] Test 1: ' + CAST(@MissingTables AS VARCHAR(10)) + ' required tables are missing!';
END

-- -----------------------------------------------------------------------------
-- TEST 2: Orphan Records Check - fact_session -> dim_user
-- -----------------------------------------------------------------------------
SET @TotalTests = @TotalTests + 1;
DECLARE @OrphanSessions INT;
SELECT @OrphanSessions = COUNT(*)
FROM analytics.fact_session s
LEFT JOIN analytics.dim_user u ON s.user_key = u.user_key
WHERE u.user_key IS NULL;

IF @OrphanSessions = 0
    PRINT '[PASS] Test 2: Zero orphan fact_session records found (all map to valid dim_user).';
ELSE
BEGIN
    SET @FailedTests = @FailedTests + 1;
    PRINT '[FAIL] Test 2: ' + CAST(@OrphanSessions AS VARCHAR(10)) + ' orphan fact_session records found without valid user_key!';
END

-- -----------------------------------------------------------------------------
-- TEST 3: Orphan Records Check - fact_agent_execution -> dim_agent
-- -----------------------------------------------------------------------------
SET @TotalTests = @TotalTests + 1;
DECLARE @OrphanAgentExec INT;
SELECT @OrphanAgentExec = COUNT(*)
FROM analytics.fact_agent_execution e
LEFT JOIN analytics.dim_agent a ON e.agent_key = a.agent_key
WHERE a.agent_key IS NULL;

IF @OrphanAgentExec = 0
    PRINT '[PASS] Test 3: Zero orphan fact_agent_execution records (all map to valid dim_agent).';
ELSE
BEGIN
    SET @FailedTests = @FailedTests + 1;
    PRINT '[FAIL] Test 3: ' + CAST(@OrphanAgentExec AS VARCHAR(10)) + ' orphan agent executions found!';
END

-- -----------------------------------------------------------------------------
-- TEST 4: Orphan Records Check - fact_api_usage -> dim_provider
-- -----------------------------------------------------------------------------
SET @TotalTests = @TotalTests + 1;
DECLARE @OrphanApiUsage INT;
SELECT @OrphanApiUsage = COUNT(*)
FROM analytics.fact_api_usage u
LEFT JOIN analytics.dim_provider p ON u.provider_key = p.provider_key
WHERE p.provider_key IS NULL;

IF @OrphanApiUsage = 0
    PRINT '[PASS] Test 4: Zero orphan fact_api_usage records (all map to valid dim_provider).';
ELSE
BEGIN
    SET @FailedTests = @FailedTests + 1;
    PRINT '[FAIL] Test 4: ' + CAST(@OrphanApiUsage AS VARCHAR(10)) + ' orphan api usage records found!';
END

-- -----------------------------------------------------------------------------
-- TEST 5: Date Dimension Integrity Check in Facts
-- -----------------------------------------------------------------------------
SET @TotalTests = @TotalTests + 1;
DECLARE @InvalidDateKeys INT;
SELECT @InvalidDateKeys = 
    (SELECT COUNT(*) FROM analytics.fact_session s LEFT JOIN analytics.dim_date d ON s.date_key = d.date_key WHERE d.date_key IS NULL) +
    (SELECT COUNT(*) FROM analytics.fact_flight_search f LEFT JOIN analytics.dim_date d ON f.date_key = d.date_key WHERE d.date_key IS NULL) +
    (SELECT COUNT(*) FROM analytics.fact_agent_execution a LEFT JOIN analytics.dim_date d ON a.date_key = d.date_key WHERE d.date_key IS NULL);

IF @InvalidDateKeys = 0
    PRINT '[PASS] Test 5: All date_key values in facts match populated dim_date rows.';
ELSE
BEGIN
    SET @FailedTests = @FailedTests + 1;
    PRINT '[FAIL] Test 5: ' + CAST(@InvalidDateKeys AS VARCHAR(10)) + ' facts have invalid date_key references!';
END

-- -----------------------------------------------------------------------------
-- TEST 6: Domain & Range Sanity Checks (No negative latencies or durations)
-- -----------------------------------------------------------------------------
SET @TotalTests = @TotalTests + 1;
DECLARE @NegativeDurations INT;
SELECT @NegativeDurations = 
    (SELECT COUNT(*) FROM analytics.fact_session WHERE duration_seconds < 0) +
    (SELECT COUNT(*) FROM analytics.fact_agent_execution WHERE duration_ms < 0) +
    (SELECT COUNT(*) FROM analytics.fact_api_usage WHERE latency_ms < 0);

IF @NegativeDurations = 0
    PRINT '[PASS] Test 6: All latency and duration metrics are non-negative.';
ELSE
BEGIN
    SET @FailedTests = @FailedTests + 1;
    PRINT '[FAIL] Test 6: ' + CAST(@NegativeDurations AS VARCHAR(10)) + ' records contain negative duration/latency values!';
END

-- -----------------------------------------------------------------------------
-- TEST 7: Data Source & Demo Flag Integrity
-- -----------------------------------------------------------------------------
SET @TotalTests = @TotalTests + 1;
DECLARE @InvalidFlags INT;
SELECT @InvalidFlags = COUNT(*)
FROM analytics.fact_session
WHERE is_demo NOT IN (0, 1) OR data_source NOT IN ('production', 'synthetic');

IF @InvalidFlags = 0
    PRINT '[PASS] Test 7: All fact_session records have valid is_demo and data_source tags.';
ELSE
BEGIN
    SET @FailedTests = @FailedTests + 1;
    PRINT '[FAIL] Test 7: ' + CAST(@InvalidFlags AS VARCHAR(10)) + ' records have invalid flag states!';
END

-- -----------------------------------------------------------------------------
-- TEST 8: Analytical Views Validation
-- -----------------------------------------------------------------------------
SET @TotalTests = @TotalTests + 1;
DECLARE @MissingViews INT;
SELECT @MissingViews = COUNT(*)
FROM (
    VALUES 
        ('v_user_trip_summary'), ('v_destination_popularity'), ('v_monthly_trip_growth'),
        ('v_agent_performance'), ('v_api_usage'), ('v_error_summary'),
        ('v_user_engagement'), ('v_trip_conversion'), ('v_user_retention'),
        ('v_flight_search_summary'), ('v_hotel_search_summary'),
        ('v_place_search_summary'), ('v_weather_search_summary')
) AS ReqViews(ViewName)
WHERE NOT EXISTS (
    SELECT 1 FROM sys.views v
    JOIN sys.schemas s ON v.schema_id = s.schema_id
    WHERE s.name = 'analytics' AND v.name = ReqViews.ViewName
);

IF @MissingViews = 0
    PRINT '[PASS] Test 8: All 13 Tableau-ready views exist in schema [analytics].';
ELSE
BEGIN
    SET @FailedTests = @FailedTests + 1;
    PRINT '[FAIL] Test 8: ' + CAST(@MissingViews AS VARCHAR(10)) + ' views are missing!';
END

-- -----------------------------------------------------------------------------
-- SUMMARY SCORECARD
-- -----------------------------------------------------------------------------
PRINT '=============================================================================';
PRINT 'Data Quality Audit Completed: ' + CAST(@TotalTests - @FailedTests AS VARCHAR(10)) + ' / ' + CAST(@TotalTests AS VARCHAR(10)) + ' Passed.';
IF @FailedTests = 0
    PRINT 'Status: HEALTHY (All checks passed successfully)';
ELSE
    PRINT 'Status: WARNING (' + CAST(@FailedTests AS VARCHAR(10)) + ' tests failed. Review logs above)';
PRINT '=============================================================================';
GO
