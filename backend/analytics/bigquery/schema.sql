-- =============================================================================
-- TravelOS Analytics Data Warehouse
-- Engine: Google BigQuery (Standard SQL)
-- Dataset: travelos_analytics
-- =============================================================================

-- -----------------------------------------------------------------------------
-- DIMENSIONS
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `travelos_analytics.dim_date` (
    date_key    INT64    NOT NULL,
    full_date   DATE     NOT NULL,
    year        INT64    NOT NULL,
    quarter     INT64    NOT NULL,
    month       INT64    NOT NULL,
    month_name  STRING   NOT NULL,
    week        INT64    NOT NULL,
    day         INT64    NOT NULL,
    day_name    STRING   NOT NULL,
    is_weekend  BOOL     NOT NULL
);

CREATE TABLE IF NOT EXISTS `travelos_analytics.dim_user` (
    user_key           INT64     NOT NULL,
    user_id            STRING    NOT NULL,
    account_created_at TIMESTAMP NOT NULL,
    country            STRING,
    platform           STRING,
    acquisition_source STRING,
    data_source        STRING    NOT NULL,
    is_demo            BOOL      NOT NULL
);

CREATE TABLE IF NOT EXISTS `travelos_analytics.dim_destination` (
    destination_key  INT64    NOT NULL,
    destination_name STRING   NOT NULL,
    country          STRING,
    region           STRING,
    latitude         FLOAT64,
    longitude        FLOAT64
);

CREATE TABLE IF NOT EXISTS `travelos_analytics.dim_agent` (
    agent_key   INT64  NOT NULL,
    agent_name  STRING NOT NULL,
    agent_role  STRING NOT NULL,
    description STRING
);

CREATE TABLE IF NOT EXISTS `travelos_analytics.dim_provider` (
    provider_key  INT64  NOT NULL,
    provider_name STRING NOT NULL,
    provider_type STRING NOT NULL,
    description   STRING
);

CREATE TABLE IF NOT EXISTS `travelos_analytics.dim_trip` (
    trip_key         INT64     NOT NULL,
    user_key         INT64     NOT NULL,
    session_id       STRING    NOT NULL,
    destination_key  INT64,
    destination_name STRING,
    start_date       DATE,
    duration_days    INT64,
    budget           FLOAT64,
    currency         STRING,
    travelers        INT64,
    trip_status      STRING,
    created_at       TIMESTAMP NOT NULL,
    data_source      STRING    NOT NULL,
    is_demo          BOOL      NOT NULL
);

-- -----------------------------------------------------------------------------
-- FACTS (Partitioned by timestamp/date for fast OLAP scans & low BigQuery query costs)
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `travelos_analytics.fact_session` (
    session_key         INT64     NOT NULL,
    session_id          STRING    NOT NULL,
    user_key            INT64     NOT NULL,
    date_key            INT64,
    started_at          TIMESTAMP NOT NULL,
    ended_at            TIMESTAMP,
    duration_seconds    INT64,
    message_count       INT64,
    itinerary_generated BOOL,
    data_source         STRING    NOT NULL,
    is_demo             BOOL      NOT NULL
)
PARTITION BY DATE(started_at)
CLUSTER BY user_key, session_id;

CREATE TABLE IF NOT EXISTS `travelos_analytics.fact_chat` (
    chat_key          INT64     NOT NULL,
    session_key       INT64     NOT NULL,
    user_key          INT64     NOT NULL,
    trip_key          INT64,
    session_id        STRING    NOT NULL,
    message_timestamp TIMESTAMP NOT NULL,
    role              STRING    NOT NULL,
    intent            STRING,
    response_type     STRING,
    message_length    INT64,
    latency_ms        INT64,
    data_source       STRING    NOT NULL,
    is_demo           BOOL      NOT NULL
)
PARTITION BY DATE(message_timestamp)
CLUSTER BY session_key, role;

