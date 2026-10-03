-- =============================================================================
-- TravelOS Analytics Data Warehouse
-- Migration 002: Create Tableau-Ready Analytical Views
-- Engine: Microsoft SQL Server | Language: T-SQL
-- Safe: CREATE OR ALTER VIEW (idempotent)
-- =============================================================================

USE TravelOS_Analytics;
GO

-- =============================================================================
-- v_user_trip_summary
-- Per-user trip summary for user analytics dashboards
-- =============================================================================
CREATE OR ALTER VIEW analytics.v_user_trip_summary AS
SELECT
    u.user_key,
    u.user_id,
    u.country,
    u.platform,
    u.acquisition_source,
    u.account_created_at,
    u.data_source,
    u.is_demo,
    COUNT(DISTINCT t.trip_key)                          AS total_trips,
    SUM(CASE WHEN t.trip_status = 'completed'  THEN 1 ELSE 0 END) AS completed_trips,
    SUM(CASE WHEN t.trip_status = 'abandoned'  THEN 1 ELSE 0 END) AS abandoned_trips,
    SUM(CASE WHEN t.trip_status = 'planned'    THEN 1 ELSE 0 END) AS planned_trips,
    AVG(CAST(t.duration_days AS FLOAT))                AS avg_duration_days,
    AVG(t.budget)                                      AS avg_budget,
    MAX(t.created_at)                                  AS last_trip_date,
    -- Favorite destination (most visited)
    (
        SELECT TOP 1 d2.destination_name
        FROM analytics.dim_trip t2
        JOIN analytics.dim_destination d2 ON t2.destination_key = d2.destination_key
        WHERE t2.user_key = u.user_key
        GROUP BY d2.destination_name
        ORDER BY COUNT(*) DESC
    ) AS favorite_destination
FROM analytics.dim_user u
LEFT JOIN analytics.dim_trip t ON u.user_key = t.user_key
GROUP BY
    u.user_key, u.user_id, u.country, u.platform, u.acquisition_source,
    u.account_created_at, u.data_source, u.is_demo;
GO

-- =============================================================================
-- v_destination_popularity
-- Destination analytics for Dashboard 3
-- =============================================================================
CREATE OR ALTER VIEW analytics.v_destination_popularity AS
SELECT
    d.destination_key,
    d.destination_name,
    d.city,
    d.country,
    d.region,
    d.latitude,
    d.longitude,
    COUNT(DISTINCT t.trip_key)                          AS trip_count,
    COUNT(DISTINCT t.user_key)                          AS unique_users,
    AVG(CAST(t.duration_days AS FLOAT))                AS avg_duration_days,
    AVG(t.budget)                                      AS avg_budget,
    COUNT(DISTINCT fs.flight_search_key)                AS flight_searches,
    COUNT(DISTINCT hs.hotel_search_key)                 AS hotel_searches,
    COUNT(DISTINCT ps.place_search_key)                 AS place_searches,
    COUNT(DISTINCT i.itinerary_key)                     AS itineraries_generated
FROM analytics.dim_destination d
LEFT JOIN analytics.dim_trip             t  ON d.destination_key = t.destination_key
LEFT JOIN analytics.fact_flight_search   fs ON t.trip_key = fs.trip_key
LEFT JOIN analytics.fact_hotel_search    hs ON t.trip_key = hs.trip_key
LEFT JOIN analytics.fact_place_search    ps ON t.trip_key = ps.trip_key
LEFT JOIN analytics.fact_itinerary       i  ON t.trip_key = i.trip_key
GROUP BY
    d.destination_key, d.destination_name, d.city, d.country,
    d.region, d.latitude, d.longitude;
GO

