from socket import *
from rdt_stopandwait import *
import threading
import time
from util import *
import os

def clientMain(serverIP, server_port, filename, window_size):
	# message = input("Enter file name:") #take file name as input
	client_socket = socket(AF_INET, SOCK_DGRAM) #make udp socket
	saw_rdt_obj = rdt_stopandwait(client_socket, (serverIP, server_port), 0, 0)
	print("Requesting File:", filename)

	delete_file_first('client/' + filename)

	saw_rdt_obj.rdt_send(filename.encode())
	receivedMessage = saw_rdt_obj.rdt_receive()

	# print(receivedMessage)

	filesize = int(receivedMessage.decode("utf-8")) #decode file size

	if(filesize >0):
		print("file size: "+str(filesize))
		file = open("client/" + filename, "a+b") #download file to client path
		count = filesize/packet_data_size
		tic = time.time()
		while filesize:
			chunk = saw_rdt_obj.rdt_receive() #download file in chunks
			print_download_bar(count - filesize/packet_data_size, count,
				prefix = 'downloading', suffix = util_round(time.time() - tic, 1000))
			filesize = filesize - len(chunk) #deduct length
			file.write(chunk) #write chunk
		file.close()
		# print('\n', filename,"Received successfully with size:", os.stat("client/"+filename).st_size)
	else:
		print("file not found")

	client_socket.close() #close socket

def start_client(filename):
	tic = time.time()
	serverIP,server_port,filename,window_size = read_params(filename)
	clientMain(serverIP, server_port, filename, window_size)
	print('\n', filename, 'completed in', util_round(time.time() - tic, 1000),
		'with size:', os.stat("client/"+filename).st_size)

def read_params(filename):
	file = open(filename)
	serverIP = file.readline()
	server_port = int(file.readline())
	filename = file.readline()
	window_size = int(file.readline())
	return (serverIP[:-1], server_port, filename[:-1], window_size)

def run_client():
	tic = time.time()
	thread1 = threading.Thread(target = start_client, args = ("client.in",))
	thread2 = threading.Thread(target = start_client, args = ("client1.in",))
	thread3 = threading.Thread(target = start_client, args = ("client2.in",))
	thread4 = threading.Thread(target = start_client, args = ("client3.in",))
	thread5 = threading.Thread(target = start_client, args = ("client4.in",))
	
	#parallel

	# thread1.start()
	# thread2.start()
	# thread3.start()
	# thread4.start()
	# thread5.start()
	
	#sequential

	# thread1.run()
	# thread2.run()
	# thread3.run()
	thread4.run()
	# thread5.run()

	print('whole run completed in:', util_round(time.time() - tic, 1000))

def delete_file_first(filename):
	try:
		os.remove(filename)
	except OSError:
		pass

run_client()


