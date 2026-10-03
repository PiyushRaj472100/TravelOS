-- =============================================================================
-- TravelOS Analytics Data Warehouse
-- Migration 001: Create Schema, Dimensions, Facts
-- Engine: Microsoft SQL Server | Language: T-SQL
-- Run once against: TravelOS_Analytics database
-- Safe: Additive only (IF NOT EXISTS guards throughout)
-- =============================================================================

USE TravelOS_Analytics;
GO

-- Analytics schema
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'analytics')
    EXEC('CREATE SCHEMA analytics');
GO

-- =============================================================================
-- DIMENSION: dim_date
-- =============================================================================
IF NOT EXISTS (SELECT 1 FROM sys.objects WHERE object_id = OBJECT_ID(N'analytics.dim_date') AND type = 'U')
BEGIN
    CREATE TABLE analytics.dim_date (
        date_key    INT          NOT NULL,
        full_date   DATE         NOT NULL,
        year        SMALLINT     NOT NULL,
        quarter     TINYINT      NOT NULL,
        month       TINYINT      NOT NULL,
        month_name  NVARCHAR(20) NOT NULL,
        week        TINYINT      NOT NULL,
        day         TINYINT      NOT NULL,
        day_name    NVARCHAR(20) NOT NULL,
        is_weekend  BIT          NOT NULL DEFAULT 0,
        CONSTRAINT PK_dim_date PRIMARY KEY CLUSTERED (date_key)
    );
END
GO

-- =============================================================================
-- DIMENSION: dim_user
-- =============================================================================
IF NOT EXISTS (SELECT 1 FROM sys.objects WHERE object_id = OBJECT_ID(N'analytics.dim_user') AND type = 'U')
BEGIN
    CREATE TABLE analytics.dim_user (
        user_key           INT          NOT NULL IDENTITY(1,1),
        user_id            NVARCHAR(100) NOT NULL,
        account_created_at DATETIME2    NOT NULL DEFAULT SYSDATETIME(),
        country            NVARCHAR(100) NULL,
        platform           NVARCHAR(50)  NULL,
        acquisition_source NVARCHAR(100) NULL,
        data_source        NVARCHAR(20)  NOT NULL DEFAULT 'production',
        is_demo            BIT          NOT NULL DEFAULT 0,
        created_at         DATETIME2    NOT NULL DEFAULT SYSDATETIME(),
        CONSTRAINT PK_dim_user PRIMARY KEY CLUSTERED (user_key),
        CONSTRAINT UQ_dim_user_id UNIQUE (user_id)
    );
    CREATE NONCLUSTERED INDEX IX_dim_user_is_demo ON analytics.dim_user (is_demo);
END
GO

-- =============================================================================
-- DIMENSION: dim_destination
-- =============================================================================
IF NOT EXISTS (SELECT 1 FROM sys.objects WHERE object_id = OBJECT_ID(N'analytics.dim_destination') AND type = 'U')
BEGIN
    CREATE TABLE analytics.dim_destination (
        destination_key  INT          NOT NULL IDENTITY(1,1),
        destination_id   NVARCHAR(100) NOT NULL,
        destination_name NVARCHAR(200) NOT NULL,
        city             NVARCHAR(200) NULL,
        country          NVARCHAR(200) NULL,
        region           NVARCHAR(200) NULL,
        latitude         DECIMAL(9,6)  NULL,
        longitude        DECIMAL(9,6)  NULL,
        created_at       DATETIME2    NOT NULL DEFAULT SYSDATETIME(),
        CONSTRAINT PK_dim_destination PRIMARY KEY CLUSTERED (destination_key),
        CONSTRAINT UQ_dim_destination_id UNIQUE (destination_id)
    );
    CREATE NONCLUSTERED INDEX IX_dim_destination_name ON analytics.dim_destination (destination_name);
END
GO

