# sookie
wait for a socket to start listening, then exits

Sookie waits for a server socket to start accepting connections, and when it does sooke exits and allows the calling shell script to continue on its way. Sookie exits wit an error if the wait times out. All actioons are logged using syslog, locally and optionally remotely to, for instance, a logstash server.
