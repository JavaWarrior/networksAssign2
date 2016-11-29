from consts import *
from socket import *
import select
import random
class rdt:
	send_seq_num = 0
	recv_seq_num = 0
	selfSocket = 0
	toAdd = 0
	timeoutVal = start_timeout_val
	plp = 0
	rtt = 1
	def __init__(self, socket, toAdd, plp, seed):
		self.selfSocket = socket
		self.toAdd = toAdd
		self.selfSocket.setblocking(0)
		self.plp = plp
		random.seed(seed)

	def clear(self):
		self.send_seq_num = 0
		self.recv_seq_num = 0
		self.toAdd = 0
		self.timeoutVal = start_timeout_val

	def rdt_send(self, msg):
		length = len(msg)
		sent = 0
		max_trials_num = max(10, length / packet_data_size * 2)
		while (sent < length):
			data = 0
			if(packet_data_size + sent < length):
				data = makePkt(msg[sent:sent+packet_data_size], self.send_seq_num)
				sent = sent + packet_data_size
			else:
				data = makePkt(msg[sent:length], self.send_seq_num)
				sent = length
			trials = 0
			while trials < max_trials_num:
				# print(sent)
				self.sendPkt(data)
				ready = select.select([self.selfSocket], [], [], self.timeoutVal)
				if(ready[0]):
					data,self.toAdd = self.selfSocket.recvfrom(packet_data_size+header_size)
					if(getSeqNum(data) == self.send_seq_num):
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
			ready = select.select([self.selfSocket], [], [], self.timeoutVal)
			if(ready[0]):
				data,self.toAdd = self.selfSocket.recvfrom(packet_data_size+header_size)
				# print("rdt")
				# print(data)
				rec_seq = getSeqNum(data)
				# print("cur seq num:", self.recv_seq_num , "packet seq num:" ,rec_seq)
				if(rec_seq != self.recv_seq_num):
					self.sendPkt(makePkt(b'',(self.recv_seq_num+1)%2))
					trials = trials + 1
				else:
					self.sendPkt(makePkt(b'',self.recv_seq_num))
					self.recv_seq_num = (self.recv_seq_num + 1)%2
					return getData(data)
			else:
				trials = trials + 1
		if(trials == max_trials_num):
			raise Exception("timed out")
	def sendPkt(self, pkt):
		if(random.random() >= self.plp):
			# print(self.plp)
			self.selfSocket.sendto(pkt, self.toAdd)
	

def getSeqNum(data):
	return int.from_bytes(data[0:1], byteorder = 'big')

def makePkt(data, seqNum):
	ret = seqNum.to_bytes(1, byteorder = 'big')
	ret = ret + data
	return ret

def getData(msg):
	return msg[header_size:]

