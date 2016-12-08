from abc import ABCMeta, abstractmethod

class rdt:
	__metaclass__ = ABCMeta

	@abstractmethod
	def rdt_send(self, msg): pass
	@abstractmethod
	def rdt_recieve(self): pass
	@abstractmethod
	def clear(self): pass
	@abstractmethod
	def make_pkt(self, data, seq_num): pass
	@abstractmethod
	def get_seq_num(self,msg): pass
	@abstractmethod
	def get_data(self,msg): pass
	@abstractmethod
	def check_valid(self, msg): pass