CREATE TABLE IF NOT EXISTS `travelos_analytics.fact_flight_search` (
    search_key          INT64     NOT NULL,
    session_key         INT64     NOT NULL,
    user_key            INT64     NOT NULL,
    trip_key            INT64,
    session_id          STRING    NOT NULL,
    date_key            INT64,
    search_timestamp    TIMESTAMP NOT NULL,
    origin_airport      STRING,
    destination_airport STRING,
    destination_key     INT64,
    departure_date      DATE,
    passengers          INT64,
    cabin_class         STRING,
    results_count       INT64,
    lowest_price        FLOAT64,
    currency            STRING,
    provider_key        INT64,
    success             BOOL,
    latency_ms          INT64,
    data_source         STRING    NOT NULL,
    is_demo             BOOL      NOT NULL
)
PARTITION BY DATE(search_timestamp)
CLUSTER BY destination_key, provider_key;

CREATE TABLE IF NOT EXISTS `travelos_analytics.fact_hotel_search` (
    search_key       INT64     NOT NULL,
    session_key      INT64     NOT NULL,
    user_key         INT64     NOT NULL,
    trip_key         INT64,
    session_id       STRING    NOT NULL,
    date_key         INT64,
    search_timestamp TIMESTAMP NOT NULL,
    destination_name STRING,
    destination_key  INT64,
    check_in_date    DATE,
    check_out_date   DATE,
    rooms            INT64,
    travelers        INT64,
    results_count    INT64,
    lowest_price     FLOAT64,
    currency         STRING,
    provider_key     INT64,
    success          BOOL,
    latency_ms       INT64,
    data_source      STRING    NOT NULL,
    is_demo          BOOL      NOT NULL
)
PARTITION BY DATE(search_timestamp)
CLUSTER BY destination_key, provider_key;

CREATE TABLE IF NOT EXISTS `travelos_analytics.fact_place_search` (
    search_key       INT64     NOT NULL,
    session_key      INT64     NOT NULL,
    user_key         INT64     NOT NULL,
    trip_key         INT64,
    session_id       STRING    NOT NULL,
    date_key         INT64,
    search_timestamp TIMESTAMP NOT NULL,
    destination_name STRING,
    destination_key  INT64,
    category         STRING,
    results_count    INT64,
    provider_key     INT64,
    success          BOOL,
    latency_ms       INT64,
    data_source      STRING    NOT NULL,
    is_demo          BOOL      NOT NULL
)
PARTITION BY DATE(search_timestamp);

CREATE TABLE IF NOT EXISTS `travelos_analytics.fact_weather_search` (
    search_key       INT64     NOT NULL,
    session_key      INT64     NOT NULL,
    user_key         INT64     NOT NULL,
    trip_key         INT64,
    session_id       STRING    NOT NULL,
    date_key         INT64,
    search_timestamp TIMESTAMP NOT NULL,
    destination_name STRING,
    destination_key  INT64,
    request_date     DATE,
    provider_key     INT64,
    success          BOOL,
    latency_ms       INT64,
    data_source      STRING    NOT NULL,
    is_demo          BOOL      NOT NULL
)
PARTITION BY DATE(search_timestamp);

CREATE TABLE IF NOT EXISTS `travelos_analytics.fact_itinerary` (
    itinerary_key      INT64     NOT NULL,
    session_key        INT64     NOT NULL,
    user_key           INT64     NOT NULL,
    trip_key           INT64,
    session_id         STRING    NOT NULL,
    date_key           INT64,
    generated_at       TIMESTAMP NOT NULL,
    destination_name   STRING,
    destination_key    INT64,
    duration_days      INT64,
    activity_count     INT64,
    generation_time_ms INT64,
    data_source        STRING    NOT NULL,
    is_demo            BOOL      NOT NULL
)
PARTITION BY DATE(generated_at)
CLUSTER BY destination_key;

CREATE TABLE IF NOT EXISTS `travelos_analytics.fact_agent_execution` (
    execution_key INT64     NOT NULL,
    session_key   INT64     NOT NULL,
    user_key      INT64     NOT NULL,
    trip_key      INT64,
    session_id    STRING    NOT NULL,
    agent_key     INT64     NOT NULL,
    date_key      INT64,
    started_at    TIMESTAMP NOT NULL,
    completed_at  TIMESTAMP NOT NULL,
    duration_ms   INT64,
    status        STRING    NOT NULL,
    model         STRING,
    input_tokens  INT64,
    output_tokens INT64,
    error_type    STRING,
    data_source   STRING    NOT NULL,
    is_demo       BOOL      NOT NULL
)
PARTITION BY DATE(started_at)
CLUSTER BY agent_key, status;