-- =============================================================================
-- v_monthly_trip_growth
-- Monthly trends for Executive Dashboard
-- =============================================================================
CREATE OR ALTER VIEW analytics.v_monthly_trip_growth AS
SELECT
    dd.year,
    dd.month,
    dd.month_name,
    CAST(dd.year AS NVARCHAR(4)) + '-' + RIGHT('0' + CAST(dd.month AS NVARCHAR(2)), 2) AS year_month,
    COUNT(DISTINCT t.trip_key)                AS total_trips,
    COUNT(DISTINCT t.user_key)                AS active_users,
    SUM(CASE WHEN t.trip_status = 'completed' THEN 1 ELSE 0 END) AS completed_trips,
    SUM(CASE WHEN t.trip_status = 'abandoned' THEN 1 ELSE 0 END) AS abandoned_trips,
    AVG(t.budget)                             AS avg_budget,
    t.data_source,
    t.is_demo
FROM analytics.dim_trip t
JOIN analytics.dim_date dd ON dd.full_date = CAST(t.created_at AS DATE)
GROUP BY dd.year, dd.month, dd.month_name, t.data_source, t.is_demo;
GO

-- =============================================================================
-- v_agent_performance
-- AI agent performance — supports any number of agents dynamically
-- =============================================================================
CREATE OR ALTER VIEW analytics.v_agent_performance AS
SELECT
    a.agent_key,
    a.agent_name,
    a.agent_type,
    a.agent_version,
    a.is_active,
    COUNT(ae.execution_key)                                AS execution_count,
    SUM(CASE WHEN ae.status = 'success' THEN 1 ELSE 0 END) AS successful_executions,
    SUM(CASE WHEN ae.status = 'failed'  THEN 1 ELSE 0 END) AS failed_executions,
    SUM(CASE WHEN ae.status = 'skipped' THEN 1 ELSE 0 END) AS skipped_executions,
    CASE WHEN COUNT(ae.execution_key) > 0
         THEN CAST(SUM(CASE WHEN ae.status='success' THEN 1.0 ELSE 0 END) / COUNT(ae.execution_key) * 100 AS DECIMAL(5,2))
         ELSE NULL END                                     AS success_rate_pct,
    AVG(CAST(ae.duration_ms AS FLOAT))                    AS avg_latency_ms,
    AVG(CAST(ae.input_tokens  AS FLOAT))                  AS avg_input_tokens,
    AVG(CAST(ae.output_tokens AS FLOAT))                  AS avg_output_tokens,
    ae.data_source,
    ae.is_demo
FROM analytics.dim_agent a
LEFT JOIN analytics.fact_agent_execution ae ON a.agent_key = ae.agent_key
GROUP BY a.agent_key, a.agent_name, a.agent_type, a.agent_version, a.is_active, ae.data_source, ae.is_demo;
GO

-- =============================================================================
-- v_api_usage
-- Provider API analytics for Dashboard 5
-- =============================================================================
CREATE OR ALTER VIEW analytics.v_api_usage AS
SELECT
    p.provider_key,
    p.provider_name,
    p.provider_type,
    au.endpoint,
    COUNT(au.api_usage_key)                                  AS total_calls,
    SUM(CASE WHEN au.success = 1 THEN 1 ELSE 0 END)          AS successful_calls,
    SUM(CASE WHEN au.success = 0 THEN 1 ELSE 0 END)          AS failed_calls,
    CASE WHEN COUNT(au.api_usage_key) > 0
         THEN CAST(SUM(CASE WHEN au.success=1 THEN 1.0 ELSE 0 END) / COUNT(au.api_usage_key) * 100 AS DECIMAL(5,2))
         ELSE NULL END                                        AS success_rate_pct,
    AVG(CAST(au.latency_ms AS FLOAT))                        AS avg_latency_ms,
    SUM(au.estimated_cost)                                    AS total_estimated_cost,
    au.data_source,
    au.is_demo
FROM analytics.dim_provider p
LEFT JOIN analytics.fact_api_usage au ON p.provider_key = au.provider_key
GROUP BY p.provider_key, p.provider_name, p.provider_type, au.endpoint, au.data_source, au.is_demo;
GO

