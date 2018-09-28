#!/bin/bash

cd ./scm-mapapp
python3 scm_proxy.py &
cd ../scm-snmp
python3 snmp_poll_supervisor.py &
cd ../scm-mapapp
python3 scm_poll_supervisor.py &
echo " background taks running"
