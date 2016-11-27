from socket import *
from util import *

CHUNK_SIZE = 500
serverName = "localhost"
serverPort = 5000
bufferSize = 100
message = input("Enter file name:") #take file name as input
clientSocket = socket(AF_INET, SOCK_DGRAM) #make udp socket
rdt_obj = rdt(clientSocket, (serverName, serverPort))


rdt_obj.rdt_send(message.encode())
receivedMessage = rdt_obj.rdt_receive()

print(receivedMessage)

fileSize = int(receivedMessage.decode("utf-8")) #decode file size

if(fileSize >0):
	print("file size: "+str(fileSize))

	file = open("client/" + message, "a+b") #download file to client path

	while fileSize:
		chunk = rdt_obj.rdt_receive() #download file in chunks
		fileSize = fileSize - len(chunk) #deduct length
		file.write(chunk) #write chunk
	file.close()
	print("Received successfully.")
else:
	print("file not found")

clientSocket.close() #close socket