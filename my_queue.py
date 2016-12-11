import queue

class MyQueue(queue.Queue):
	def __init__(self, sz):
		super().__init__(sz)

	def top(self):
		return self.queue[0]

	def get_index(self, idx):
		with self.mutex:
			if(idx < len(self.queue)):
				return self.queue[idx]
			else: return -1

	def find(self, param, val):
		with self.mutex:
			for obj in self.queue:
				if(obj[param] == val):
					return obj
		return -1
	def remove(self, obj):
		del obj