CREATE TABLE IF NOT EXISTS `travelos_analytics.fact_api_usage` (
    usage_key         INT64     NOT NULL,
    session_key       INT64     NOT NULL,
    user_key          INT64     NOT NULL,
    trip_key          INT64,
    session_id        STRING    NOT NULL,
    provider_key      INT64     NOT NULL,
    date_key          INT64,
    request_timestamp TIMESTAMP NOT NULL,
    endpoint          STRING,
    latency_ms        INT64,
    status_code       INT64,
    success           BOOL      NOT NULL,
    error_type        STRING,
    estimated_cost    FLOAT64,
    data_source       STRING    NOT NULL,
    is_demo           BOOL      NOT NULL
)
PARTITION BY DATE(request_timestamp)
CLUSTER BY provider_key, success;

CREATE TABLE IF NOT EXISTS `travelos_analytics.fact_error` (
    error_key    INT64     NOT NULL,
    session_key  INT64     NOT NULL,
    user_key     INT64     NOT NULL,
    trip_key     INT64,
    session_id   STRING    NOT NULL,
    date_key     INT64,
    occurred_at  TIMESTAMP NOT NULL,
    service      STRING    NOT NULL,
    error_type   STRING    NOT NULL,
    provider_key INT64,
    agent_key    INT64,
    status_code  INT64,
    data_source  STRING    NOT NULL,
    is_demo      BOOL      NOT NULL
)
PARTITION BY DATE(occurred_at)
CLUSTER BY service, error_type;

-- -----------------------------------------------------------------------------
-- ANALYTICAL VIEWS FOR TABLEAU
-- -----------------------------------------------------------------------------

CREATE OR REPLACE VIEW `travelos_analytics.v_destination_popularity` AS
SELECT
    d.destination_name,
    d.country,
    d.region,
    d.latitude,
    d.longitude,
    COUNT(DISTINCT hs.search_key)    AS total_hotel_searches,
    COUNT(DISTINCT fs.search_key)    AS total_flight_searches,
    COUNT(DISTINCT i.itinerary_key)  AS total_itineraries,
    AVG(hs.lowest_price)             AS avg_hotel_price,
    AVG(fs.lowest_price)             AS avg_flight_price
FROM `travelos_analytics.dim_destination` d
LEFT JOIN `travelos_analytics.fact_hotel_search` hs  ON d.destination_key = hs.destination_key
LEFT JOIN `travelos_analytics.fact_flight_search` fs ON d.destination_key = fs.destination_key
LEFT JOIN `travelos_analytics.fact_itinerary` i     ON d.destination_key = i.destination_key
GROUP BY d.destination_name, d.country, d.region, d.latitude, d.longitude;

CREATE OR REPLACE VIEW `travelos_analytics.v_agent_performance` AS
SELECT
    a.agent_name,
    COUNT(*)                                                 AS total_executions,
    COUNTIF(e.status = 'success')                            AS successful_executions,
    ROUND(100.0 * COUNTIF(e.status = 'success') / COUNT(*), 2) AS success_rate_pct,
    AVG(e.duration_ms)                                       AS avg_duration_ms,
    SUM(COALESCE(e.input_tokens, 0))                         AS total_input_tokens,
    SUM(COALESCE(e.output_tokens, 0))                        AS total_output_tokens
FROM `travelos_analytics.fact_agent_execution` e
JOIN `travelos_analytics.dim_agent` a ON e.agent_key = a.agent_key
GROUP BY a.agent_name;

CREATE OR REPLACE VIEW `travelos_analytics.v_api_usage` AS
SELECT
    p.provider_name,
    p.provider_type,
    COUNT(*)                                                 AS total_requests,
    COUNTIF(u.success = TRUE)                                AS successful_requests,
    ROUND(100.0 * COUNTIF(u.success = TRUE) / COUNT(*), 2)   AS availability_rate_pct,
    AVG(u.latency_ms)                                        AS avg_latency_ms,
    SUM(COALESCE(u.estimated_cost, 0.0))                     AS total_estimated_cost_usd
FROM `travelos_analytics.fact_api_usage` u
JOIN `travelos_analytics.dim_provider` p ON u.provider_key = p.provider_key
GROUP BY p.provider_name, p.provider_type;
