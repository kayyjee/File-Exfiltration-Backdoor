# Backdoor File Exfiltration


A backdoor client server application 

Operates using TCP or UDP. Attacking machine sends commands for victim to execute.
Communication is on a covert channel with data encrypted.
A specific directory on the victim is monitored. 
Any new files or modifications initiate a port-knock with server followed by 
sending the file to the server.




Steps



VICTIM

Manipulate the victim config.txt file with the correct paramaters

srcIP: IP of victim machine
dstIP: IP of server / attacking machine
dstPort: port where attacker is listening
fileDir: directory to be watched. Files modified / added here are sent to attacker
password: key to encrypt / decrypt data


Run victim script on client

	$ python client.py




SERVER

Run the script
	
	$ sudo python server.py


You now have a live session where you can enter terminal commands that will be executed on Victim

enter 'exit' to close





Features:
	* command execution
	* File Exfiltration on specific directory 
	
