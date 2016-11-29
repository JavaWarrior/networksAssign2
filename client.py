from socket import *
from util import *
import threading
import time

def clientMain(serverIP, serverPort, fileName, windowSize):
	# message = input("Enter file name:") #take file name as input
	clientSocket = socket(AF_INET, SOCK_DGRAM) #make udp socket
	rdt_obj = rdt(clientSocket, (serverIP, serverPort), 0, 0)
	print("Requesting File:", fileName)
	rdt_obj.rdt_send(fileName.encode())
	receivedMessage = rdt_obj.rdt_receive()

	# print(receivedMessage)

	fileSize = int(receivedMessage.decode("utf-8")) #decode file size

	if(fileSize >0):
		print("file size: "+str(fileSize))

		file = open("client/" + fileName, "a+b") #download file to client path
		count = fileSize/packet_data_size
		tic = time.time()
		while fileSize:
			chunk = rdt_obj.rdt_receive() #download file in chunks
			printProgress(count - fileSize/packet_data_size, count,prefix = 'downloading', suffix = time.time() - tic)
			fileSize = fileSize - len(chunk) #deduct length
			file.write(chunk) #write chunk
		file.close()
		print(fileName,"Received successfully.")
	else:
		print("file not found")

	clientSocket.close() #close socket

def startClient(fileName):
	serverIP,serverPort,fileName,windowSize = readParams(fileName)
	clientMain(serverIP, serverPort, fileName, windowSize)

def readParams(fileName):
	file = open(fileName)
	serverIP = file.readline()
	serverPort = int(file.readline())
	fileName = file.readline()
	windowSize = int(file.readline())
	return (serverIP[:-1], serverPort, fileName[:-1], windowSize)

def runClient():
	thread1 = threading.Thread(target = startClient, args = ("client.in",))
	thread2 = threading.Thread(target = startClient, args = ("client1.in",))
	thread3 = threading.Thread(target = startClient, args = ("client2.in",))
	thread4 = threading.Thread(target = startClient, args = ("client3.in",))
	thread5 = threading.Thread(target = startClient, args = ("client4.in",))
	
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
	# thread4.run()
	thread5.run()

runClient()