#!/bin/bash

openssl rand -hex 32 > /app/git_hash

# Start unoserver if either web or cron might generate PDF documents
if [ "$ENABLE_WEB" == "True" ] || [ "$ENABLE_CRON" == "True" ]; then
    echo "Starting Unoserver daemon..."

    if [ ! -f "/opt/libreoffice/program/soffice" ]; then
        echo "ERROR: LibreOffice executable not found at /opt/libreoffice/program/soffice" >&2
        exit 1
    fi

    if ! command -v unoserver &> /dev/null; then
        echo "ERROR: 'unoserver' command not found" >&2
        exit 1
    fi
    
    /opt/libreoffice/program/python -m unoserver.server --executable /opt/libreoffice/program/soffice &
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