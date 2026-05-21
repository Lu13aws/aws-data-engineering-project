import os
import json
from datetime import datetime
from pathlib import Path

import boto3
import requests
from dotenv import load_dotenv


# Base URL for the Ember API
BASE_URL = "https://api.ember-energy.org/v1"

# Specific endpoint for monthly electricity generation data
ENDPOINT = "/electricity-generation/monthly"


def main():
    # Load environment variables from the .env file
    load_dotenv()

    # Read values from environment variables
    api_key = os.getenv("EMBER_API_KEY")
    s3_bucket = os.getenv("S3_RAW_BUCKET")
    aws_region = os.getenv("AWS_REGION")

    # Stop the program if required environment variables are missing
    if not api_key:
        raise ValueError("EMBER_API_KEY was not found. Check your .env file.")

    if not s3_bucket:
        raise ValueError("S3_RAW_BUCKET was not found. Check your .env file.")

    if not aws_region:
        raise ValueError("AWS_REGION was not found. Check your .env file.")

    # Define query parameters for the Ember API request
    params = {
        "entity_code": ["DEU", "FRA", "CHE"],  # Germany, France, Switzerland
        "series": ["Solar", "Wind"],          # Electricity generation sources
        "start_date": "2025-04",
        "end_date": "2026-04",
        "is_aggregate_series": "false",
        "api_key": api_key                    # Ember expects the API key as query parameter
    }

    # Build the full API URL
    url = f"{BASE_URL}{ENDPOINT}"

    print("Sending request to Ember API...")
    print(f"URL: {url}")

    # Send GET request to the Ember API
    response = requests.get(url, params=params, timeout=30)

    # Print HTTP status code
    print(f"Status code: {response.status_code}")

    # Stop script if the API request failed
    response.raise_for_status()

    # Convert API response to JSON
    data = response.json()

    # Create timestamp for unique file naming
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Define local output directory
    output_dir = Path("data/raw/ember/electricity_generation/monthly")

    # Create local folder structure if it does not exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Define local output file path
    file_path = output_dir / f"ember_monthly_generation_{timestamp}.json"

    # Save JSON response locally
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

    print(f"Data successfully saved locally to: {file_path}")

    # Create S3 client
    s3_client = boto3.client("s3", region_name=aws_region)

    # Define S3 object key
    s3_key = (
        "raw/ember/electricity_generation/monthly/"
        "year=2026/month=04/"
        f"{file_path.name}"
    )

    # Upload local JSON file to S3 raw bucket
    s3_client.upload_file(
        Filename=str(file_path),
        Bucket=s3_bucket,
        Key=s3_key
    )

    print(f"File successfully uploaded to S3 bucket: {s3_bucket}")
    print(f"S3 object key: {s3_key}")

    # Print preview of returned data
    print("\nPreview of returned data:")
    print(json.dumps(data, indent=4)[:1000])


if __name__ == "__main__":
    main()