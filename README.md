## Project Description: 
Part of this project is the retrieval, ingestion, transformation and analysis of data using certain AWS services. This file documents my AWS data engineering journey.

### Project Structure

- `src/`
  - python ingestion scripts 
- `infra/`
  - infrastructure configuration
- `notebooks/`
  - future data exploration and analysis

### Environment Setup

Configured:
- `.env` file for API key management
- `requirements.txt` for Python dependencies

### Python Dependencies

- requests
- boto3
- python-dotenv


### AWS Budget Plan
Created budget plan on aws. set monthly budget = 50 US Dollar

## Network Diagramm
https://miro.com/app/board/uXjVHS6eY4g=/?moveToWidget=3458764672103169096&cot=14

## Data Source
this project uses the Ember Monthly Electricity Dataset:
https://ember-energy.org/data/monthly-electricity-data/
This dataset contains monthly generation, emissions and demand data for 88 geographies representing more than 90% of global power demand. Data is collected from multi-country datasets (EIA, Eurostat, Energy Institute) as well as national sources (e.g China data from the National Bureau of Statistics).

The data is updated twice a month with an update in the first week of the month followed by a second update in the third week of the month.

## Project Progress 
### 20260519
#### Initial Infrastructure Setup
- Created initial AWS S3 raw data bucket
- Region: eu-central-1 (Frankfurt)
- Public access blocked
- ACL (Access Control List) disabled
- Bucket versioning disabled
- Default Encryption: SSE-S3 (Server-side encryption with Amazon S3 managed keys
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
