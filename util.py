from consts import *
from socket import *
import select


class rdt:
	send_seq_num = 0
	recv_seq_num = 0
	selfSocket = 0
	toAdd = 0
	timeoutVal = start_timeout_val
	def __init__(self, socket, toAdd):
		self.selfSocket = socket
		self.toAdd = toAdd
		self.selfSocket.setblocking(0)

	def clear(self):
		self.send_seq_num = 0
		self.recv_seq_num = 0
		self.toAdd = 0
		self.timeoutVal = start_timeout_val

	def rdt_send(self, msg):
		length = len(msg)
		sent = 0
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
				self.selfSocket.sendto(data, self.toAdd)
				ready = select.select([self.selfSocket], [], [], self.timeoutVal)
				if(ready[0]):
					data,self.toAdd = self.selfSocket.recvfrom(packet_data_size+2)
					if(getSeqNum(data) == self.send_seq_num):
						#expected ack
						break
					else:
						trials = trials + 1
				else:
					trials = trials + 1


				
			self.send_seq_num = (self.send_seq_num + 1)% 2

	def rdt_receive(self):
		trials = 0
		while(trials < max_trials_num):
			ready = select.select([self.selfSocket], [], [], self.timeoutVal)
			if(ready[0]):
				data,self.toAdd = self.selfSocket.recvfrom(packet_data_size+2)
				# print("rdt")
				# print(data)
				rec_seq = getSeqNum(data)
				# print("cur seq num:", self.recv_seq_num , "packet seq num:" ,rec_seq)
				if(rec_seq != self.recv_seq_num):
					makePkt(b"", self.recv_seq_num)
					self.selfSocket.sendto(makePkt(b'',(self.recv_seq_num+1)%2), self.toAdd)
					trials = trials + 1
				else:
					self.selfSocket.sendto(makePkt(b'',self.recv_seq_num), self.toAdd)
					self.recv_seq_num = (self.recv_seq_num + 1)%2
					return getData(data)
			else:
				trials = trials + 1
				continue
		if(trials == max_trials_num):
			raise Exception("timed out")


def getSeqNum(data):
	return int.from_bytes(data[0:1], byteorder = 'big')

def makePkt(data, seqNum):
	ret = seqNum.to_bytes(1, byteorder = 'big')
	ret = ret + data
	return ret

def getData(msg):
	return msg[1:]
