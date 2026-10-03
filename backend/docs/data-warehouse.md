# TravelOS — Production Microsoft SQL Server Data Warehouse & Tableau Analytics Guide

## 1. Executive Summary & Architecture Overview

TravelOS incorporates an enterprise-grade **Microsoft SQL Server Data Warehouse** and **Tableau Analytics layer**. Designed as an additive, decoupled analytical repository, it captures operational telemetry, agent execution traces, external provider API performance, search demands, and customer journey funnels without introducing latency or stability risks to the primary FastAPI / LangGraph runtime.

### Architectural Principles

1. **Non-Blocking Telemetry Ingestion**: All operational event emissions from LangGraph nodes and orchestrators run in isolated execution blocks (`try/except`). If SQL Server is undergoing maintenance or temporarily unreachable, TravelOS functions seamlessly without dropped requests or user degradation.
2. **Strict Separation of Concerns**: The operational application continues to run FastAPI, LangGraph, and in-memory FAISS vector indexing. The data warehouse is an analytical sink designed specifically for OLAP aggregations, business intelligence, and Tableau reporting.
3. **Data Provenance & Isolation**: Every record in the warehouse includes `is_demo` (`BIT`) and `data_source` (`NVARCHAR(20)`) columns. Production data and synthetic test/demo datasets live side-by-side cleanly, allowing single-click filtering in Tableau (`WHERE is_demo = 0` for live production audits, `WHERE is_demo = 1` for executive demonstrations).
4. **Direct Tableau Integration**: Leverages Microsoft SQL Server's native TDS protocol, standard views in the `analytics` schema, and a dedicated least-privilege, read-only SQL Server user (`travelos_tableau_reader`).

```
+-----------------------------------------------------------------------------------+
|                            TRAVELOS RUNTIME LAYER                                |
|  [FastAPI] ---> [LangGraph StateGraph] ---> [Agents: Orchestrator, Hotel, etc.]   |
|                         | (Non-blocking async telemetry)                          |
+-------------------------|---------------------------------------------------------+
                          v
+-----------------------------------------------------------------------------------+
|                        ANALYTICS INGESTION SERVICE                                |
|  [app.analytics.analytics_events] ---> [analytics_repository]                     |
|                                       | (pyodbc connection pool)                  |
+---------------------------------------|-------------------------------------------+
                                        v
+-----------------------------------------------------------------------------------+
|                 MICROSOFT SQL SERVER (TravelOS_Analytics DB)                      |
|                                                                                   |
|  [Dimension Tables]          [Fact Tables]               [Tableau Views]         |
|  - dim_date                  - fact_session              - v_monthly_trip_growth |
|  - dim_user                  - fact_chat                 - v_user_trip_summary   |
|  - dim_destination           - fact_flight_search        - v_destination_pop...  |
|  - dim_agent                 - fact_hotel_search         - v_agent_performance   |
|  - dim_provider              - fact_place_search         - v_api_usage           |
|  - dim_trip                  - fact_weather_search       - v_trip_conversion     |
|                              - fact_itinerary            - v_error_summary       |
|                              - fact_agent_execution      - v_user_engagement     |
|                              - fact_api_usage                                    |
|                              - fact_error                                        |
+-----------------------------------------------------------------------------------+
                                        | (TDS Port 1433 / SELECT only)
                                        v
+-----------------------------------------------------------------------------------+
|                           TABLEAU ANALYTICS SUITE                                 |
|  [1. Executive KPI]      [2. Destination Matrix]    [3. AI Agent Latency]         |
|  [4. Provider SLAs]      [5. Conversion Funnel]     [6. Error Root-Cause]         |
+-----------------------------------------------------------------------------------+
```

---

## 2. SQL Server Dimensional Model (Star Schema)

The warehouse utilizes a Kimball-style dimensional star schema optimized for fast query response times, window functions, and Tableau data source relationships.

### Dimension Tables

| Dimension | Primary Key | Business Key | Description |
|-----------|-------------|--------------|-------------|
| `analytics.dim_date` | `date_key` (INT, `YYYYMMDD`) | `full_date` (DATE) | Calendar dimension covering year, quarter, month, week, day, weekend flags. |
| `analytics.dim_user` | `user_key` (INT, IDENTITY) | `user_id` (NVARCHAR) | Unique users/anonymous actors with platform and acquisition channel. |
| `analytics.dim_destination` | `destination_key` (INT) | `destination_name` | City/Country metadata with geographic coordinates for Tableau maps. |
| `analytics.dim_agent` | `agent_key` (INT) | `agent_name` | TravelOS LangGraph agents (Orchestrator, Research, Hotel, Activity, Itinerary, Budget). |
| `analytics.dim_provider` | `provider_key` (INT) | `provider_name` | External providers (Duffel, RouteStack, Geoapify, MapTiler, Open-Meteo, Gemini). |
| `analytics.dim_trip` | `trip_key` (INT, IDENTITY) | `session_id` | Planned, completed, or abandoned trip specifications and budget ranges. |

### Fact Tables

