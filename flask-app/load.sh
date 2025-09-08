#!/bin/bash

read -p "Enter the base URL of your Flask app (e.g., http://localhost:5000): " BASE_URL

read -p "Enter number of requests per endpoint: " NUM_REQUESTS

# List of endpoints
ENDPOINTS=(
  "/"
  "/db"
  "/compute"
  "/error"
  "/order"
  "/pay"
  "/checkout"
  "/buy"
)

echo "Starting load generation on $BASE_URL ..."
echo "Sending $NUM_REQUESTS requests to each endpoint."

for endpoint in "${ENDPOINTS[@]}"; do
  echo ">>> Hitting $BASE_URL$endpoint"
  for i in $(seq 1 $NUM_REQUESTS); do
    curl -s -o /dev/null -w "%{http_code} " "$BASE_URL$endpoint"
  done
  echo -e "\nDone with $endpoint"
done

echo "Load test finished!"
