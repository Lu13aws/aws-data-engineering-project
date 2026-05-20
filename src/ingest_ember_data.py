import os
import json
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv


# Base URL for the Ember API
BASE_URL = "https://api.ember-energy.org/v1"

# Specific endpoint for monthly electricity generation data
ENDPOINT = "/electricity-generation/monthly"


def main():

    # Load environment variables from the .env file
    load_dotenv()

    # Read API key from environment variable
    api_key = os.getenv("EMBER_API_KEY")

    # Stop the program if no API key is found
    if not api_key:
        raise ValueError("EMBER_API_KEY was not found. Check your .env file.")

    # Parameters for the API request
    # These define:
    # - countries
    # - energy types
    # - time period
    params = {
        "entity_code": "DEU,FRA,CHE",   # Germany, France, Switzerland
        "series": "Solar,Wind",         # Energy sources
        "start_date": "2025-04",        # Start period
        "end_date": "2026-04",          # End period
        "is_aggregate_series": "false",
        "api_key": api_key,             # Personal API key
    }

    # Build the full API URL
    url = f"{BASE_URL}{ENDPOINT}"

    print("Sending request to Ember API...")
    print(f"URL: {url}")

    # Send GET request to the API
    response = requests.get(url, params=params, timeout=30)

    # Print HTTP response status
    print("Status code:", response.status_code)

    # If request fails, print error and stop
    if response.status_code != 200:
        print("Error response:")
        print(response.text)
        response.raise_for_status()

    # Convert API response to Python dictionary
    data = response.json()

    # Create local folder for raw data storage
    output_dir = Path("data/raw/ember/electricity_generation/monthly")

    # Create folder structure if it does not exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create timestamp for unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Build output filename
    output_file = output_dir / f"ember_monthly_generation_{timestamp}.json"

    # Save JSON response locally
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

    print(f"Data successfully saved to: {output_file}")

    # Print preview of the JSON response
    print("\nPreview of returned data:")
    print(json.dumps(data, indent=2)[:1000])


# Entry point of the script
if __name__ == "__main__":
    main()