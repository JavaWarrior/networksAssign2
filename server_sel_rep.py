from socket import *
from util import *
from consts import *
import threading
import os
import time

from rdt_sel_rep import *
class server_thread(threading.Thread):
	running = True
	filename = 0
	def __init__(self,filename):
		threading.Thread.__init__(self)
		self.filename = filename

	def server_main(self, server_port, window_size, seed, plp):
		server_socket = socket(AF_INET, SOCK_DGRAM)

		server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

		server_socket.bind(("", server_port))
		sr_rdt_obj = rdt_sel_rep(server_socket, ("localhost", server_port), plp, seed, window_size)

		print("server started")
		while self.running:
			message = sr_rdt_obj.rdt_receive()
			message = message.decode("utf-8")
			task = threading.Thread(target = connection_thread, args = (message, sr_rdt_obj.to_add, seed, plp, window_size))
			task.start()
			sr_rdt_obj.clear()

		# server_socket.shutdown(1)
		server_socket.close()

	def turn_off(self):
		self.running = False

	def start_server(self):
		server_port, window_size, seed, plp = read_params(self.filename)
		self.server_main(server_port, window_size, seed, plp)

	def run(self):
		self.start_server()


def connection_thread(filename, client_add, seed, plp, window_size):
	# print("entered child")
	thread_socket = socket(AF_INET, SOCK_DGRAM)
	thread_socket.bind(("",0))
	sr_rdt_obj = rdt_sel_rep(thread_socket, client_add, plp, seed, window_size)
	if os.path.isfile("server/"+filename):
		file = open("server/"+filename, "rb")
		fileSize = os.stat("server/"+filename).st_size
		print("request: " + filename + ", size: " + str(fileSize))
		tic = time.time()
		sr_rdt_obj.rdt_send_buf(str(fileSize).encode())

		sr_rdt_obj.rdt_send(file)
		file.close()
		print("Sent successfully in:", util_round(time.time() - tic, 1000), "sec")
	else:
		print("requested file not found: "+ filename)
		sr_rdt_obj.rdt_send(b"0")

	# thread_socket.shutdown(1)
	thread_socket.close()

#thread = threading.Thread(target = connection_thread)
#thread.start()

def read_params(filename):
	file = open(filename)
	server_port = int(file.readline())
	window_size = int(file.readline())
	seed = int(file.readline())
	plp = float(file.readline())
	return (server_port, window_size, seed, plp)

st = server_thread('server.in')
st.run()
