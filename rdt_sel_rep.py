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
import threading
import queue

class rdt_sel_rep(rdt):
	# constants #
	header_size = 6 									#extra bits added for header (4 seq num and 2 checksum)
	plp = 0												#packet loss probability
	# constants #
	
	self_socket = 0										#socket used by this class for sending receiving
	to_add = 0											#address that we're running connection with
	timeout_val = 0										#time out value (rtt dependent)

	window_size =0
	seqnum_max = 0
	
	send_lock = 0
	recv_lock = 0

	send_base = 0
	next_seqnum  = 0

	recv_base = 0

	timer_queue = 0
	recv_queue = 0
	running = True

	def __init__(self, socket, to_add, plp, seed, window_size):
		#constructor
		self.self_socket = socket
		self.to_add = to_add
		self.self_socket.setblocking(0)
		self.plp = plp
		random.seed(seed)
		self.timeout_val = self.start_timeout_val

		self.window_size = window_size
		self.seqnum_max = window_size * 2 + 1

		self.send_lock = threading.RLock()	
		self.recv_lock = threading.RLock()	

		self.timer_queue = queue.Queue(self.window_size)
		self.recv_queue = queue.Queue(self.window_size)

		#start send and receiving threads
		threading.Thread(target = self.sender_kernel, args = ()).start()
		threading.Thread(target = self.receiver_kernel, args = ()).start()



	def clear(self):
		#used to reset connection(mainly for server welcoming port)
		self.to_add = 0
		self.timeout_val = self.start_timeout_val

		self.send_lock = threading.RLock()	
		self.recv_lock = threading.RLock()	

		self.send_base = 0
		self.next_seqnum = 0

		self.recv_base = 0

		self.timer_queue = queue.Queue(self.window_size)
		self.recv_queue = queue.Queue(self.window_size)

		self.running = True

	def rdt_send(self, file):
		chunk = file.read(packet_data_size)
		while(chunk):
			#make object representing this packet
			obj = {'time': -1, 'data': chunk, 'seqnum': self.gen_seqnum(), 'acked': False}
			print('sending...')
			self.timer_queue.put(obj) #queue.put wait till queue has place and puts object in it

			chunk = file.read(packet_data_size) #read another file

		while(not self.timer_queue.empty()): continue

		self.running = False

	def rdt_send_buf(self, msg):
		#make object representing this packet
		obj = {'time': -1, 'data': msg, 'seqnum': self.gen_seqnum(), 'acked': False}
		self.timer_queue.put(obj) #queue.put wait till queue has place and puts object in it		
		while(not self.timer_queue.empty()): continue

	def sender_foreach(self,obj,i):
		if(obj['acked'] and  obj['seqnum'] == self.send_base):
			#advance window
			t = self.timer_queue.get()
			self.send_lock.acquire()
			self.send_base = (self.send_base + 1)%self.seqnum_max
			self.calc_timeout(t['time'])
			self.send_lock.release()


		elif (obj['acked']):
			#do nothing packet already acked
			return
		elif (obj['time'] == -1 or time.time() - obj['time'] > self.timeout_val):
			#resend packet
			with self.timer_queue.mutex:
				self.timer_queue.queue[i]['time'] = time.time()
				#update timer value
			self.send_pkt(self.make_pkt(obj['data'], obj['seqnum']))

	def sender_kernel(self):
		#sender thread
		while(self.running):
			queue_foreach(self.timer_queue, self.sender_foreach)
				

	def receiver_kernel(self):
		while(self.running):
			ready = select.select([self.self_socket], [], [], 0)	#wait till received packet
			if(ready[0]):
				#packet arrived
				rcvd_pkt,self.to_add = self.self_socket.recvfrom(packet_data_size+self.header_size) #get received packet
				rec_seqnum = self.get_seq_num(rcvd_pkt)
				print(rcvd_pkt)
				if(not self.check_valid(rcvd_pkt)):
					continue
				if(self.is_ack(rcvd_pkt)):
					#ack package received
					with self.send_lock:
						if(rec_seqnum == self.send_base):
							t = self.timer_queue.get()
							self.calc_timeout(t['time'])
							self.send_base = (self.send_base + 1)%self.seqnum_max
						elif(self.is_ack_waited(rec_seqnum)):
							#we're waiting for this ack
							obj, idx = find(self.timer_queue, 'seqnum', rec_seqnum)
							if(rec_seqnum != -1):
								edit(self.timer_queue, idx, ['acked', 'time'], [True, time.time() - obj['time']])
				else:
					#we're receiving packets
					if(self.is_pkt_not_dup(rec_seqnum)):
						#packet is not duplicate
						self.recv_queue.put({'data': self.get_data(rcvd_pkt), 'seqnum': rec_seqnum})
					#ack the packet anyway
					self.send_pkt(self.make_pkt(b'', rec_seqnum))

	def rdt_receive(self):
		while(1):
			element, idx = find(self.recv_queue, 'seqnum', self.recv_base)
			if(idx != -1):
				element = remove(self.recv_queue, idx)
				with self.recv_lock:
					self.recv_base = (self.recv_base + 1)%self.seqnum_max
				return element['data']

	def gen_seqnum(self):
		self.send_lock.acquire()
		val = self.next_seqnum
		self.next_seqnum = (self.next_seqnum + 1)% self.seqnum_max
		self.send_lock.release()
		return val

	def is_ack_waited(self, seqnum):
		with self.send_lock:
			if(self.send_base < self.next_seqnum):
				return seqnum >= self.send_base and seqnum < self.next_seqnum
			elif(self.send_base > self.next_seqnum):
				return seqnum >= self.send_base or seqnum < self.next_seqnum

	def is_pkt_not_dup(self, seqnum):
		with self.recv_lock:
			if(self.recv_base + self.window_size < self.seqnum_max ):
				return seqnum >= self.recv_base and seqnum < self.recv_base + self.window_size
			else:
				return seqnum > self.recv_base or seqnum < (self.recv_base + self.window_size)%self.seqnum_max


	def send_pkt(self, pkt):
		if(random.random() >= self.plp):
			# print(self.plp)
			ready = select.select([], [self.self_socket], [], 0)
			while(not ready[1]):
				ready = select.select([], [self.self_socket], [], 0)
				#wait until ready then send the packet.
			self.self_socket.sendto(pkt, self.to_add)
	

	def get_seq_num(self, data):
		return int.from_bytes(data[0:4], byteorder = 'big')

	def make_pkt(self, data, seq_num):
		checksum_val = 0
		ret = seq_num.to_bytes(4, byteorder = 'big') + data #make packet with no checksum
		checksum_val = checksum(ret) #compute checksum
		# print(checksum(ret) == checksum_val)
		assert(checksum(ret) == checksum_val)
		ret = seq_num.to_bytes(4, byteorder = 'big') + checksum_val.to_bytes(2,byteorder = 'big') + data #update packet checksum
		return ret

	def get_data(self, msg):
		return msg[self.header_size:]

	def check_valid(self, pkt):
		data = pkt[0:4]+pkt[self.header_size:]
		checksum_val = int.from_bytes(pkt[4:6],byteorder = 'big')
		# print(checksum_val, checksum(data), data)
		return (checksum(data)==checksum_val)

	def is_ack(self, pkt):
		return len(pkt) == 6
		# 1 seqnum and 2 checksum for ack