| Fact Table | Grain | Key Foreign Keys | Key Metrics |
|------------|-------|------------------|-------------|
| `analytics.fact_session` | 1 row per conversation session | `user_key`, `date_key` | `duration_seconds`, `message_count`, `itinerary_generated` |
| `analytics.fact_chat` | 1 row per message | `session_key`, `user_key`, `trip_key` | `message_length`, `latency_ms` |
| `analytics.fact_flight_search` | 1 row per flight query | `session_key`, `destination_key`, `provider_key` | `passengers`, `results_count`, `lowest_price`, `latency_ms` |
| `analytics.fact_hotel_search` | 1 row per hotel search | `session_key`, `destination_key`, `provider_key` | `rooms`, `travelers`, `results_count`, `lowest_price`, `latency_ms` |
| `analytics.fact_place_search` | 1 row per activity query | `session_key`, `destination_key`, `provider_key` | `results_count`, `latency_ms` |
| `analytics.fact_weather_search` | 1 row per weather query | `session_key`, `destination_key`, `provider_key` | `latency_ms` |
| `analytics.fact_itinerary` | 1 row per synthesized plan | `session_key`, `destination_key`, `trip_key` | `duration_days`, `activity_count`, `generation_time_ms` |
| `analytics.fact_agent_execution`| 1 row per agent node run | `session_key`, `agent_key`, `date_key` | `duration_ms`, `input_tokens`, `output_tokens`, `status` |
| `analytics.fact_api_usage` | 1 row per outbound HTTP call | `session_key`, `provider_key`, `date_key` | `latency_ms`, `status_code`, `estimated_cost` |
| `analytics.fact_error` | 1 row per system/provider fault| `session_key`, `provider_key`, `agent_key` | `status_code`, `error_type` |

---

## 3. Database Deployment & Migration Guide

### Prerequisites
- Microsoft SQL Server 2019, 2022, or Azure SQL Database
- SQL Server Management Studio (SSMS), Azure Data Studio, or `sqlcmd`
- Microsoft ODBC Driver 17 or 18 for SQL Server installed on host machine
- Python 3.10+ with `pyodbc` package installed

### Execution Steps

#### Step 1: Create Database
In SSMS or `sqlcmd`:
```sql
CREATE DATABASE TravelOS_Analytics;
GO
```

#### Step 2: Run DDL Migrations
Execute the provided SQL files in numerical order:
1. `backend/analytics/sql/001_create_schema.sql`:
   - Creates the `analytics` schema.
   - Instantiates all dimension and fact tables.
   - Builds nonclustered covering indexes for high-volume analytics queries.
2. `backend/analytics/sql/002_create_views.sql`:
   - Instantiates 13 analytical views for Tableau dashboards.
3. `backend/analytics/sql/003_create_tableau_user.sql`:
   - Creates `travelos_tableau_reader` SQL login and user.
   - Explicitly grants `SELECT` and strictly `DENY`s write permissions.

#### Step 3: Configure Environment Variables
Update `backend/.env` with your SQL Server parameters:
```env
ANALYTICS_ENABLED=true
SQL_SERVER_HOST=localhost
SQL_SERVER_PORT=1433
SQL_SERVER_DATABASE=TravelOS_Analytics
SQL_SERVER_USER=sa
SQL_SERVER_PASSWORD=YourSecurePassword123!
SQL_SERVER_ODBC_DRIVER=ODBC Driver 17 for SQL Server
```

#### Step 4: Seed Demo Data
To populate the warehouse with realistic data without calling external APIs:
```bash
python scripts/seed_analytics_demo.py
```
*(Use `python scripts/seed_analytics_demo.py --clean` if you wish to reset and re-seed).*

#### Step 5: Run Automated Data Quality Checks
Execute `backend/analytics/sql/data_quality_checks.sql` in SSMS to verify zero orphans, full referential integrity, and correct view schemas.

---

## 4. Tableau Desktop & Server Connection Guide

### Connection Configuration
1. Open **Tableau Desktop**.
2. Under **Connect > To a Server**, select **Microsoft SQL Server**.
3. Fill in connection details:
   - **Server**: `<your_server_host>,1433` (e.g. `localhost,1433` or Azure SQL endpoint)
   - **Database**: `TravelOS_Analytics`
   - **Authentication**: `Username and Password`
   - **Username**: `travelos_tableau_reader`
   - **Password**: `<your_configured_reader_password>`
   - **Require SSL / Encrypt**: Enabled (recommended)

### Recommended Data Source Strategies

#### Option A: Direct Analytical Views (Recommended for Rapid Dashboards)
Drag the pre-aggregated views from schema `analytics` directly onto the canvas:
- `v_monthly_trip_growth` -> Executive Scorecard
- `v_destination_popularity` -> Destination Demand Heatmap
- `v_agent_performance` -> AI Orchestration Benchmarks
- `v_api_usage` & `v_error_summary` -> Infrastructure & Cost SLA
- `v_trip_conversion` -> Marketing & Conversion Funnel

