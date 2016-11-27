from consts import *
from socket import *
import select


class rdt:
	send_seq_num = 0
	recv_seq_num = 0
	selfSocket = 0
	toAdd = 0
	timeoutVal = 5
	def __init__(self, socket, toAdd):
		self.selfSocket = socket
		self.toAdd = toAdd
		# self.selfSocket.setblocking(0)

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
			while 1:
				self.selfSocket.sendto(data, self.toAdd)
				ready = select.select([self.selfSocket], [], [], self.timeoutVal)
				if(ready[0]):
					data,self.toAdd = self.selfSocket.recvfrom(packet_data_size+2)
					if(getSeqNum(data) == self.send_seq_num):
						#expected ack
						break

				
			self.send_seq_num = (self.send_seq_num + 1)% 2

	def rdt_receive(self):
		while(1):
			ready = select.select([self.selfSocket], [], [], self.timeoutVal)
			if(ready[0]):
				data,self.toAdd = self.selfSocket.recvfrom(packet_data_size+2)
				rec_seq = getSeqNum(data)
				while(rec_seq != self.recv_seq_num):
					makePkt(b"", self.recv_seq_num)
					ready = select.select([self.selfSocket], [], [], self.timeoutVal)
					if(ready[0]):
						data,self.toAdd = self.selfSocket.recvfrom(packet_data_size+2)
						rec_seq = getSeqNum(data)
						#print(data[1:].decode("utf-8"))
				self.recv_seq_num = (self.recv_seq_num + 1)%2
				return data[1:]


def getSeqNum(data):
	return int.from_bytes(data[0:1], byteorder = 'big')

def makePkt(data, seqNum):
	ret = seqNum.to_bytes(1, byteorder = 'big')
	ret = ret + data
	return ret
