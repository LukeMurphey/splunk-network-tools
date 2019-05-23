
[speedtest://default]
* Configure an input to do a Internet connection performance test

server = <value>
* The server to use when testing
* A server will be automatically selected if this is left blank

runs = <value>
* The number of runs to execute

[ping://default]
* Configure an input to ping a host to ensure it is up

dest = <value>
* A comma separated list of hosts or networks to ping
* This field can contain CIDR ranges (e.g. 10.0.1.0/24), host names, or IP addresses 

runs = <value>
* The number of runs to execute

interval = <value>
* Indicates how often to perform the ping

port = <value>
* Indicates which port to use if using TCP
* Leave this blank in order to use ICMP

[portscan://default]
* Configure an input to port scan a host to identify open ports

dest = <value>
* A comma separated list of hosts or networks to ping

interval = <value>
* Indicates how often to perform the ping

ports = <value>
* Indicates which ports to scan
