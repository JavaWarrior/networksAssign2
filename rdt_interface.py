from abc import ABCMeta, abstractmethod

class rdt:
	__metaclass__ = ABCMeta
	
	start_timeout_val = 0.2

	rtt_exp = start_timeout_val
	rtt_var = 0

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

	def calc_timeout(self,new_rtt):
		self.rtt_exp = 0.875 * self.rtt_exp + 0.125 * new_rtt
		self.rtt_var = 0.75 * self.rtt_var + 0.25 * abs(self.rtt_exp - new_rtt)
		# print(new_rtt, self.rtt_exp + 4 * self.rtt_var)
		return self.rtt_exp + 4 * self.rtt_var

