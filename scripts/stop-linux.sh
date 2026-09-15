#!/bin/sh
# Stop and remove the JobFit container.
docker rm -f jobfit 2>/dev/null || true