-- =============================================================================
-- DIMENSION: dim_agent  (dynamic — any number of agents)
-- =============================================================================
IF NOT EXISTS (SELECT 1 FROM sys.objects WHERE object_id = OBJECT_ID(N'analytics.dim_agent') AND type = 'U')
BEGIN
    CREATE TABLE analytics.dim_agent (
        agent_key     INT          NOT NULL IDENTITY(1,1),
        agent_name    NVARCHAR(100) NOT NULL,
        agent_type    NVARCHAR(100) NULL,
        agent_version NVARCHAR(50)  NULL,
        created_at    DATETIME2    NOT NULL DEFAULT SYSDATETIME(),
        is_active     BIT          NOT NULL DEFAULT 1,
        CONSTRAINT PK_dim_agent PRIMARY KEY CLUSTERED (agent_key),
        CONSTRAINT UQ_dim_agent_name UNIQUE (agent_name)
    );
END
GO

-- =============================================================================
-- DIMENSION: dim_provider  (dynamic — any number of providers)
-- =============================================================================
IF NOT EXISTS (SELECT 1 FROM sys.objects WHERE object_id = OBJECT_ID(N'analytics.dim_provider') AND type = 'U')
BEGIN
    CREATE TABLE analytics.dim_provider (
        provider_key  INT          NOT NULL IDENTITY(1,1),
        provider_name NVARCHAR(100) NOT NULL,
        provider_type NVARCHAR(100) NULL,
        created_at    DATETIME2    NOT NULL DEFAULT SYSDATETIME(),
        CONSTRAINT PK_dim_provider PRIMARY KEY CLUSTERED (provider_key),
        CONSTRAINT UQ_dim_provider_name UNIQUE (provider_name)
    );
END
GO

-- =============================================================================
-- DIMENSION: dim_trip
-- =============================================================================
IF NOT EXISTS (SELECT 1 FROM sys.objects WHERE object_id = OBJECT_ID(N'analytics.dim_trip') AND type = 'U')
BEGIN
    CREATE TABLE analytics.dim_trip (
        trip_key        INT          NOT NULL IDENTITY(1,1),
        trip_id         NVARCHAR(100) NOT NULL,
        user_key        INT          NULL,
        session_id      NVARCHAR(200) NULL,
        destination_key INT          NULL,
        start_date      DATE         NULL,
        end_date        DATE         NULL,
        duration_days   INT          NULL,
        traveler_count  INT          NULL,
        budget          DECIMAL(18,2) NULL,
        currency        NVARCHAR(10)  NULL,
        travel_style    NVARCHAR(100) NULL,
        trip_status     NVARCHAR(50)  NOT NULL DEFAULT 'planned',
        created_at      DATETIME2    NOT NULL DEFAULT SYSDATETIME(),
        completed_at    DATETIME2    NULL,
        data_source     NVARCHAR(20)  NOT NULL DEFAULT 'production',
        is_demo         BIT          NOT NULL DEFAULT 0,
        CONSTRAINT PK_dim_trip PRIMARY KEY CLUSTERED (trip_key),
        CONSTRAINT UQ_dim_trip_id UNIQUE (trip_id),
        CONSTRAINT FK_dim_trip_user FOREIGN KEY (user_key) REFERENCES analytics.dim_user (user_key),
        CONSTRAINT FK_dim_trip_destination FOREIGN KEY (destination_key) REFERENCES analytics.dim_destination (destination_key)
    );
    CREATE NONCLUSTERED INDEX IX_dim_trip_user_key ON analytics.dim_trip (user_key);
    CREATE NONCLUSTERED INDEX IX_dim_trip_status   ON analytics.dim_trip (trip_status);
    CREATE NONCLUSTERED INDEX IX_dim_trip_is_demo  ON analytics.dim_trip (is_demo);
END
GO

