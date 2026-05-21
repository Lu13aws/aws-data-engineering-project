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

#### S3 Object Structure
raw/ember/electricity_generation/monthly/year=2026/month=04/





    
