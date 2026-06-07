## Project Description

Batch energy analytics pipeline built on AWS using the Ember Monthly Electricity API.
The system ingests monthly electricity generation data for 8 European countries, transforms it through AWS Glue into columnar Parquet, and visualizes production trends and energy mix through an Amazon QuickSight dashboard.

---

## Project Structure

```
aws-data-engineering-project/
├── src/           # Python ingestion scripts
├── infra/         # Infrastructure-as-code (placeholder)
├── notebooks/     # Exploratory analysis (placeholder)
├── data/          # Local raw data (gitignored)
│   └── raw/ember/electricity_generation/monthly/
├── skills/        # Reusable skill documentation (10 skills)
├── .env           # Local secrets (gitignored)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Final Architecture

| Service | Role |
|---------|------|
| Amazon S3 | Raw and processed data lake (two buckets) |
| AWS Glue ETL | JSON → Parquet transformation with Explode + Flatten |
| AWS Glue Crawler | Auto-discovers schema from processed Parquet |
| AWS Glue Data Catalog | Central metadata store (`ember_energy_db`) |
| Amazon Athena | SQL validation and ad-hoc analytics |
| Amazon QuickSight | Interactive dashboard: stacked area chart, KPI cards, geographic map |

---

## Final Data Flow

```
Ember Energy API
→ Python Ingestion Script (src/ingest_ember_data.py)
→ Amazon S3 Raw Bucket (JSON, partitioned by extraction_date=YYYY-MM-DD)
→ AWS Glue ETL Job (EmberGlueETLJob-v1)
   → Explode Array Or Map Into Rows
   → Flatten Nested Fields
   → Parquet / Snappy output
