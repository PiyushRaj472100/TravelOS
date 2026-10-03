-- =============================================================================
-- TravelOS Analytics Data Warehouse
-- Example Analytical Queries (T-SQL)
-- Engine: Microsoft SQL Server
-- Database: TravelOS_Analytics
-- Schema: analytics
-- =============================================================================

USE TravelOS_Analytics;
GO

-- =============================================================================
-- 1. EXECUTIVE KPI SUMMARY SCORECARD
-- High-level snapshot of user volume, session engagement, and conversion
-- =============================================================================
SELECT
    COUNT(DISTINCT s.session_key)                                              AS total_sessions,
    COUNT(DISTINCT s.user_key)                                                 AS total_active_users,
    SUM(CASE WHEN s.itinerary_generated = 1 THEN 1 ELSE 0 END)                 AS total_itineraries_created,
    CAST(ROUND(100.0 * SUM(CASE WHEN s.itinerary_generated = 1 THEN 1 ELSE 0 END) 
         / NULLIF(COUNT(DISTINCT s.session_key), 0), 2) AS DECIMAL(5,2))       AS session_to_itinerary_conversion_pct,
    AVG(s.message_count)                                                       AS avg_messages_per_session,
    AVG(s.duration_seconds)                                                    AS avg_session_duration_seconds
FROM analytics.fact_session s
WHERE s.is_demo = 1; -- Filter: 1 for synthetic demo, 0 for production
GO

-- =============================================================================
-- 2. DESTINATION POPULARITY & DEMAND MATRIX
-- Combines flight searches, hotel searches, and generated itineraries
-- =============================================================================
SELECT TOP 10
    d.destination_name,
    d.country,
    COUNT(DISTINCT fs.search_key)                                             AS total_flight_searches,
    COUNT(DISTINCT hs.search_key)                                             AS total_hotel_searches,
    COUNT(DISTINCT i.itinerary_key)                                           AS total_itineraries_built,
    AVG(hs.lowest_price)                                                      AS avg_hotel_price_quoted,
    AVG(fs.lowest_price)                                                      AS avg_flight_price_quoted
FROM analytics.dim_destination d
LEFT JOIN analytics.fact_flight_search fs ON d.destination_key = fs.destination_key AND fs.is_demo = 1
LEFT JOIN analytics.fact_hotel_search  hs ON d.destination_key = hs.destination_key AND hs.is_demo = 1
LEFT JOIN analytics.fact_itinerary     i  ON d.destination_key = i.destination_key AND i.is_demo = 1
GROUP BY d.destination_name, d.country
ORDER BY total_itineraries_built DESC, total_hotel_searches DESC;
GO

-- =============================================================================
-- 3. END-TO-END CONVERSION FUNNEL
-- Session -> Search -> Itinerary Generation -> Completed Trip
-- =============================================================================
WITH FunnelStages AS (
    SELECT
        s.session_key,
        1 AS stage_1_session_started,
        CASE WHEN EXISTS (
            SELECT 1 FROM analytics.fact_flight_search f WHERE f.session_key = s.session_key
            UNION ALL
            SELECT 1 FROM analytics.fact_hotel_search h WHERE h.session_key = s.session_key
        ) THEN 1 ELSE 0 END AS stage_2_search_performed,
        CASE WHEN s.itinerary_generated = 1 THEN 1 ELSE 0 END AS stage_3_itinerary_generated,
        CASE WHEN EXISTS (
            SELECT 1 FROM analytics.dim_trip t WHERE t.session_id = s.session_id AND t.trip_status = 'completed'
        ) THEN 1 ELSE 0 END AS stage_4_trip_completed
    FROM analytics.fact_session s
    WHERE s.is_demo = 1
)
SELECT
    COUNT(*)                                                                 AS total_sessions,
    SUM(stage_2_search_performed)                                            AS sessions_with_search,
    SUM(stage_3_itinerary_generated)                                         AS sessions_with_itinerary,
    SUM(stage_4_trip_completed)                                              AS sessions_with_completed_trip,
    CAST(ROUND(100.0 * SUM(stage_2_search_performed) / COUNT(*), 2) AS DECIMAL(5,2))   AS dropoff_to_search_pct,
    CAST(ROUND(100.0 * SUM(stage_3_itinerary_generated) / NULLIF(SUM(stage_2_search_performed), 0), 2) AS DECIMAL(5,2)) AS search_to_itinerary_pct,
    CAST(ROUND(100.0 * SUM(stage_4_trip_completed) / NULLIF(SUM(stage_3_itinerary_generated), 0), 2) AS DECIMAL(5,2)) AS itinerary_to_completed_pct
FROM FunnelStages;
GO

-- =============================================================================
-- 4. AI AGENT PERFORMANCE & LATENCY BENCHMARKS (P50, P90, P95, AVG)
-- Evaluates OrchestratorAgent, ResearchAgent, HotelAgent, ActivityAgent, etc.
-- =============================================================================
SELECT
    a.agent_name,
    COUNT(*)                                                                 AS total_invocations,
    SUM(CASE WHEN e.status = 'success' THEN 1 ELSE 0 END)                    AS successful_runs,
    CAST(ROUND(100.0 * SUM(CASE WHEN e.status = 'success' THEN 1 ELSE 0 END) 
         / COUNT(*), 2) AS DECIMAL(5,2))                                     AS success_rate_pct,
    AVG(e.duration_ms)                                                       AS avg_duration_ms,
    -- SQL Server Percentile calculations
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY e.duration_ms) OVER (PARTITION BY a.agent_name) AS p50_duration_ms,
    PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY e.duration_ms) OVER (PARTITION BY a.agent_name) AS p90_duration_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY e.duration_ms) OVER (PARTITION BY a.agent_name) AS p95_duration_ms,
    SUM(COALESCE(e.input_tokens, 0))                                         AS total_input_tokens,
    SUM(COALESCE(e.output_tokens, 0))                                        AS total_output_tokens