-- =============================================================================
-- FACT: fact_session
-- =============================================================================
IF NOT EXISTS (SELECT 1 FROM sys.objects WHERE object_id = OBJECT_ID(N'analytics.fact_session') AND type = 'U')
BEGIN
    CREATE TABLE analytics.fact_session (
        session_event_key   INT          NOT NULL IDENTITY(1,1),
        user_key            INT          NULL,
        session_id          NVARCHAR(200) NOT NULL,
        started_at          DATETIME2    NOT NULL,
        ended_at            DATETIME2    NULL,
        message_count       INT          NOT NULL DEFAULT 0,
        trip_started        BIT          NOT NULL DEFAULT 0,
        itinerary_generated BIT          NOT NULL DEFAULT 0,
        session_status      NVARCHAR(50)  NOT NULL DEFAULT 'active',
        data_source         NVARCHAR(20)  NOT NULL DEFAULT 'production',
        is_demo             BIT          NOT NULL DEFAULT 0,
        CONSTRAINT PK_fact_session PRIMARY KEY CLUSTERED (session_event_key),
        CONSTRAINT FK_fact_session_user FOREIGN KEY (user_key) REFERENCES analytics.dim_user (user_key)
    );
    CREATE NONCLUSTERED INDEX IX_fact_session_user_key  ON analytics.fact_session (user_key);
    CREATE NONCLUSTERED INDEX IX_fact_session_started   ON analytics.fact_session (started_at);
    CREATE NONCLUSTERED INDEX IX_fact_session_is_demo   ON analytics.fact_session (is_demo);
END
GO

-- =============================================================================
-- FACT: fact_chat  (no private message content stored)
-- =============================================================================
IF NOT EXISTS (SELECT 1 FROM sys.objects WHERE object_id = OBJECT_ID(N'analytics.fact_chat') AND type = 'U')
BEGIN
    CREATE TABLE analytics.fact_chat (
        chat_event_key INT          NOT NULL IDENTITY(1,1),
        user_key       INT          NULL,
        session_id     NVARCHAR(200) NOT NULL,
        trip_key       INT          NULL,
        timestamp      DATETIME2    NOT NULL,
        role           NVARCHAR(20)  NOT NULL,
        intent         NVARCHAR(100) NULL,
        response_type  NVARCHAR(100) NULL,
        message_length INT          NULL,
        latency_ms     INT          NULL,
        data_source    NVARCHAR(20)  NOT NULL DEFAULT 'production',
        is_demo        BIT          NOT NULL DEFAULT 0,
        CONSTRAINT PK_fact_chat PRIMARY KEY CLUSTERED (chat_event_key),
        CONSTRAINT FK_fact_chat_user FOREIGN KEY (user_key) REFERENCES analytics.dim_user (user_key),
        CONSTRAINT FK_fact_chat_trip FOREIGN KEY (trip_key) REFERENCES analytics.dim_trip (trip_key)
    );
    CREATE NONCLUSTERED INDEX IX_fact_chat_session   ON analytics.fact_chat (session_id);
    CREATE NONCLUSTERED INDEX IX_fact_chat_timestamp ON analytics.fact_chat (timestamp);
    CREATE NONCLUSTERED INDEX IX_fact_chat_is_demo   ON analytics.fact_chat (is_demo);
END
GO