#### Option B: Star Schema Logical Model (For Deep Slice & Dice)
1. Add `analytics.fact_session` as the central fact table.
2. Form relationships (noodles) to:
   - `analytics.dim_date` on `date_key`
   - `analytics.dim_user` on `user_key`
   - `analytics.dim_trip` on `session_id = session_id`
3. Add secondary logical tables for `fact_agent_execution` linked to `dim_agent`.

---

## 5. Tableau Dashboard Design Blueprints

### Dashboard 1: Executive KPI & Revenue Feasibility
- **Target Audience**: Product Leadership, General Manager, Executives
- **Key Visualizations**:
  - **KPI Scorecards**: Total Sessions, Unique Travelers, Generated Itineraries, Conversion Rate (%).
  - **Monthly Growth Curve**: Dual-axis line/bar chart displaying session volume vs. completed trips over time (`v_monthly_trip_growth`).
  - **Budget Allocation Donut**: Average user budget distribution across Low, Mid, and Luxury tiers.
  - **Top 5 Desired Destinations**: Ranked horizontal bar chart.

### Dashboard 2: Destination Demand & Geolocation Map
- **Target Audience**: Business Development, Inventory Sourcing, Partnerships
- **Key Visualizations**:
  - **Global Demand Heatmap**: Tableau Symbol Map using `latitude` and `longitude` from `v_destination_popularity`, sized by search volume and colored by average hotel price.
  - **Flight vs. Hotel Inquiry Volume**: Side-by-side bar chart showing interest ratios per city.
  - **Search Seasonality**: Heat matrix (Month of Travel vs Destination).

### Dashboard 3: AI Multi-Agent Performance & Latency
- **Target Audience**: AI Engineers, Platform Architects
- **Key Visualizations**:
  - **Agent Latency Profile**: Box-and-whisker plot or bar chart comparing `avg_duration_ms`, `p90`, and `p95` across agents (`OrchestratorAgent`, `HotelAgent`, etc.).
  - **Token Consumption**: Stacked area chart showing total input/output tokens over time.
  - **Success SLA Gauge**: Bullet graph indicating the 99% uptime/success SLA per agent.

### Dashboard 4: External API Provider SLAs & Cost Allocation
- **Target Audience**: DevOps, Finance, Infrastructure Operations
- **Key Visualizations**:
  - **Provider Availability Matrix**: Percentage of HTTP 200 vs 4xx/5xx responses for Duffel, RouteStack, Geoapify, Gemini.
  - **API Latency Distribution**: Line chart with historical spikes and benchmark bands.
  - **Estimated Operational Cost**: Cumulative cost breakdown by provider ($ USD).

### Dashboard 5: Customer Journey & Conversion Funnel
- **Target Audience**: Growth Team, UX Researchers, Product Managers
- **Key Visualizations**:
  - **Step-by-Step Funnel**: Funnel chart from `Session Started` -> `Search Performed` -> `Itinerary Synthesized` -> `Trip Completed`.
  - **Drop-off Analysis**: Identification of stages where user engagement halts.
  - **Platform Engagement Breakdown**: Session duration and message counts segmented by Web, iOS, and Android platforms.

### Dashboard 6: System Error Root-Cause & Fallback Diagnostics
- **Target Audience**: Reliability Engineering (SRE), Support Leads
- **Key Visualizations**:
  - **Error Incident Timeline**: Spike detection chart grouping incidents by hour/day.
  - **Root Cause Pareto**: Tree-map or Pareto chart categorizing `HTTP_429_RateLimit`, `ExecutionTimeout`, etc.
  - **Service Failure Correlation**: Heatmap linking errors to specific agents or external providers.

---

## 6. Maintenance, Partitioning & Operations

### Backup Strategy
1. **Full Backups**: Weekly full database backup.
2. **Differential Backups**: Daily differential backup.
3. **Transaction Log Backups**: Every 1-2 hours if database is in `FULL` recovery mode, or maintain in `SIMPLE` recovery mode if analytics can be recreated via ETL replays.

### Index Maintenance
For high data volumes (> 1M rows), run periodic index defragmentation:
```sql
ALTER INDEX ALL ON analytics.fact_session REORGANIZE;
ALTER INDEX ALL ON analytics.fact_agent_execution REORGANIZE;
```

### Segregating Demo vs. Production Data
To purge synthetic data after a demonstration or testing cycle without impacting production metrics:
```sql
EXEC('DELETE FROM analytics.fact_error WHERE is_demo = 1');
EXEC('DELETE FROM analytics.fact_api_usage WHERE is_demo = 1');
EXEC('DELETE FROM analytics.fact_agent_execution WHERE is_demo = 1');
EXEC('DELETE FROM analytics.fact_itinerary WHERE is_demo = 1');
EXEC('DELETE FROM analytics.fact_session WHERE is_demo = 1');
EXEC('DELETE FROM analytics.dim_trip WHERE is_demo = 1');
EXEC('DELETE FROM analytics.dim_user WHERE is_demo = 1');
```
Production rows (`is_demo = 0`, `data_source = 'production'`) remain untouched.
