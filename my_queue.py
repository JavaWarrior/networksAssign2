import queue

class MyQueue(queue.Queue):
	def __init__(self, sz):
		super().__init__(sz)

	def top(self):
		with self.mutex:
			if(len(self.queue) > 0):
				return self.queue[0]
			return -1

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

	def find_idx(self, param, val):
		with self.mutex:
			for i in range(len(self.queue)):
				if(self.queue[i][param] == val):
					return i
		return -1

	def remove(self, obj_idx):
		with self.mutex:
			if(obj_idx < len(self.queue)):
				x = self.queue[obj_idx]
				del self.queue[obj_idx]
			else:
				x = -1
		return x

	def clear(self):
		with self.mutex:
			self.queue.clear()