-- =============================================================================
-- FACT: fact_flight_search
-- =============================================================================
IF NOT EXISTS (SELECT 1 FROM sys.objects WHERE object_id = OBJECT_ID(N'analytics.fact_flight_search') AND type = 'U')
BEGIN
    CREATE TABLE analytics.fact_flight_search (
        flight_search_key INT          NOT NULL IDENTITY(1,1),
        user_key          INT          NULL,
        session_id        NVARCHAR(200) NOT NULL,
        trip_key          INT          NULL,
        origin            NVARCHAR(100) NULL,
        destination       NVARCHAR(200) NULL,
        departure_date    DATE         NULL,
        return_date       DATE         NULL,
        passengers        INT          NULL,
        cabin_class       NVARCHAR(50)  NULL,
        results_count     INT          NULL,
        lowest_price      DECIMAL(18,2) NULL,
        currency          NVARCHAR(10)  NULL,
        provider_key      INT          NULL,
        success           BIT          NOT NULL DEFAULT 1,
        latency_ms        INT          NULL,
        timestamp         DATETIME2    NOT NULL DEFAULT SYSDATETIME(),
        data_source       NVARCHAR(20)  NOT NULL DEFAULT 'production',
        is_demo           BIT          NOT NULL DEFAULT 0,
        CONSTRAINT PK_fact_flight PRIMARY KEY CLUSTERED (flight_search_key),
        CONSTRAINT FK_fact_flight_user     FOREIGN KEY (user_key)     REFERENCES analytics.dim_user (user_key),
        CONSTRAINT FK_fact_flight_trip     FOREIGN KEY (trip_key)     REFERENCES analytics.dim_trip (trip_key),
        CONSTRAINT FK_fact_flight_provider FOREIGN KEY (provider_key) REFERENCES analytics.dim_provider (provider_key)
    );
    CREATE NONCLUSTERED INDEX IX_fact_flight_session   ON analytics.fact_flight_search (session_id);
    CREATE NONCLUSTERED INDEX IX_fact_flight_timestamp ON analytics.fact_flight_search (timestamp);
    CREATE NONCLUSTERED INDEX IX_fact_flight_is_demo   ON analytics.fact_flight_search (is_demo);
END
GO

-- =============================================================================
-- FACT: fact_hotel_search
-- =============================================================================
IF NOT EXISTS (SELECT 1 FROM sys.objects WHERE object_id = OBJECT_ID(N'analytics.fact_hotel_search') AND type = 'U')
BEGIN
    CREATE TABLE analytics.fact_hotel_search (
        hotel_search_key INT          NOT NULL IDENTITY(1,1),
        user_key         INT          NULL,
        session_id       NVARCHAR(200) NOT NULL,
        trip_key         INT          NULL,
        destination      NVARCHAR(200) NULL,
        check_in         DATE         NULL,
        check_out        DATE         NULL,
        rooms            INT          NULL,
        travelers        INT          NULL,
        results_count    INT          NULL,
        lowest_price     DECIMAL(18,2) NULL,
        currency         NVARCHAR(10)  NULL,
        provider_key     INT          NULL,
        success          BIT          NOT NULL DEFAULT 1,
        latency_ms       INT          NULL,
        timestamp        DATETIME2    NOT NULL DEFAULT SYSDATETIME(),
        data_source      NVARCHAR(20)  NOT NULL DEFAULT 'production',
        is_demo          BIT          NOT NULL DEFAULT 0,
        CONSTRAINT PK_fact_hotel PRIMARY KEY CLUSTERED (hotel_search_key),
        CONSTRAINT FK_fact_hotel_user     FOREIGN KEY (user_key)     REFERENCES analytics.dim_user (user_key),
        CONSTRAINT FK_fact_hotel_trip     FOREIGN KEY (trip_key)     REFERENCES analytics.dim_trip (trip_key),
        CONSTRAINT FK_fact_hotel_provider FOREIGN KEY (provider_key) REFERENCES analytics.dim_provider (provider_key)
    );
    CREATE NONCLUSTERED INDEX IX_fact_hotel_session   ON analytics.fact_hotel_search (session_id);
    CREATE NONCLUSTERED INDEX IX_fact_hotel_timestamp ON analytics.fact_hotel_search (timestamp);
    CREATE NONCLUSTERED INDEX IX_fact_hotel_is_demo   ON analytics.fact_hotel_search (is_demo);
END
GO

