from socket import *
from util import *
from consts import *
import threading
import os


def serverMain(serverPort, windowSize, seed, plp):
	serverSocket = socket(AF_INET, SOCK_DGRAM)
	serverSocket.bind(("", serverPort))
	rdt_obj = rdt(serverSocket, ("localhost", serverPort), plp, seed)

	print("server started")
	while 1:
		try:
			message = rdt_obj.rdt_receive()
		except:
			continue
		message = message.decode("utf-8")
		task = threading.Thread(target = threadFunc, args = (message, rdt_obj.toAdd, seed, plp))
		task.start()
		rdt_obj.clear()


def threadFunc(fileName, clientAdd, seed, plp):
	# print("entered child")
	threadSocket = socket(AF_INET, SOCK_DGRAM)
	threadSocket.bind(("",0))
	rdt_obj = rdt(threadSocket, clientAdd, plp, seed)
	if os.path.isfile("server/"+fileName):
		file = open("server/"+fileName, "rb")
		fileSize = os.stat("server/"+fileName).st_size
		print("request: " + fileName + ", size: " + str(fileSize))

		rdt_obj.rdt_send(str(fileSize).encode())

		chunk = file.read(packet_data_size)
		while chunk:
			rdt_obj.rdt_send(chunk)
			chunk = file.read(packet_data_size)
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
	plp = float(file.readline())
	return (serverPort, windowSize, seed, plp)

def startServer(fileName):
	serverPort, windowSize, seed, plp = readParams(fileName)
	serverMain(serverPort, windowSize, seed, plp)

startServer('server.in')