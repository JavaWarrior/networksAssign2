import client
import server
import statistics
import time
import threading
def run_test(serverfilename):

	files = ['client.in', 'client1.in', 'client2.in', 'client3.in', 'client4.in']
	thread_server = server.server_thread(serverfilename)
	thread_server.start()

	time.sleep(1)
	out = open('tests/stopwait_out_'+serverfilename+'.out', 'w')

	out.write(serverfilename)
	out.write('\n')
	
	for file in files:
		times = [0] * 5
		for i in range(5):
			tic = time.time()
			client.start_client(file)			
			times[i] = time.time() - tic
			out.write(str(times[i]))
			out.write(',')
		out.write(str(sum(times) / len(times)))
		out.write(',')
		out.write(str(statistics.stdev(times)))
		out.write('\n')

	thread_server.turn_off()


run_test('server_0.in')
run_test('server_0.05.in')
run_test('server_0.1.in')
run_test('server_0.3.in')