-- =============================================================================
-- FACT: fact_place_search
-- =============================================================================
IF NOT EXISTS (SELECT 1 FROM sys.objects WHERE object_id = OBJECT_ID(N'analytics.fact_place_search') AND type = 'U')
BEGIN
    CREATE TABLE analytics.fact_place_search (
        place_search_key INT          NOT NULL IDENTITY(1,1),
        user_key         INT          NULL,
        session_id       NVARCHAR(200) NOT NULL,
        trip_key         INT          NULL,
        destination      NVARCHAR(200) NULL,
        category         NVARCHAR(100) NULL,
        results_count    INT          NULL,
        provider_key     INT          NULL,
        success          BIT          NOT NULL DEFAULT 1,
        latency_ms       INT          NULL,
        timestamp        DATETIME2    NOT NULL DEFAULT SYSDATETIME(),
        data_source      NVARCHAR(20)  NOT NULL DEFAULT 'production',
        is_demo          BIT          NOT NULL DEFAULT 0,
        CONSTRAINT PK_fact_place PRIMARY KEY CLUSTERED (place_search_key),
        CONSTRAINT FK_fact_place_user     FOREIGN KEY (user_key)     REFERENCES analytics.dim_user (user_key),
        CONSTRAINT FK_fact_place_trip     FOREIGN KEY (trip_key)     REFERENCES analytics.dim_trip (trip_key),
        CONSTRAINT FK_fact_place_provider FOREIGN KEY (provider_key) REFERENCES analytics.dim_provider (provider_key)
    );
    CREATE NONCLUSTERED INDEX IX_fact_place_session   ON analytics.fact_place_search (session_id);
    CREATE NONCLUSTERED INDEX IX_fact_place_timestamp ON analytics.fact_place_search (timestamp);
    CREATE NONCLUSTERED INDEX IX_fact_place_is_demo   ON analytics.fact_place_search (is_demo);
END
GO

-- =============================================================================
-- FACT: fact_weather_search
-- =============================================================================
IF NOT EXISTS (SELECT 1 FROM sys.objects WHERE object_id = OBJECT_ID(N'analytics.fact_weather_search') AND type = 'U')
BEGIN
    CREATE TABLE analytics.fact_weather_search (
        weather_search_key INT          NOT NULL IDENTITY(1,1),
        user_key           INT          NULL,
        session_id         NVARCHAR(200) NOT NULL,
        trip_key           INT          NULL,
        destination        NVARCHAR(200) NULL,
        request_date       DATE         NULL,
        forecast_date      DATE         NULL,
        provider_key       INT          NULL,
        success            BIT          NOT NULL DEFAULT 1,
        latency_ms         INT          NULL,
        timestamp          DATETIME2    NOT NULL DEFAULT SYSDATETIME(),
        data_source        NVARCHAR(20)  NOT NULL DEFAULT 'production',
        is_demo            BIT          NOT NULL DEFAULT 0,
        CONSTRAINT PK_fact_weather PRIMARY KEY CLUSTERED (weather_search_key),
        CONSTRAINT FK_fact_weather_user     FOREIGN KEY (user_key)     REFERENCES analytics.dim_user (user_key),
        CONSTRAINT FK_fact_weather_trip     FOREIGN KEY (trip_key)     REFERENCES analytics.dim_trip (trip_key),
        CONSTRAINT FK_fact_weather_provider FOREIGN KEY (provider_key) REFERENCES analytics.dim_provider (provider_key)
    );
    CREATE NONCLUSTERED INDEX IX_fact_weather_session ON analytics.fact_weather_search (session_id);
    CREATE NONCLUSTERED INDEX IX_fact_weather_is_demo ON analytics.fact_weather_search (is_demo);
END
GO

