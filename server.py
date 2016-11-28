from socket import *
from util import *
import threading
import os
CHUNK_SIZE = 500
port = 5000
bufferSize = 1000

def serverMain():
	serverSocket = socket(AF_INET, SOCK_DGRAM)
	serverSocket.bind(("", port))

	rdt_obj = rdt(serverSocket, ("localhost", port))

	print("server started")
	while 1:
		try:
			message = rdt_obj.rdt_receive()
		except:
			continue
		message = message.decode("utf-8")
		task = threading.Thread(target = threadFunc, args = (message, rdt_obj.toAdd))
		task.start()
		rdt_obj.clear()


def threadFunc(fileName,clientAdd):
	# print("entered child")
	threadSocket = socket(AF_INET, SOCK_DGRAM)
	threadSocket.bind(("",0))
	rdt_obj = rdt(threadSocket, clientAdd)
	if os.path.isfile("server/"+fileName):
		file = open("server/"+fileName, "rb")
		fileSize = os.stat("server/"+fileName).st_size
		print("request: " + fileName + ", size: " + str(fileSize))

		rdt_obj.rdt_send(str(fileSize).encode())

		chunk = file.read(CHUNK_SIZE)
		while chunk:
			rdt_obj.rdt_send(chunk)
			chunk = file.read(CHUNK_SIZE)
		file.close()
		print("Sent successfully")
	else:
		print("requested file not found: "+ fileName)
		rdt_obj.rdt_send(b"0")

#thread = threading.Thread(target = threadFunc)
#thread.start()

def readParams(fileName):
	file = open(fileName)
	serverPort = int(file.readline())
	windowSize = int(file.readline())
	seed = int(file.readline())
	prob = int(file.readline())
	return (serverPort, windowSize, seed, prob)
serverMain()