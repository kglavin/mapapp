# mapapp
map application for monitoring a set of steelconnect manager instances

This is a plotly base DASH application build on top of Flask. 

The system consists of a set of backgroud processes that
- act as a local proxy cache to store information that is derived from the SCM instance, this is to limit the amount of rest-api interaction with the SCM thus not overloading the SCM instnacews 
- an SNMP polling subsystem that polls SNMP information from the appliances that are managed by the individual SCM instances, this infromation is stored in a time series database. 
- an instance of the influxdb time series data based into which statistics from the appliances are stored. 
- an SCM polling subsytem which periodically polls information via rest-api from the SCM instances and stores them in the proxy cache instance. 





