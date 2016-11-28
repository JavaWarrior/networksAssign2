from socket import *
from util import *
import threading
def clientMain(serverIP, serverPort, fileName, windowSize):
	# message = input("Enter file name:") #take file name as input
	clientSocket = socket(AF_INET, SOCK_DGRAM) #make udp socket
	rdt_obj = rdt(clientSocket, (serverIP, serverPort))

	print("Requesting File:", fileName)
	rdt_obj.rdt_send(fileName.encode())
	receivedMessage = rdt_obj.rdt_receive()

	print(receivedMessage)

	fileSize = int(receivedMessage.decode("utf-8")) #decode file size

	if(fileSize >0):
		print("file size: "+str(fileSize))

		file = open("client/" + fileName, "a+b") #download file to client path

		while fileSize:
			chunk = rdt_obj.rdt_receive() #download file in chunks
			fileSize = fileSize - len(chunk) #deduct length
			file.write(chunk) #write chunk
		file.close()
		print("Received successfully.")
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
	thread1.run()
	thread2.run()
	thread3.run()

runClient()