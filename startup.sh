#!/bin/bash

openssl rand -hex 32 > /app/git_hash

# Start unoserver if either web or cron might generate PDF documents
if [ "$ENABLE_WEB" == "True" ] || [ "$ENABLE_CRON" == "True" ]; then
    echo "Starting Unoserver daemon"
    unoserver &
fi

if [ "$ENABLE_CRON" == "True" ]; then
    echo "Starting Python Cron"
    python /bin/scheduler.py /app/python-cron /app/logs/python-cron.log &
    status=$?
    if [ $status -ne 0 ]; then
        echo "Failed to start cron: $status"
        exit $status
    fi
fi

if [ "$ENABLE_WEB" == "True" ]; then
    echo "Starting Gunicorn"
    # Use exec so Gunicorn receives SIGTERM signals directly from Docker/K8s for graceful shutdown
    exec gunicorn disturbance.wsgi --bind :8080 --config /app/gunicorn.ini.py
else
    echo "ENABLE_WEB environment variable not set to True, web server is not starting."
    /bin/bash
fi