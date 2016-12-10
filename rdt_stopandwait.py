from consts import *
from socket import *
import select
import random
import struct
import array
import sys
from rdt_interface import *
from util import *
import time

class rdt_stopandwait(rdt):
	# constants #
	header_size = 3 									#extra bits added for header (1 seq num and 2 checksum)
	plp = 0												#packet loss probability
	# constants #
	
	send_seq_num = 0									#current seq num for sending packets
	recv_seq_num = 0									#current seq num for receiving packets
	self_socket = 0										#socket used by this class for sending receiving
	to_add = 0											#address that we're running connection with
	timeout_val = 0										#time out value (rtt dependent)
	
	def __init__(self, socket, to_add, plp, seed):
		#constructor
		self.self_socket = socket
		self.to_add = to_add
		self.self_socket.setblocking(0)
		self.plp = plp
		random.seed(seed)
		self.timeout_val = self.start_timeout_val

	def clear(self):
		#used to reset connection(mainly for server welcoming port)
		self.send_seq_num = 0
		self.recv_seq_num = 0
		self.to_add = 0
		self.timeout_val = self.start_timeout_val

	def rdt_send(self, msg):
		#send msg of at max packet_data_size
		assert(len(msg) <= packet_data_size)

		max_trials_num = 3			#at most connection will drop every packet once or twice
		trials = 0					#number of trials to send packets
		to_be_sent = self.make_pkt(msg, self.send_seq_num) #make packet to be send
		packet_time_start = time.time()			#store time when packet was sent
		self.send_pkt(to_be_sent)						#send packet
		# while trials <= max_trials_num:
		while 1:
			# print('sending packet', len(msg))	
			ready = select.select([self.self_socket], [], [], self.timeout_val)	#wait for ack
			if(ready[0]):		#packet received
				# print('received packet')
				rcvd_pkt,self.to_add = self.self_socket.recvfrom(packet_data_size+self.header_size)
				#receive packet 
				# print(self.to_add)
				if(self.get_seq_num(rcvd_pkt) == self.send_seq_num and self.isAck(rcvd_pkt)):
					#expected ack
					self.timeout_val = self.calc_timeout(time.time() - packet_time_start)
					#rtt between sending packet and receiving ack
					break
				else:
					#received ack seqnum is invalid (delayed ack)
					trials = trials + 1
			else:
				#at timeout reset rtt counter
				packet_time_start = time.time()
				self.send_pkt(to_be_sent)						#send packet				
				trials = trials + 1
		self.send_seq_num = (self.send_seq_num + 1)% 2
		# if(trials > max_trials_num):
			# raise Exception("timed out")

	def rdt_receive(self):
		trials = 0
		max_trials_num = 3

		while(1):
			ready = select.select([self.self_socket], [], [], 0)	#wait till received packet
			if(ready[0]):	#something is received
				rcvd_pkt,self.to_add = self.self_socket.recvfrom(packet_data_size+self.header_size) #get received packet
				# print("rdt")
				# print(rcvd_pkt)
				rec_seq = self.get_seq_num(rcvd_pkt)
				# print("cur seq num:", self.recv_seq_num , "packet seq num:" ,rec_seq)
				if(rec_seq != self.recv_seq_num):
					#received packet with wrong seq number (our last ack is lost)
					self.send_pkt(self.make_pkt(b'',(self.recv_seq_num+1)%2))	#resend the ack
					# print('received wrong packet')
					self.recv_last_pack = time.time()
				elif (self.check_valid(rcvd_pkt) and not self.isAck(rcvd_pkt)):
					#received the wanted packet
					self.send_pkt(self.make_pkt(b'',self.recv_seq_num)) #ack that we received the packet correctly
					self.recv_seq_num = (self.recv_seq_num + 1)%2	#increase seq num for receiving files
					return self.get_data(rcvd_pkt)

	def send_pkt(self, pkt):
		if(random.random() >= self.plp):
			# print(self.plp)
			ready = select.select([], [self.self_socket], [], 0)
			while(not ready[1]):
				ready = select.select([], [self.self_socket], [], 0)
				#wait until ready then send the packet.
			self.self_socket.sendto(pkt, self.to_add)
	

	def get_seq_num(self, data):
		return int.from_bytes(data[0:1], byteorder = 'big')

	def make_pkt(self, data, seq_num):
		checksum_val = 0
		ret = seq_num.to_bytes(1, byteorder = 'big') + data #make packet with no checksum
		checksum_val = checksum(ret) #compute checksum
		# print(checksum(ret) == checksum_val)
		assert(checksum(ret) == checksum_val)
		ret = seq_num.to_bytes(1, byteorder = 'big') + checksum_val.to_bytes(2,byteorder = 'big') + data #update packet checksum
		return ret

	def get_data(self, msg):
		return msg[self.header_size:]

	def check_valid(self, pkt):
		data = pkt[0:1]+pkt[self.header_size:]
		checksum_val = int.from_bytes(pkt[1:3],byteorder = 'big')
		# print(checksum_val, checksum(data), data)
		return (checksum(data)==checksum_val)

	def isAck(self, pkt):
		return len(pkt) == 3
		# 1 seqnum and 2 checksum for ack