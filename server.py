from socket import *
from util import *
import os
CHUNK_SIZE = 500
port = 5000
bufferSize = 1000
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(("", port))

rdt_obj = rdt(serverSocket, ("localhost", port))

print("server started")
while 1:
	message = rdt_obj.rdt_receive()
	message = message.decode("utf-8")
	print(message)
	if os.path.isfile("server/"+message):
		file = open("server/"+message, "rb")
		fileSize = os.stat("server/"+message).st_size
		print("request: " + message + ", size: " + str(fileSize))

		rdt_obj.rdt_send(str(fileSize).encode())

		chunk = file.read(CHUNK_SIZE)
		while chunk:
			rdt_obj.rdt_send(chunk)
			chunk = file.read(CHUNK_SIZE)
		file.close()
		print("Sent successfully")
	else:
		print("requested file not found: "+ message)
		rdt_obj.rdt_send(b"0")
