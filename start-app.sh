#!/usr/bin/env bash
# start-server.sh

python manage.py waitdb 
python manage.py migrate 
cd /opt/app/ 
pwd 
service clamav-daemon restart
./start-server.sh