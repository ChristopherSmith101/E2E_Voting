#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. Install dependencies
pip install -r requirements.txt

# 2. Database Cleanup (The "Common Issue" fix)
if [ -f "web/instance/app.db" ]; then
    echo "Removing old database..."
    rm web/instance/app.db
fi