-- =============================================================================
-- FACT: fact_itinerary
-- =============================================================================
IF NOT EXISTS (SELECT 1 FROM sys.objects WHERE object_id = OBJECT_ID(N'analytics.fact_itinerary') AND type = 'U')
BEGIN
    CREATE TABLE analytics.fact_itinerary (
        itinerary_key      INT          NOT NULL IDENTITY(1,1),
        user_key           INT          NULL,
        session_id         NVARCHAR(200) NOT NULL,
        trip_key           INT          NULL,
        destination        NVARCHAR(200) NULL,
        duration_days      INT          NULL,
        activity_count     INT          NULL,
        generated_at       DATETIME2    NOT NULL DEFAULT SYSDATETIME(),
        generation_time_ms INT          NULL,
        status             NVARCHAR(50)  NOT NULL DEFAULT 'generated',
        data_source        NVARCHAR(20)  NOT NULL DEFAULT 'production',
        is_demo            BIT          NOT NULL DEFAULT 0,
        CONSTRAINT PK_fact_itinerary PRIMARY KEY CLUSTERED (itinerary_key),
        CONSTRAINT FK_fact_itin_user FOREIGN KEY (user_key) REFERENCES analytics.dim_user (user_key),
        CONSTRAINT FK_fact_itin_trip FOREIGN KEY (trip_key) REFERENCES analytics.dim_trip (trip_key)
    );
    CREATE NONCLUSTERED INDEX IX_fact_itin_generated ON analytics.fact_itinerary (generated_at);
    CREATE NONCLUSTERED INDEX IX_fact_itin_is_demo   ON analytics.fact_itinerary (is_demo);
END
GO

-- =============================================================================
-- FACT: fact_agent_execution  (dynamic agent support via dim_agent)
-- =============================================================================
IF NOT EXISTS (SELECT 1 FROM sys.objects WHERE object_id = OBJECT_ID(N'analytics.fact_agent_execution') AND type = 'U')
BEGIN
    CREATE TABLE analytics.fact_agent_execution (
        execution_key INT          NOT NULL IDENTITY(1,1),
        user_key      INT          NULL,
        session_id    NVARCHAR(200) NOT NULL,
        trip_key      INT          NULL,
        agent_key     INT          NULL,
        started_at    DATETIME2    NOT NULL,
        completed_at  DATETIME2    NULL,
        duration_ms   INT          NULL,
        status        NVARCHAR(50)  NOT NULL DEFAULT 'success',
        model         NVARCHAR(100) NULL,
        input_tokens  INT          NULL,
        output_tokens INT          NULL,
        error_type    NVARCHAR(200) NULL,
        data_source   NVARCHAR(20)  NOT NULL DEFAULT 'production',
        is_demo       BIT          NOT NULL DEFAULT 0,
        CONSTRAINT PK_fact_agent_exec PRIMARY KEY CLUSTERED (execution_key),
        CONSTRAINT FK_fact_ae_user  FOREIGN KEY (user_key)  REFERENCES analytics.dim_user (user_key),
        CONSTRAINT FK_fact_ae_trip  FOREIGN KEY (trip_key)  REFERENCES analytics.dim_trip (trip_key),
        CONSTRAINT FK_fact_ae_agent FOREIGN KEY (agent_key) REFERENCES analytics.dim_agent (agent_key)
    );
    CREATE NONCLUSTERED INDEX IX_fact_ae_agent_key  ON analytics.fact_agent_execution (agent_key);
    CREATE NONCLUSTERED INDEX IX_fact_ae_session    ON analytics.fact_agent_execution (session_id);
    CREATE NONCLUSTERED INDEX IX_fact_ae_started_at ON analytics.fact_agent_execution (started_at);
    CREATE NONCLUSTERED INDEX IX_fact_ae_is_demo    ON analytics.fact_agent_execution (is_demo);
END
GO