→ Amazon S3 Processed Bucket
→ AWS Glue Crawler (EmberProcessedDataCrawler)
→ AWS Glue Data Catalog (ember_energy_db)
→ Amazon Athena (SQL validation + analytics)
→ Amazon QuickSight Dashboard
```

### Network Diagram
https://miro.com/app/board/uXjVHS6eY4g=/?moveToWidget=3458764672103169096&cot=14

---

## Service Setup

### Amazon S3

Two buckets, both in `eu-central-1` (Frankfurt).

**Raw bucket:** `ember-energy-raw-data-v1-759302162548-eu-central-1-an`

| Setting | Value |
|---------|-------|
| Block all public access | On |
| ACLs | Disabled (bucket owner enforced) |
| Versioning | Off |
| Default encryption | SSE-S3 |
| Bucket Key | On |

**S3 partition structure:**
```
raw/ember/electricity_generation/monthly/extraction_date=YYYY-MM-DD/<filename>.json
```

### IAM Role

**Role name:** `GlueETLRole-EmberEnergyProject`

Attached policies:
- `AmazonS3FullAccess`
- `AWSGlueServiceRole`
- `CloudWatchLogsFullAccess`

Trust policy: allows `glue.amazonaws.com` to assume the role.

### AWS Glue ETL Job

**Job name:** `EmberGlueETLJob-v1`

Transform pipeline:
1. Amazon S3 Raw Source (JSON)
2. Explode Array Or Map Into Rows — expands `data[]` array into individual `record` rows
3. Flatten — promotes `record.*` fields to top-level columns (`record.entity`, `record.date`, etc.)
4. Amazon S3 Processed Target

Output: Parquet format, Snappy compression.

### AWS Glue Crawler

**Crawler name:** `EmberProcessedDataCrawler`

- Source: processed S3 bucket prefix
- Target database: `ember_energy_db`
- Schedule: on demand
- Run after each ETL job execution to update the catalog table

### Amazon Athena

- Data source: `AwsDataCatalog`
- Database: `ember_energy_db`
- Query results stored in a dedicated S3 results bucket
- Used for data quality validation after each pipeline run

### Amazon QuickSight

1. Security & Permissions → authorize QuickSight to access Amazon Athena and both S3 buckets
2. New dataset → Athena → select `ember_energy_db` and the catalog table
3. In the dataset editor: change the date column type from string to `Date` with format `yyyy-MM-dd`
4. Import to SPICE for faster dashboard queries
5. Publish dashboard with interactive Country and Energy Source filter controls

---

## Environment Setup

Create a `.env` file at the project root with:

```
EMBER_API_KEY=
S3_RAW_BUCKET=
AWS_REGION=
```

Install dependencies and run:

```bash
pip install -r requirements.txt
python src/ingest_ember_data.py
```

Requires AWS credentials configured locally (`aws configure` or `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` environment variables).

---

## Data Source

This project uses the Ember Monthly Electricity Dataset:
https://ember-energy.org/data/monthly-electricity-data/

This dataset contains monthly generation, emissions and demand data for 88 geographies representing more than 90% of global power demand. Data is collected from multi-country datasets (EIA, Eurostat, Energy Institute) as well as national sources (e.g. China data from the National Bureau of Statistics).

The data is updated twice a month with an update in the first week of the month followed by a second update in the third week of the month.

**Countries ingested:** DEU, FRA, CHE, ITA, ESP, POL, BEL, NLD

**Energy sources:** Solar, Wind, Hydro, Bioenergy, Nuclear, Coal, Gas

**Metrics:** `generation_twh` (absolute output), `share_of_generation_pct` (% of total mix)

**Date range:** 2020-01 to 2026-04

---

## AWS Budget

Monthly budget cap: $50 USD (configured in AWS Budgets).

---

## Challenges & Fixes

### Nested JSON Not Queryable in Athena

**Symptom:** After the first Glue ETL run, Athena returned struct-typed columns (`array<struct<...>>`) instead of scalar values. Standard SQL queries like `SELECT entity FROM table` failed.

**Root cause:** The Ember API response wraps all records inside a `data` array. Glue wrote this array as-is into Parquet without expanding it, so the `data` column remained a nested struct.

**Fix:**
1. Glue Studio → open `EmberGlueETLJob-v1`
2. Add transform: **Explode Array Or Map Into Rows** — source column `data`, output column `record`
3. Add transform: **Flatten** — promotes `record.entity`, `record.date`, etc. to top-level columns
4. Save and re-run the job
5. Delete old processed files in S3, then re-run the Glue Crawler to refresh the catalog table

---

### Duplicate Records After Re-ingestion

**Symptom:** Athena data quality check (`GROUP BY entity_code, date, series HAVING COUNT(*) > 1`) returned rows — duplicate records existed in the processed dataset.

**Root cause:** Multiple ingestion runs wrote JSON files to different `extraction_date=` S3 partitions for the same time period. The Glue ETL job scanned all raw partitions and appended output to the processed bucket, producing duplicate rows.

**Fix:**
1. Delete all objects in the processed S3 bucket prefix
2. Delete the corresponding Glue Data Catalog table
3. Remove obsolete raw S3 partitions containing overlapping data
4. Re-run `EmberGlueETLJob-v1` against the clean raw data
5. Re-run `EmberProcessedDataCrawler` to regenerate the catalog table
6. Re-validate in Athena — duplicate check should return zero rows

---

## Lessons Learned

- Glue visual ETL does not auto-flatten nested API responses — Explode + Flatten transforms must be added explicitly for any JSON with a nested array
- Hive-style partition keys (`extraction_date=YYYY-MM-DD`) enable Athena partition pruning but also cause duplicate data if overlapping date ranges are re-ingested without clearing the processed layer first
- QuickSight silently breaks time-axis charts when date columns are typed as strings — always change to `Date` with format `yyyy-MM-dd` in the dataset editor before importing
- QuickSight's Athena and S3 access permissions are configured inside QuickSight's own Security & Permissions console — they are separate from AWS IAM and easy to miss during initial setup

---

## Future Improvements

### Infrastructure
- Terraform or AWS CDK for all resources (currently all manual console setup)
- Version-suffix resource names when schema changes (`EmberGlueETLJob-v2`, `ember-index-v2`)

### Orchestration
- AWS EventBridge Scheduler or Apache Airflow to automate ingestion + ETL on a monthly cadence
- CloudWatch alarms for Glue job failures and data freshness SLA breaches

### Analytics
- Jupyter notebooks in `notebooks/` for exploratory analysis and statistical summaries
- Athena saved queries for reusable data quality checks

### Data
- Expand to more countries or time periods
- Ingest Ember demand and emissions datasets alongside generation data

### Dashboards
- Additional QuickSight sheets: year-over-year comparison, renewable share trend
- Embed dashboard in a web application using QuickSight embedding API

### ML Extensions
- Anomaly detection on monthly generation using SageMaker or OpenSearch ML
- Forecast next 6 months of generation per energy source

---

## Project Progress

### 20260519
#### Initial Infrastructure Setup
- Created initial AWS S3 raw data bucket
- Region: eu-central-1 (Frankfurt)
- Public access blocked
- ACL (Access Control List) disabled
- Bucket versioning disabled
- Default Encryption: SSE-S3 (Server-side encryption with Amazon S3 managed keys)
- Bucket Key enabled

### 20260520

- Set up a local Python development environment using a virtual environment (.venv)
- Configured dependency management with requirements.txt
- Implemented an ingestion pipeline for the Ember Energy API
- Successfully connected to the Ember API using an API key stored securely in a .env file
- Retrieved monthly electricity generation data for selected countries and technologies
- Stored raw API responses locally in JSON format following a data lake folder structure
- Added detailed code comments and documentation for maintainability
- Configured .gitignore to exclude:
  - local raw data files
  - environment variables and secrets
  - virtual environments
  - temporary and log files
- Cleaned the Git repository by removing tracked local data and sensitive files
- Successfully tested the ingestion script with HTTP Status Code 200
- Pushed the updated project structure and ingestion pipeline to GitHub

### 20260521

- Verified local AWS authentication and connectivity using AWS CLI
- Confirmed successful IAM user access with `aws sts get-caller-identity`
- Updated the `.env` configuration with:
  - S3 bucket name
  - AWS region
- Extended the Python ingestion script to support:
  - local JSON storage
  - S3 uploads using `boto3`
- Implemented structured S3 object partitioning:
  - source
  - dataset
  - frequency
  - year/month partitions
- Successfully uploaded Ember electricity generation data to the S3 raw bucket
- Validated uploaded objects directly inside the AWS S3 Console
- S3 object structure: raw/ember/electricity_generation/monthly/year=2026/month=04/

Created/configured IAM role for AWS Glue permissions
role name:
- GlueETLRole-EmberEnergyProject

permissions:
- AmazonS3FullAccess
- AWSGlueServiceRole
- CloudWatchLogFullAccess

Created first AWS Glue ETL Job:
- EmberGlueETLJob-v1

Configured ETL workflow:
Amazon S3 Raw Source
- Transform Raw Energy Data
- Amazon S3 Processed Target

Configured processed output:
- Format: Parquet
- Compression: Snappy

Processed Data Target
- Configured Glue target location in Processed S3 bucket for analytics-ready datasets.

### 20260523
- Successfully executed first AWS Glue ETL job
- Transformed raw JSON energy data into Parquet format
- Stored transformed output in processed S3 bucket
- Validated IAM permissions and Glue runtime configuration
- Confirmed end-to-end ETL pipeline functionality

### 20260523
- Created AWS Glue Crawler (`EmberProcessedDataCrawler`)
- Connected crawler to processed Parquet dataset
- Created Glue Data Catalog database (`ember_energy_db`)
- Automatically generated catalog table from processed data

### 20260523
Successfully queried processed parquet dataset using Amazon Athena.

Observation: The current dataset still contains nested JSON/object structures inside the `stats` column. Next step:
Explode and Flatten nested API response structures into analytics-ready relational columns using AWS Glue transformations.

Data Transformation Improvements

Observation
The initial processed dataset still contained nested JSON structures inside the `data` column, which made analytical querying in Amazon Athena difficult.

Solution
To transform the nested API response into an analytics-ready tabular structure, the AWS Glue ETL pipeline was updated with additional transformation steps:

1. **Explode Array Or Map Into Rows**
   - The nested `data` array from the Ember API response was exploded into individual records.
   - A new column named `record` was created for each array element.

2. **Flatten Transformation**
   - The nested fields inside the `record` object were flattened into relational columns.
   - Example output columns:
     - `record.entity`
     - `record.entity_code`
     - `record.date`
     - `record.series`

Result
The processed dataset can now be queried efficiently in Amazon Athena using standard SQL statements instead of working with nested JSON structures.

### 20260524
Expanded Dataset Ingestion & Athena Validation

API Ingestion Improvements
- Updated the Ember API ingestion script to request larger datasets across multiple countries and energy generation series.
- Extended API parameters:
  - Multiple `entity_code` values
  - Multiple `series` values
  - Expanded historical date range

S3 Raw Layer Improvements
- Implemented dynamic S3 partition-style prefixes using extraction dates:
  ```text
  raw/ember/electricity_generation/monthly/extraction_date=YYYY-MM-DD/
  ```

### 20260524
Data Quality Validation:
The processed dataset was validated using Amazon Athena SQL queries.

Validation checks included:
- null value detection
- duplicate record detection
- date range validation
- record count verification

During validation, duplicate records were identified due to overlapping ingestion batches stored in different S3 raw partitions. The issue was resolved by cleaning obsolete raw and processed files and rerunning the Glue ETL pipeline and rerunning the Glue Crawler Job.

Final validation confirmed:
- no duplicate records
- valid date formats
- successful ingestion and transformation pipeline execution

### 20260525
Dashboard Progress Update

Today, the AWS QuickSight dashboard was successfully connected to the processed energy dataset stored in Amazon S3 and queried through Amazon Athena.

Completed Features
- Configured AWS QuickSight access permissions
- Connected Athena and S3 datasets to QuickSight
- Fixed date formatting issues in the dataset preparation step
- Created interactive line chart visualizing European energy production trends
- Added dynamic filters:
  - Country filter
  - Energy source filter
- Built KPI cards for:
  - Total Energy Production (TWh)
  - Number of Countries
  - Number of Energy Sources
- Improved dashboard layout and visual organization
- Published the first dashboard version in Amazon QuickSight

Current Dashboard Insights
The dashboard currently allows users to:
- Explore energy generation trends over time
- Compare different energy sources
- Filter by specific countries and energy categories
- View high-level production metrics   
