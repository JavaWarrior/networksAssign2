from consts import *
from socket import *
import select
import random
import struct
import array
import sys
from rdt_interface import *
from util import *
class rdt_stopandwait(rdt):
	# constants #
	start_timeout_val = 0.2
	header_size = 3
	# constants #
	
	send_seq_num = 0
	recv_seq_num = 0
	self_socket = 0
	to_add = 0
	timeout_val = start_timeout_val
	plp = 0
	rtt = 1

	def __init__(self, socket, to_add, plp, seed):
		self.self_socket = socket
		self.to_add = to_add
		self.self_socket.setblocking(0)
		self.plp = plp
		random.seed(seed)

	def clear(self):
		self.send_seq_num = 0
		self.recv_seq_num = 0
		self.to_add = 0
		self.timeout_val = self.start_timeout_val

	def rdt_send(self, msg):
		length = len(msg)
		sent = 0
		max_trials_num = max(10, length / packet_data_size * 2)
		while (sent < length):
			data = 0
			if(packet_data_size + sent < length):
				data = self.make_pkt(msg[sent:sent+packet_data_size], self.send_seq_num)
				sent = sent + packet_data_size
			else:
				data = self.make_pkt(msg[sent:length], self.send_seq_num)
				sent = length
			trials = 0
			while trials < max_trials_num:
				# print(sent)
				# print('sending packet')
				self.send_pkt(data)
				ready = select.select([self.self_socket], [], [], self.timeout_val)
				if(ready[0]):
					# print('received packet')
					data,self.to_add = self.self_socket.recvfrom(packet_data_size+self.header_size)
					if(self.get_seq_num(data) == self.send_seq_num):
						#expected ack
						break
					else:
						trials = trials + 1
				else:
					trials = trials + 1
			self.send_seq_num = (self.send_seq_num + 1)% 2
		if(trials == max_trials_num):
			raise Exception("timed out")

	def rdt_receive(self):
		trials = 0
		max_trials_num = 10
		while(trials < max_trials_num):
			ready = select.select([self.self_socket], [], [], self.timeout_val)
			if(ready[0]):
				data,self.to_add = self.self_socket.recvfrom(packet_data_size+self.header_size)
				# print("rdt")
				# print(data)
				rec_seq = self.get_seq_num(data)
				# print("cur seq num:", self.recv_seq_num , "packet seq num:" ,rec_seq)
				if(rec_seq != self.recv_seq_num):
					self.send_pkt(self.make_pkt(b'',(self.recv_seq_num+1)%2))
					trials = trials + 1
					print('received wrong packet')
				elif (self.check_valid(data)):
					self.send_pkt(self.make_pkt(b'',self.recv_seq_num))
					self.recv_seq_num = (self.recv_seq_num + 1)%2
					return self.get_data(data)
				else:
					#ack nothing here 
					trials = trials + 1
					print('received corrupted packet')
			else:
				trials = trials + 1
		if(trials == max_trials_num):
			raise Exception("timed out")
	def send_pkt(self, pkt):
		if(random.random() >= self.plp):
			# print(self.plp)
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