-- =============================================================================
-- FACT: fact_api_usage  (NO API keys / secrets stored — ever)
-- =============================================================================
IF NOT EXISTS (SELECT 1 FROM sys.objects WHERE object_id = OBJECT_ID(N'analytics.fact_api_usage') AND type = 'U')
BEGIN
    CREATE TABLE analytics.fact_api_usage (
        api_usage_key      INT          NOT NULL IDENTITY(1,1),
        user_key           INT          NULL,
        session_id         NVARCHAR(200) NOT NULL,
        trip_key           INT          NULL,
        provider_key       INT          NULL,
        endpoint           NVARCHAR(500) NULL,
        request_timestamp  DATETIME2    NOT NULL,
        response_timestamp DATETIME2    NULL,
        latency_ms         INT          NULL,
        status_code        INT          NULL,
        success            BIT          NOT NULL DEFAULT 1,
        error_type         NVARCHAR(200) NULL,
        estimated_cost     DECIMAL(18,4) NULL,
        data_source        NVARCHAR(20)  NOT NULL DEFAULT 'production',
        is_demo            BIT          NOT NULL DEFAULT 0,
        CONSTRAINT PK_fact_api PRIMARY KEY CLUSTERED (api_usage_key),
        CONSTRAINT FK_fact_api_user     FOREIGN KEY (user_key)     REFERENCES analytics.dim_user (user_key),
        CONSTRAINT FK_fact_api_trip     FOREIGN KEY (trip_key)     REFERENCES analytics.dim_trip (trip_key),
        CONSTRAINT FK_fact_api_provider FOREIGN KEY (provider_key) REFERENCES analytics.dim_provider (provider_key)
    );
    CREATE NONCLUSTERED INDEX IX_fact_api_provider   ON analytics.fact_api_usage (provider_key);
    CREATE NONCLUSTERED INDEX IX_fact_api_timestamp  ON analytics.fact_api_usage (request_timestamp);
    CREATE NONCLUSTERED INDEX IX_fact_api_is_demo    ON analytics.fact_api_usage (is_demo);
END
GO

-- =============================================================================
-- FACT: fact_error
-- =============================================================================
IF NOT EXISTS (SELECT 1 FROM sys.objects WHERE object_id = OBJECT_ID(N'analytics.fact_error') AND type = 'U')
BEGIN
    CREATE TABLE analytics.fact_error (
        error_key    INT          NOT NULL IDENTITY(1,1),
        user_key     INT          NULL,
        session_id   NVARCHAR(200) NOT NULL,
        trip_key     INT          NULL,
        provider_key INT          NULL,
        agent_key    INT          NULL,
        service      NVARCHAR(200) NULL,
        error_type   NVARCHAR(200) NULL,
        status_code  INT          NULL,
        timestamp    DATETIME2    NOT NULL DEFAULT SYSDATETIME(),
        resolved     BIT          NOT NULL DEFAULT 0,
        data_source  NVARCHAR(20)  NOT NULL DEFAULT 'production',
        is_demo      BIT          NOT NULL DEFAULT 0,
        CONSTRAINT PK_fact_error PRIMARY KEY CLUSTERED (error_key),
        CONSTRAINT FK_fact_err_user     FOREIGN KEY (user_key)     REFERENCES analytics.dim_user (user_key),
        CONSTRAINT FK_fact_err_trip     FOREIGN KEY (trip_key)     REFERENCES analytics.dim_trip (trip_key),
        CONSTRAINT FK_fact_err_provider FOREIGN KEY (provider_key) REFERENCES analytics.dim_provider (provider_key),
        CONSTRAINT FK_fact_err_agent    FOREIGN KEY (agent_key)    REFERENCES analytics.dim_agent (agent_key)
    );
    CREATE NONCLUSTERED INDEX IX_fact_error_timestamp ON analytics.fact_error (timestamp);
    CREATE NONCLUSTERED INDEX IX_fact_error_is_demo   ON analytics.fact_error (is_demo);
END
GO

