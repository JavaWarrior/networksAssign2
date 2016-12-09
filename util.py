from consts import *
from socket import *
import select
import random
import struct
import array
import sys


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
				# print('sending packet')
				self.sendPkt(data)
				ready = select.select([self.selfSocket], [], [], self.timeoutVal)
				if(ready[0]):
					# print('received packet')
					rec_data,self.toAdd = self.selfSocket.recvfrom(packet_data_size+header_size)
					if(getSeqNum(rec_data) == self.send_seq_num):
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
					print('received wrong packet')
				elif (checkValid(data)):
					self.sendPkt(makePkt(b'',self.recv_seq_num))
					self.recv_seq_num = (self.recv_seq_num + 1)%2
					return getData(data)
				else:
					#ack nothing here 
					trials = trials + 1
					print('received corrupted packet')
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
	checksumVal = 0
	ret = seqNum.to_bytes(1, byteorder = 'big') + data #make packet with no checksum
	checksumVal = checksum(ret) #compute checksum
	# print(checksum(ret) == checksumVal)
	assert(checksum(ret) == checksumVal)
	ret = seqNum.to_bytes(1, byteorder = 'big') + checksumVal.to_bytes(2,byteorder = 'big') + data #update packet checksum
	return ret

def getData(msg):
	return msg[header_size:]

if struct.pack("H",1) == "\x00\x01": # big endian
	def checksum(pkt):
		if len(pkt) % 2 == 1:
			pkt += "\0".encode()
		s = sum(array.array("H", pkt))
		s = (s >> 16) + (s & 0xffff)
		s += s >> 16
		s = ~s
		return s & 0xffff
else:
	def checksum(pkt):
		# pkt = pkt1
		if len(pkt) % 2 == 1:
			pkt += "\0".encode()
		s = sum(array.array("H", pkt))
		s = (s >> 16) + (s & 0xffff)
		s += s >> 16
		s = ~s
		return (((s>>8)&0xff)|s<<8) & 0xffff

def checkValid(pkt):
	data = pkt[0:1]+pkt[header_size:]
	checksumVal = int.from_bytes(pkt[1:3],byteorder = 'big')
	# print(checksumVal, checksum(data), data)
	return (checksum(data)==checksumVal)

def printProgress (iteration, total, prefix = '', suffix = '', decimals = 1, barLength = 50):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        barLength   - Optional  : character length of bar (Int)
    """
    formatStr = "{0:." + str(decimals) + "f}"
    percent = formatStr.format(100 * (iteration / float(total)))
    filledLength = int(round(barLength * iteration / float(total)))
    bar = '█' * filledLength + '-' * (barLength - filledLength)
    sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percent, '%', suffix)),
    if iteration == total:
        sys.stdout.write('\n')
    sys.stdout.flush()	