-- =============================================================================
-- v_error_summary
-- Error analytics — by service, provider, agent
-- =============================================================================
CREATE OR ALTER VIEW analytics.v_error_summary AS
SELECT
    e.service,
    e.error_type,
    e.status_code,
    p.provider_name,
    a.agent_name,
    COUNT(e.error_key)                                    AS error_count,
    SUM(CASE WHEN e.resolved = 1 THEN 1 ELSE 0 END)       AS resolved_count,
    SUM(CASE WHEN e.resolved = 0 THEN 1 ELSE 0 END)       AS unresolved_count,
    MIN(e.timestamp)                                      AS first_occurrence,
    MAX(e.timestamp)                                      AS last_occurrence,
    e.data_source,
    e.is_demo
FROM analytics.fact_error e
LEFT JOIN analytics.dim_provider p ON e.provider_key = p.provider_key
LEFT JOIN analytics.dim_agent    a ON e.agent_key    = a.agent_key
GROUP BY e.service, e.error_type, e.status_code, p.provider_name, a.agent_name, e.data_source, e.is_demo;
GO

-- =============================================================================
-- v_user_engagement
-- Session-level engagement metrics
-- =============================================================================
CREATE OR ALTER VIEW analytics.v_user_engagement AS
SELECT
    u.user_key,
    u.user_id,
    u.country,
    u.data_source,
    u.is_demo,
    COUNT(DISTINCT s.session_event_key)             AS total_sessions,
    AVG(CAST(s.message_count AS FLOAT))             AS avg_messages_per_session,
    SUM(CAST(s.trip_started AS INT))                AS sessions_with_trip,
    SUM(CAST(s.itinerary_generated AS INT))         AS sessions_with_itinerary,
    -- avg session duration minutes
    AVG(CAST(DATEDIFF(MINUTE, s.started_at, ISNULL(s.ended_at, s.started_at)) AS FLOAT)) AS avg_session_duration_min,
    MAX(s.started_at)                               AS last_session_at
FROM analytics.dim_user u
LEFT JOIN analytics.fact_session s ON u.user_key = s.user_key
GROUP BY u.user_key, u.user_id, u.country, u.data_source, u.is_demo;
GO

-- =============================================================================
-- v_trip_conversion
-- Funnel: session -> trip -> searches -> itinerary -> completion
-- =============================================================================
CREATE OR ALTER VIEW analytics.v_trip_conversion AS
SELECT
    u.user_key,
    u.user_id,
    u.data_source,
    u.is_demo,
    COUNT(DISTINCT s.session_event_key)                          AS sessions_started,
    COUNT(DISTINCT t.trip_key)                                   AS trips_started,
    COUNT(DISTINCT fs.flight_search_key)                         AS flight_searches,
    COUNT(DISTINCT hs.hotel_search_key)                          AS hotel_searches,
    COUNT(DISTINCT ps.place_search_key)                          AS place_searches,
    COUNT(DISTINCT i.itinerary_key)                              AS itineraries_generated,
    SUM(CASE WHEN t.trip_status = 'completed' THEN 1 ELSE 0 END) AS trips_completed
FROM analytics.dim_user u
LEFT JOIN analytics.fact_session       s  ON u.user_key = s.user_key
LEFT JOIN analytics.dim_trip           t  ON u.user_key = t.user_key
LEFT JOIN analytics.fact_flight_search fs ON t.trip_key = fs.trip_key
LEFT JOIN analytics.fact_hotel_search  hs ON t.trip_key = hs.trip_key
LEFT JOIN analytics.fact_place_search  ps ON t.trip_key = ps.trip_key
LEFT JOIN analytics.fact_itinerary     i  ON t.trip_key = i.trip_key
GROUP BY u.user_key, u.user_id, u.data_source, u.is_demo;
GO

-- =============================================================================
-- v_user_retention
-- Cohort-style retention — users with activity in multiple months
-- =============================================================================
CREATE OR ALTER VIEW analytics.v_user_retention AS
SELECT
    u.user_key,
    u.user_id,
    u.data_source,
    u.is_demo,
    YEAR(u.account_created_at)  AS cohort_year,
    MONTH(u.account_created_at) AS cohort_month,
    COUNT(DISTINCT CAST(YEAR(s.started_at) AS NVARCHAR(4)) + '-' + CAST(MONTH(s.started_at) AS NVARCHAR(2)))
                                AS active_months,
    MIN(s.started_at)           AS first_session,
    MAX(s.started_at)           AS last_session