FROM analytics.fact_agent_execution e
JOIN analytics.dim_agent a ON e.agent_key = a.agent_key
WHERE e.is_demo = 1
GROUP BY a.agent_name, e.duration_ms;
GO

-- =============================================================================
-- 5. EXTERNAL API PROVIDER RELIABILITY & COST SCORECARD
-- Duffel, RouteStack, Geoapify, MapTiler, Open-Meteo, Google Gemini
-- =============================================================================
SELECT
    p.provider_name,
    p.provider_type,
    COUNT(*)                                                                 AS total_api_calls,
    SUM(CASE WHEN u.success = 1 THEN 1 ELSE 0 END)                           AS successful_calls,
    CAST(ROUND(100.0 * SUM(CASE WHEN u.success = 1 THEN 1 ELSE 0 END) 
         / COUNT(*), 2) AS DECIMAL(5,2))                                     AS availability_sla_pct,
    AVG(u.latency_ms)                                                        AS avg_latency_ms,
    MAX(u.latency_ms)                                                        AS max_latency_ms,
    SUM(COALESCE(u.estimated_cost, 0.0))                                     AS total_estimated_cost_usd
FROM analytics.fact_api_usage u
JOIN analytics.dim_provider p ON u.provider_key = p.provider_key
WHERE u.is_demo = 1
GROUP BY p.provider_name, p.provider_type
ORDER BY total_api_calls DESC;
GO

-- =============================================================================
-- 6. SYSTEM ERROR RATE & ROOT CAUSE BREAKDOWN
-- Tracks failure hot-spots across services and agent execution
-- =============================================================================
SELECT
    err.service,
    err.error_type,
    COALESCE(p.provider_name, a.agent_name, 'System Core')                   AS component_source,
    COUNT(*)                                                                 AS incident_count,
    MAX(err.occurred_at)                                                     AS latest_incident_timestamp
FROM analytics.fact_error err
LEFT JOIN analytics.dim_provider p ON err.provider_key = p.provider_key
LEFT JOIN analytics.dim_agent    a ON err.agent_key    = a.agent_key
WHERE err.is_demo = 1
GROUP BY err.service, err.error_type, COALESCE(p.provider_name, a.agent_name, 'System Core')
ORDER BY incident_count DESC;
GO

-- =============================================================================
-- 7. USER COHORT RETENTION ANALYSIS (BY SIGNUP MONTH)
-- Cohort analysis showing percentage of users returning in subsequent months
-- =============================================================================
WITH UserCohorts AS (
    SELECT
        u.user_key,
        DATEFROMPARTS(YEAR(u.account_created_at), MONTH(u.account_created_at), 1) AS cohort_month
    FROM analytics.dim_user u
    WHERE u.is_demo = 1
),
UserActivities AS (
    SELECT
        s.user_key,
        DATEDIFF(month, uc.cohort_month, DATEFROMPARTS(d.year, d.month, 1)) AS month_number
    FROM analytics.fact_session s
    JOIN analytics.dim_date d ON s.date_key = d.date_key
    JOIN UserCohorts uc ON s.user_key = uc.user_key
    WHERE s.is_demo = 1
    GROUP BY s.user_key, DATEDIFF(month, uc.cohort_month, DATEFROMPARTS(d.year, d.month, 1))
)
SELECT
    uc.cohort_month,
    COUNT(DISTINCT uc.user_key)                                              AS cohort_size,
    COUNT(DISTINCT CASE WHEN ua.month_number = 0 THEN ua.user_key END)       AS month_0,
    COUNT(DISTINCT CASE WHEN ua.month_number = 1 THEN ua.user_key END)       AS month_1,
    COUNT(DISTINCT CASE WHEN ua.month_number = 2 THEN ua.user_key END)       AS month_2,
    COUNT(DISTINCT CASE WHEN ua.month_number = 3 THEN ua.user_key END)       AS month_3
FROM UserCohorts uc
LEFT JOIN UserActivities ua ON uc.user_key = ua.user_key
GROUP BY uc.cohort_month
ORDER BY uc.cohort_month;
GO

-- =============================================================================
-- 8. BUDGET FEASIBILITY & SPENDING DISTRIBUTION
-- User budget vs. estimated total trip cost (hotels + flights)
-- =============================================================================
SELECT
    CASE 
        WHEN t.budget < 1000 THEN 'Budget (< $1,000)'
        WHEN t.budget BETWEEN 1000 AND 3000 THEN 'Mid-range ($1,000 - $3,000)'
        WHEN t.budget BETWEEN 3001 AND 6000 THEN 'Premium ($3,001 - $6,000)'
        ELSE 'Luxury (> $6,000)'
    END AS budget_tier,
    COUNT(*)                                                                 AS trip_count,
    AVG(t.duration_days)                                                     AS avg_duration_days,
    AVG(t.budget)                                                            AS avg_planned_budget,
    SUM(CASE WHEN t.trip_status = 'completed' THEN 1 ELSE 0 END)             AS completed_trips
FROM analytics.dim_trip t
WHERE t.is_demo = 1
GROUP BY 
    CASE 
        WHEN t.budget < 1000 THEN 'Budget (< $1,000)'
        WHEN t.budget BETWEEN 1000 AND 3000 THEN 'Mid-range ($1,000 - $3,000)'
        WHEN t.budget BETWEEN 3001 AND 6000 THEN 'Premium ($3,001 - $6,000)'
        ELSE 'Luxury (> $6,000)'
    END
ORDER BY avg_planned_budget;
GO
