import socket
import sys
import threading
from Queue import Queue
import time

HOST = sys.argv[1]  
RECEIVER = sys.argv[2]
PORT = int(sys.argv[3])

maquinas = {'1':'200.17.202.11', '2':'200.17.202.6', '3':'200.17.202.57', '4':'200.17.202.50', '5': 'ALL'}
orig = (HOST, PORT)
udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp.bind(orig)
dest = (RECEIVER, PORT)
stack_creator = (maquinas['3'], PORT)

def timer(signals):
	time.sleep(0.1)
	signals.put("OVER")
	return

def buffer_watcher(messages, signals):
	while True:
		if messages.qsize() != 0:
			signals.put("HAS")
	return

def read(messages):
	while True:
		entrada = raw_input()
		messages.put(entrada)

def receive(messages, signals):
	while True:
		msg, client = udp.recvfrom(1024)
		flag = ''
		if messages.qsize() > 0:
			for x in range(0, messages.qsize()):
				if messages.queue[x] == '#':
					flag = messages.queue[x]
					char_position = x
		if flag == "#":	
			messages.queue[char_position] = "XXX"
			time.sleep(5)
			print "Time Out!"
			print "Recreating Stack..."
			udp.sendto(msg, stack_creator)
			continue
		else:
			pass
		ttimer = threading.Thread(target=timer, args=(signals,))
		tbuffer_watcher = threading.Thread(target=buffer_watcher, args=(messages, signals,))
		ttimer.setDaemon(True)
		tbuffer_watcher.setDaemon(True)
		ttimer.start()
		tbuffer_watcher.start()
		if msg != '':
			received = msg.split('\\')
			clean_received = []
			for message in received:
				splitted_message = message.split(';')
				if not splitted_message[0] == HOST or not message.find('received'):
					clean_received.append(message)
				if splitted_message[1] == HOST or splitted_message[1] == "ALL":
					sum_chars = 0
					message_check = splitted_message[2].split('/check/')
					for x in message_check[0]:
						sum_chars += ord(x)

					sum_chars = sum_chars / float(11)
					if message_check[1] == repr(sum_chars):
						print client, splitted_message[2].split('/check/')[0]
						message = message + "-received"
					else:
						print "ERROR: The message can't be received"
			msg = '\\'.join(clean_received)
		signal = signals.get()
		if signal == "OVER":
			udp.sendto(msg, dest)
		elif signal == "HAS":
			while messages.qsize() != 0:
				typed = messages.get()
				if typed == "XXX":
					continue
				sum_chars = 0
				for x in typed[2:]:
					sum_chars += ord(x)
				sum_chars = sum_chars/float(11)
				message = HOST+';'+maquinas[typed[0]]+';'+typed[2:]+'/check/'+repr(sum_chars)
				if msg == '':
					msg = message
				else:
					msg = msg + "\\" + message
			udp.sendto(msg, dest)
	udp.close()

try:
	messages = Queue()
	signals = Queue()
	read = threading.Thread(target=read, args=(messages,)) 
	receive = threading.Thread(target=receive, args=(messages, signals,))
	read.setDaemon(True)
	receive.setDaemon(True)
	read.start()
	receive.start()

except:
   	print "Error: unable to start thread"

if sys.argv[4] == "START":
	udp.sendto('', dest)
while True:
	time.sleep(1)


