#!/usr/bin/env python
import socket
import pickle
import hashlib
import sys
import time
import random

#takes the port number as command line arguments and create server socket
serverIP="127.0.0.1"
#serverPort=int(sys.argv[1])
serverPort=9986

server=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
server.bind((serverIP,serverPort))
server.settimeout(0.01)
print("Ready to serve")

#initializes packet variables
expected_seqnum=1

#RECEIVES DATA
f = open("output", "wb")
end_of_file = False		#checksum which defines whether finish reading
last_pkt_recv = time.time()		#Whether receive the pkt,timer start counting
starttime = time.time()

#emulate timeout
t_delay=random.randint(50,150)/10000

while True:
	try:
		recvpkt=[]
		packet,clientAddress= server.recvfrom(4096)
		recvpkt = pickle.loads(packet)

		#check whether the received checksum value are the same as its sequence number
		c = recvpkt[-1]	#the last part of the received packet
		del recvpkt[-1]
		md5rec = hashlib.md5()
		md5rec.update(pickle.dumps(recvpkt))
		# detect if there exists error
		if c == md5rec.digest():	#if all the data are correct
		#check whether the received packet's sequence number is in order
			if(recvpkt[0]==expected_seqnum):		#IN ORDER
				print("ACCEPT", expected_seqnum)
				#write the data
				if recvpkt[1]:	#the second part is the data,if it's not empty
					f.write(recvpkt[1])
				else:			#if the data is empty,its bool value=False
					end_of_file = True

				#create ACK (seqnum,checksum)
				sndpkt = []
				sndpkt.append(recvpkt[0])	#return received data sequence number
				md5 = hashlib.md5()
				md5.update(pickle.dumps(sndpkt))
				sndpkt.append(md5.digest())
				ack_pkt = pickle.dumps(sndpkt)

				#emulate the timeout
				#time.sleep(t_delay)

				server.sendto(ack_pkt,(clientAddress[0], clientAddress[1]))
				print("Return Ack",recvpkt[0])
				# update the expected_number
				expected_seqnum = expected_seqnum + 1
				#use this to record the most recently received packet num
				last_rec_pkt=expected_seqnum-1

			else:	#DISORDER
			#Discard all the following packet and
			#resend ACK for most recently received inorder pkt
				print("Received packet" ,recvpkt[0],"is out of order")
				print("IGNORED")
				print("resend the most recently inorder ACK",last_rec_pkt)
				sndpkt = []
				sndpkt.append(last_rec_pkt)
				# Because we have update the expected sequence num,we need to subtract one
				# to tell the the client what the server most recently received
				md5 = hashlib.md5()
				md5.update(pickle.dumps(sndpkt))
				sndpkt.append(md5.digest())
				pkt_back = pickle.dumps(sndpkt)

				#return the ACK packet
				server.sendto(pkt_back, (serverIP, serverPort))
				print("Ack", expected_seqnum)
		else:	#detect error
			print("IGNORED")
	except:
		if end_of_file:		#If reach the end of the data
			if(time.time()-last_pkt_recv>0.2):
				#wait for more than a timeout period
				break

endtime = time.time()

f.close()
print('FILE TRANFER SUCCESSFUL')
print("TIME TAKEN ", str(endtime - starttime))