import struct
import sys
import array

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



def print_download_bar (iteration, total, prefix = '', suffix = '', decimals = 1, barLength = 50):
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

def util_round(number, factor):
	return int(number*factor)/factor
	#rounds number to nearest factor precision e.g. round(1.1234, 10) = 1.1


def top(q):
	with q.mutex:
		if(q.qsize() > 0 ):
			return q.queue[0]

def find(q, param, value):
	for i in range(q.qsize()):
		obj = 0
		with q.mutex:
			obj = q.queue[i]
		if obj[param] == value:
			return obj,i
	return -1,-1

def edit(q, idx, param_list, new_value_list):
	with q.mutex:
		if(idx < len(q.queue)):
			for i in range(len(param_list)):
				q.queue[idx][param_list[i]] = new_value_list[i]
def remove(q, idx):
	x = -1
	with q.mutex:
		if(idx < len(q.queue)):
			x = q.queue[idx]
			del q.queue[idx]
	return x

def queue_foreach(q, func):
	for i in range(q.qsize()):
		obj = 0
		with q.mutex:
			if(i < len(q.queue) ):
				obj = q.queue[i]
		if(obj != 0):
			ret = func(obj,i)
