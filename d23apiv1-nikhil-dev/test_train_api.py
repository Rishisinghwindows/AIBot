"""Quick test for train status API using curl."""

import subprocess
import os
from datetime import datetime

# Read API key from .env file
api_key = ""
with open(".env") as f:
    for line in f:
        if line.startswith("RAILWAY_API_KEY="):
            api_key = line.strip().split("=", 1)[1]
            break

print(f"API Key: {api_key[:10]}...{api_key[-5:]}" if api_key else "No API key found!")

train_number = "18625"
date = datetime.now().strftime("%Y%m%d")

print(f"\nTesting train {train_number} for date {date}")
print("=" * 50)

# Test API V1 (shivesh96)
print("\n1. Testing shivesh96 API...")
cmd1 = f'''curl -s -w "\\nHTTP_CODE:%{{http_code}}" \
  "https://train-running-status-indian-railways.p.rapidapi.com/getTrainRunningStatus/{train_number}/{date}" \
  -H "X-RapidAPI-Key: {api_key}" \
  -H "X-RapidAPI-Host: train-running-status-indian-railways.p.rapidapi.com"'''

result = subprocess.run(cmd1, shell=True, capture_output=True, text=True)
print(result.stdout)

# Test API V2 (rahilkhan224)
print("\n2. Testing rahilkhan224 API...")
cmd2 = f'''curl -s -w "\\nHTTP_CODE:%{{http_code}}" \
  "https://indian-railway-irctc.p.rapidapi.com/api/trains/v1/train/status?train_number={train_number}&departure_date={date}&isH5=true&client=web" \
  -H "X-RapidAPI-Key: {api_key}" \
  -H "X-RapidAPI-Host: indian-railway-irctc.p.rapidapi.com" \
  -H "x-rapid-api: rapid-api-database"'''

result = subprocess.run(cmd2, shell=True, capture_output=True, text=True)
print(result.stdout)
