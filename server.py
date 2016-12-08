from socket import *
from util import *
from consts import *
import threading
import os
import time

from rdt_stopandwait import *

def server_main(server_port, window_size, seed, plp):
	server_socket = socket(AF_INET, SOCK_DGRAM)
	server_socket.bind(("", server_port))
	saw_rdt_obj = rdt_stopandwait(server_socket, ("localhost", server_port), plp, seed)

	print("server started")
	while 1:
		try:
			message = saw_rdt_obj.rdt_receive()
		except:
			continue
		message = message.decode("utf-8")
		task = threading.Thread(target = connection_thread, args = (message, saw_rdt_obj.to_add, seed, plp))
		task.start()
		saw_rdt_obj.clear()


def connection_thread(filename, client_add, seed, plp):
	# print("entered child")
	thread_socket = socket(AF_INET, SOCK_DGRAM)
	thread_socket.bind(("",0))
	saw_rdt_obj = rdt_stopandwait(thread_socket, client_add, plp, seed)
	if os.path.isfile("server/"+filename):
		file = open("server/"+filename, "rb")
		fileSize = os.stat("server/"+filename).st_size
		print("request: " + filename + ", size: " + str(fileSize))
		tic = time.time()
		saw_rdt_obj.rdt_send(str(fileSize).encode())

		chunk = file.read(packet_data_size)
		while chunk:
			saw_rdt_obj.rdt_send(chunk)
			chunk = file.read(packet_data_size)
		file.close()
		print("Sent successfully in:", util_round(time.time() - tic), "sec")
	else:
		print("requested file not found: "+ filename)
		saw_rdt_obj.rdt_send(b"0")

#thread = threading.Thread(target = connection_thread)
#thread.start()

def read_params(filename):
	file = open(filename)
	server_port = int(file.readline())
	window_size = int(file.readline())
	seed = int(file.readline())
	plp = float(file.readline())
	return (server_port, window_size, seed, plp)

def start_server(filename):
	server_port, window_size, seed, plp = read_params(filename)
	server_main(server_port, window_size, seed, plp)

start_server('server.in')