FROM analytics.dim_user u
LEFT JOIN analytics.fact_session s ON u.user_key = s.user_key
GROUP BY u.user_key, u.user_id, u.data_source, u.is_demo,
         YEAR(u.account_created_at), MONTH(u.account_created_at);
GO

-- =============================================================================
-- v_flight_search_summary
-- =============================================================================
CREATE OR ALTER VIEW analytics.v_flight_search_summary AS
SELECT
    dd.year,
    dd.month,
    dd.month_name,
    fs.origin,
    fs.destination,
    fs.cabin_class,
    COUNT(fs.flight_search_key)                              AS total_searches,
    SUM(CASE WHEN fs.success = 1 THEN 1 ELSE 0 END)          AS successful_searches,
    AVG(CAST(fs.results_count AS FLOAT))                     AS avg_results,
    AVG(fs.lowest_price)                                     AS avg_lowest_price,
    AVG(CAST(fs.latency_ms AS FLOAT))                        AS avg_latency_ms,
    fs.data_source,
    fs.is_demo
FROM analytics.fact_flight_search fs
JOIN analytics.dim_date dd ON dd.full_date = CAST(fs.timestamp AS DATE)
GROUP BY dd.year, dd.month, dd.month_name, fs.origin, fs.destination, fs.cabin_class, fs.data_source, fs.is_demo;
GO

-- =============================================================================
-- v_hotel_search_summary
-- =============================================================================
CREATE OR ALTER VIEW analytics.v_hotel_search_summary AS
SELECT
    dd.year,
    dd.month,
    dd.month_name,
    hs.destination,
    COUNT(hs.hotel_search_key)                               AS total_searches,
    SUM(CASE WHEN hs.success = 1 THEN 1 ELSE 0 END)          AS successful_searches,
    AVG(CAST(hs.results_count AS FLOAT))                     AS avg_results,
    AVG(hs.lowest_price)                                     AS avg_lowest_price,
    AVG(CAST(hs.latency_ms AS FLOAT))                        AS avg_latency_ms,
    hs.data_source,
    hs.is_demo
FROM analytics.fact_hotel_search hs
JOIN analytics.dim_date dd ON dd.full_date = CAST(hs.timestamp AS DATE)
GROUP BY dd.year, dd.month, dd.month_name, hs.destination, hs.data_source, hs.is_demo;
GO

-- =============================================================================
-- v_place_search_summary
-- =============================================================================
CREATE OR ALTER VIEW analytics.v_place_search_summary AS
SELECT
    dd.year,
    dd.month,
    dd.month_name,
    ps.destination,
    ps.category,
    COUNT(ps.place_search_key)  AS total_searches,
    AVG(CAST(ps.results_count AS FLOAT)) AS avg_results,
    ps.data_source,
    ps.is_demo
FROM analytics.fact_place_search ps
JOIN analytics.dim_date dd ON dd.full_date = CAST(ps.timestamp AS DATE)
GROUP BY dd.year, dd.month, dd.month_name, ps.destination, ps.category, ps.data_source, ps.is_demo;
GO

-- =============================================================================
-- v_weather_search_summary
-- =============================================================================
CREATE OR ALTER VIEW analytics.v_weather_search_summary AS
SELECT
    dd.year,
    dd.month,
    dd.month_name,
    ws.destination,
    COUNT(ws.weather_search_key) AS total_searches,
    AVG(CAST(ws.latency_ms AS FLOAT)) AS avg_latency_ms,
    ws.data_source,
    ws.is_demo
FROM analytics.fact_weather_search ws
JOIN analytics.dim_date dd ON dd.full_date = CAST(ws.timestamp AS DATE)
GROUP BY dd.year, dd.month, dd.month_name, ws.destination, ws.data_source, ws.is_demo;
GO

PRINT 'Migration 002 complete: All Tableau-ready views created.';
GO
