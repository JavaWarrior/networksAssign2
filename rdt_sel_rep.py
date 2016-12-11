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
import my_queue
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
	pkts_cnt_lock = 0

	recv_cond = 0
	send_cond = 0

	send_base = 0
	next_seqnum  = 0

	recv_base = 0

	timer_queue = 0
	recv_queue = 0
	running = True

	pkts_cnt = 0
	def __init__(self, socket, to_add, plp, seed, window_size):
		#constructor
		self.self_socket = socket
		self.to_add = to_add
		# self.self_socket.setblocking(0)
		self.plp = plp
		random.seed(seed)
		self.timeout_val = self.start_timeout_val

		self.window_size = window_size
		self.seqnum_max = window_size * 2 + 1

		self.send_lock = threading.RLock()	
		self.recv_lock = threading.RLock()	
		self.pkts_cnt_lock = threading.RLock()

		self.send_cond = threading.Semaphore(0)
		self.recv_cond = threading.Semaphore(0)


		self.timer_queue = my_queue.MyQueue(self.window_size)
		self.recv_queue = my_queue.MyQueue(self.window_size)

		#start send and receiving threads
		threading.Thread(target = self.sender_kernel, args = ()).start()
		threading.Thread(target = self.receiver_kernel, args = ()).start()



	def clear(self):
		#used to reset connection(mainly for server welcoming port)
		self.to_add = 0
		self.timeout_val = self.start_timeout_val

		self.send_lock = threading.RLock()	
		self.recv_lock = threading.RLock()	
		self.pkts_cnt_lock = threading.RLock()	

		self.send_cond = threading.Semaphore(0)
		self.recv_cond = threading.Semaphore(0)

		self.send_base = 0
		self.next_seqnum = 0

		self.recv_base = 0

		self.timer_queue = my_queue.MyQueue(self.window_size)
		self.recv_queue = my_queue.MyQueue(self.window_size)

		self.running = True

	def turnoff(self):
		self.running = False
		self.self_socket.close()

	def rdt_send(self, file):
		self.pkts_cnt = 0
		chunk = file.read(packet_data_size)
		while(chunk):
			with self.pkts_cnt_lock:
				self.pkts_cnt = self.pkts_cnt + 1
			#make object representing this packet
			obj = {'time': -1, 'data': chunk, 'seqnum': self.gen_seqnum(), 'acked': False}
			self.timer_queue.put(obj) #queue.put wait till queue has place and puts object in it

			chunk = file.read(packet_data_size) #read another file

		while(1):
			self.send_cond.acquire()
			with self.pkts_cnt_lock:
				# print(self.pkts_cnt)
				if(self.pkts_cnt == 0):
					break

	def rdt_send_buf(self, msg):
		#make object representing this packet
		obj = {'time': -1, 'data': msg, 'seqnum': self.gen_seqnum(), 'acked': False}
		self.timer_queue.put(obj) #queue.put wait till queue has place and puts object in it		
		while(not self.timer_queue.empty()): self.send_cond.acquire()

	def sender_kernel(self):
		#sender thread
		while(self.running):
			sz = self.timer_queue.qsize()
			for i in range(sz):
				obj = self.timer_queue.get_index(i)
				if(obj != -1):
					if(obj['acked'] and  obj['seqnum'] == self.send_base):
						#advance window
						t = self.timer_queue.get()
						self.send_base = (self.send_base + 1)%self.seqnum_max
						self.calc_timeout(t['time'])

					elif (obj['acked']):
						#do nothing packet already acked
						return
					elif (obj['time'] == -1 or time.time() - obj['time'] > self.timeout_val):
						#update timer value
						obj['time'] = time.time()
						#resend packet
						self.send_pkt(self.make_pkt(obj['data'], obj['seqnum']))
				

	def receiver_kernel(self):
		while(self.running):
			rcvd_pkt = 0
			rcvd_pkt,self.to_add = self.self_socket.recvfrom(packet_data_size+self.header_size) #get received packet
			if(rcvd_pkt):
				#packet arrived
				rec_seqnum = self.get_seq_num(rcvd_pkt)
				if(not self.check_valid(rcvd_pkt)):
					continue
				if(self.is_ack(rcvd_pkt)):
					#ack package received
					# print('\r', 'received ack', rec_seqnum)
					if(self.is_ack_waited(rec_seqnum)):
						#we're waiting for this ack
						with self.pkts_cnt_lock:
							self.pkts_cnt = self.pkts_cnt - 1
						obj= self.timer_queue.find('seqnum', rec_seqnum)
						if(obj != -1):
							obj['acked'] = True
							obj['time'] = time.time()
						self.send_cond.release()
						self.send_cond.release()
				else:
					# print('\r', 'received msg', rec_seqnum)
					#we're receiving packets
					if(self.is_pkt_not_dup(rec_seqnum)):
						#packet is not duplicate
						self.recv_queue.put({'data': self.get_data(rcvd_pkt), 'seqnum': rec_seqnum})
					#ack the packet anyway
					# self.recv_cond.release()
					self.send_pkt(self.make_pkt(b'', rec_seqnum))

	def rdt_receive(self):
		while(1):
			# self.recv_cond.acquire()
			obj= self.recv_queue.find( 'seqnum', self.recv_base)
			if(obj != -1):
				element = self.recv_queue.remove(obj)
				self.recv_base = (self.recv_base + 1)%self.seqnum_max
				return element['data']

	def gen_seqnum(self):
		val = self.next_seqnum
		self.next_seqnum = (self.next_seqnum + 1)% self.seqnum_max
		return val

	def is_ack_waited(self, seqnum):
		if(self.send_base < self.next_seqnum):
			return seqnum >= self.send_base and seqnum < self.next_seqnum
		elif(self.send_base > self.next_seqnum):
			return seqnum >= self.send_base or seqnum < self.next_seqnum

	def is_pkt_not_dup(self, seqnum):
		if(self.recv_base + self.window_size < self.seqnum_max ):
			return seqnum >= self.recv_base and seqnum < self.recv_base + self.window_size
		else:
			return seqnum > self.recv_base or seqnum < (self.recv_base + self.window_size)%self.seqnum_max


	def send_pkt(self, pkt):
		if(random.random() >= self.plp):
			threading.Thread(target = self.self_socket.sendto, args = (pkt, self.to_add)).start()
			# self.self_socket.sendto(pkt, self.to_add)
	

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
