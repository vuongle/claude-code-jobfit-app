#!/bin/sh
# Build the JobFit image and run it on port 8000.
set -e
cd "$(dirname "$0")/.."
docker build -t jobfit .
docker rm -f jobfit 2>/dev/null || true
docker run -d --name jobfit -p 8000:8000 --env-file .env -v jobfit-data:/data jobfit
echo "JobFit is running at http://localhost:8000"