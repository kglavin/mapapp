#!/bin/bash
#
#  start the background tasks
# 
# the proxy cache node. 
# the snmp polling node(s)
# the scm rest-api polling node
# 
cd ./scm-mapapp
python3 scm_proxy.py &
sleep 3
cd ../scm-snmp
python3 snmp_poll_supervisor.py &
cd ../scm-mapapp
python3 scm_poll_supervisor.py &
echo " background tasks running"
