#!/usr/bin/env bash
# start-server.sh
PORT=${PORT:-8010}

if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ] ; then
    (cd openlxp-xss; python manage.py createsuperuser --no-input)
fi
(cd openlxp-xss; gunicorn openlxp_xss_project.wsgi --reload --user www-data --bind 0.0.0.0:$PORT --workers 3) &
nginx -g "daemon off;"
