# Build the JobFit image and run it on port 8000.
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
docker build -t jobfit .
$ErrorActionPreference = "Continue"
docker rm -f jobfit 2>$null
$ErrorActionPreference = "Stop"
docker run -d --name jobfit -p 8000:8000 --env-file .env -v jobfit-data:/data jobfit
Write-Output "JobFit is running at http://localhost:8000"