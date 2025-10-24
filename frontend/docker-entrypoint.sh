#!/bin/sh

# Replace environment variables in JavaScript files
# This allows dynamic configuration at runtime

ENV_FILE="/usr/share/nginx/html/env-config.js"

echo "window._env_ = {" > $ENV_FILE
echo "  VITE_API_BASE_URL: '${VITE_API_BASE_URL:-http://localhost:8000/api}'," >> $ENV_FILE
echo "};" >> $ENV_FILE

# Execute the CMD
exec "$@"
