#!/usr/bin/env python
#Transmit N packets in order.
# If any one of the packets is missing,it will resend after timeout
#
#the receiver would drop all the packets,then the sender will
#retransmit all of them again.
import socket
import sys
import time
import hashlib
import pickle       #To store the data

recv_host='127.0.0.1'
recv_port=9986
#recv_host=str(sys.argv[1])     #the address where you are going to send
#recv_port=int(sys.argv[2])     #you can type in the port you want

#create the socket
client=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
client.settimeout(0.01)

#takes the file name as command line arguments
#filename = ''.join(sys.argv[3])
filename='./alice.txt'

#initializes window variables (upper and lower window bounds, position of next seq number)
lar=0
seq_num=1
windowSize=5
slidewindow = []        #use this list to store all the packets

#SENDS DATA
fileOpen= open(filename, 'rb')  #read in binary
data = fileOpen.read(500)       #send 500-byte data
data_fin_state = False          #define whether the all the data are read
last_ackrecv = time.time()  # timer start to calculate

while not data_fin_state or slidewindow:    #'not' is prior 'or'
    #Only when reaching the EOF,meanwhile the window is empty.
    #Then the window will stop sending
    if(seq_num<lar+windowSize) and not data_fin_state:
    # When the window is full,stop transmitting
    # Each time we update the lar,meaning that new packets can be sent
        #create packet(seqnum,data,checksum)
        sndpkt = []
        sndpkt.append(seq_num)
        sndpkt.append(data)     #store them in the sndpkt list

        md5 = hashlib.md5()     #define hash.md5 algorithm
        md5.update(pickle.dumps(sndpkt))
        #pickle.dumps(obj,protocol) store in byte stream format.(in binary)
        #update() didn't replace the origin data.
        #But each time it would splice new data to the old one.
        #So we need to initialize md5 each time

        sndpkt.append(md5.digest())  #Add the encrypted part in the pkt list
        #Outcome digest() is an attribute of variable md5
        #Serilize the data,encrypt them.MD5 can compute data in str form and byte form

        ###
        #Use hash-md5 algorithm to encrypt the data.MD5 is an irreversable algorithm
        #It's easy to derivate from data to digest,but hard to do this in the opposite direction
        ###

        pkt=pickle.dumps(sndpkt)
        #The outcome is in HASH type.So,only after transferring
        #the object into byte('utf-8') form,then network can send them.
        # encode() would transfer data from str to byte
        # decode() would transfer data from byte to str

        #send the packet
        client.sendto(pkt,(recv_host, recv_port))
        print("Sent data",seq_num)

        #increment variable nextSeqnum
        seq_num=seq_num+1

        if(not data):   #if data is empty,data=False
            data_fin_state =not data_fin_state  #set the statement flag be True
        #append packet to window
        slidewindow.append(sndpkt)

        #read more data
        data = fileOpen.read(500)

    #RECEIPT OF AN ACK
    try:
        packet,serverAddress = client.recvfrom(4096)
        recv_pkt = []
        recv_pkt = pickle.loads(packet)

        #check value of checksum received (c) against checksum calculated (h)
        c = recv_pkt[-1]
        del recv_pkt[-1] #delete the last part
        md5 = hashlib.md5()
        md5.update(pickle.dumps(recv_pkt))

        # First,check whether got the right packet
        if c == md5.digest():   #Get correct packet
            print("Received ack for", recv_pkt[0])
            #slide window and reset timer
            while recv_pkt[0]>lar and slidewindow:  #when get the right packet
                last_ackrecv=time.time()
                # each time we get a new ACK,we just reset the recv_time and lar
                del slidewindow[0]
                # if it's in order,it must be the first one in the list
                # delete the first one,make room for other packets
                lar = lar + 1
                # update the lar number,which means we can send one more packet
        else:   #Detect error
            print("error detected")
    #TIMEOUT
    except:
        if(time.time()-last_ackrecv>0.01):
            # We cares about the timeout all the time
            # This means if we didn't received the expacted packet,
            # the timer won't be updated and after timeout,
            # client would resend all the packets in the slidewindow

            # for i in slidewindow:
            #     pkt=pickle.dumps(i)
            #     client.sendto(pkt,(recv_host, recv_port))

            for i in range(len(slidewindow)):
                pkt = pickle.dumps(slidewindow[i])
                client.sendto(pkt, (recv_host, recv_port))
                print('resend packet',slidewindow[i][0])

fileOpen.close()
print("connection closed")
client.close()