-- =============================================================================
-- SEED: dim_date 2024-01-01 to 2027-12-31
-- =============================================================================
IF NOT EXISTS (SELECT 1 FROM analytics.dim_date WHERE date_key = 20240101)
BEGIN
    DECLARE @d DATE = '2024-01-01';
    DECLARE @e DATE = '2027-12-31';
    WHILE @d <= @e
    BEGIN
        INSERT INTO analytics.dim_date (date_key,full_date,year,quarter,month,month_name,week,day,day_name,is_weekend)
        VALUES (
            CAST(FORMAT(@d,'yyyyMMdd') AS INT), @d,
            YEAR(@d), DATEPART(QUARTER,@d), MONTH(@d), DATENAME(MONTH,@d),
            DATEPART(ISO_WEEK,@d), DAY(@d), DATENAME(WEEKDAY,@d),
            CASE WHEN DATEPART(WEEKDAY,@d) IN (1,7) THEN 1 ELSE 0 END
        );
        SET @d = DATEADD(DAY,1,@d);
    END
END
GO

-- =============================================================================
-- SEED: dim_agent (TravelOS agents — add more here as needed)
-- =============================================================================
IF NOT EXISTS (SELECT 1 FROM analytics.dim_agent WHERE agent_name='OrchestratorAgent')
    INSERT INTO analytics.dim_agent (agent_name,agent_type,agent_version,is_active) VALUES('OrchestratorAgent','orchestrator','1.0',1);
IF NOT EXISTS (SELECT 1 FROM analytics.dim_agent WHERE agent_name='ResearchAgent')
    INSERT INTO analytics.dim_agent (agent_name,agent_type,agent_version,is_active) VALUES('ResearchAgent','specialist','1.0',1);
IF NOT EXISTS (SELECT 1 FROM analytics.dim_agent WHERE agent_name='HotelAgent')
    INSERT INTO analytics.dim_agent (agent_name,agent_type,agent_version,is_active) VALUES('HotelAgent','specialist','1.0',1);
IF NOT EXISTS (SELECT 1 FROM analytics.dim_agent WHERE agent_name='ActivityAgent')
    INSERT INTO analytics.dim_agent (agent_name,agent_type,agent_version,is_active) VALUES('ActivityAgent','specialist','1.0',1);
IF NOT EXISTS (SELECT 1 FROM analytics.dim_agent WHERE agent_name='ItineraryAgent')
    INSERT INTO analytics.dim_agent (agent_name,agent_type,agent_version,is_active) VALUES('ItineraryAgent','specialist','1.0',1);
IF NOT EXISTS (SELECT 1 FROM analytics.dim_agent WHERE agent_name='BudgetAgent')
    INSERT INTO analytics.dim_agent (agent_name,agent_type,agent_version,is_active) VALUES('BudgetAgent','specialist','1.0',1);
GO

-- =============================================================================
-- SEED: dim_provider (external API providers)
-- =============================================================================
IF NOT EXISTS (SELECT 1 FROM analytics.dim_provider WHERE provider_name='Duffel')
    INSERT INTO analytics.dim_provider (provider_name,provider_type) VALUES('Duffel','flights');
IF NOT EXISTS (SELECT 1 FROM analytics.dim_provider WHERE provider_name='RouteStack')
    INSERT INTO analytics.dim_provider (provider_name,provider_type) VALUES('RouteStack','hotels');
IF NOT EXISTS (SELECT 1 FROM analytics.dim_provider WHERE provider_name='Geoapify')
    INSERT INTO analytics.dim_provider (provider_name,provider_type) VALUES('Geoapify','geo');
IF NOT EXISTS (SELECT 1 FROM analytics.dim_provider WHERE provider_name='Open-Meteo')
    INSERT INTO analytics.dim_provider (provider_name,provider_type) VALUES('Open-Meteo','weather');
IF NOT EXISTS (SELECT 1 FROM analytics.dim_provider WHERE provider_name='Google Gemini')
    INSERT INTO analytics.dim_provider (provider_name,provider_type) VALUES('Google Gemini','llm');
IF NOT EXISTS (SELECT 1 FROM analytics.dim_provider WHERE provider_name='MapTiler')
    INSERT INTO analytics.dim_provider (provider_name,provider_type) VALUES('MapTiler','maps');
GO

PRINT 'Migration 001 complete: schema, dimensions, facts, indexes, seeds.';
GO
