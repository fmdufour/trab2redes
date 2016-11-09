#!/usr/bin/env python
import socket
import time
import sys
import threading
from Queue import Queue

#
TAM_TOKEN_VAZIO = 2

UDP_IP = "127.0.0.1"
UDP_PORT = 5005
ESGOTOU_TEMPO = False
PORTA_VIZINHO = int(sys.argv[2])
IP_VIZINHO = UDP_IP

def get_mensagem_console():
	leu = False
	while(not leu):
		entrada = raw_input()

		campos = entrada.split(' ') 

		if(len(campos) == 3):						
			return entrada		
		else:
			print "Digite a Mensagem no Formato <Destino> <Prioridade> <Msg>"		

def ler_mensagens(mensagens):
	while True:
		entrada = get_mensagem_console();		 
		mensagens.put(entrada);		

def cria_socket(ip, porta):
	sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
	#sock.setblocking(False)
	sock.bind((ip, porta))

	return sock

def start_thread_msg(mensagens):
	ler = threading.Thread(target=ler_mensagens, args=(mensagens,))
	ler.setDaemon(True)	
	ler.start()

def start_thread_tempo():
	timer = threading.Thread(target=conta_tempo)
	timer.setDaemon(True)	
	timer.start()

def conta_tempo():
	global ESGOTOU_TEMPO
	print "=====INICIANDO TEMPO====="
	ESGOTOU_TEMPO = False
	time.sleep(10)	
	ESGOTOU_TEMPO = True
	print "======TEMPO ESGOTADO======"



def dono_token(mensagens, sock):	
	while(not ESGOTOU_TEMPO):
		if(mensagens.qsize() > 0):
			msg = mensagens.get()					
			#print "Enviando Mensagem para " + IP_VIZINHO + ":" + str(PORTA_VIZINHO)
			sock.sendto(msg, (IP_VIZINHO, PORTA_VIZINHO))
			msg, addr = sock.recvfrom(1024) 
			#print "Recebeu de Volta a Msg:" + msg
	#envia token ja que esgotou o tempo
	sock.sendto("##", (IP_VIZINHO, PORTA_VIZINHO))	
	


def main():
	global IP_VIZINHO
	global PORTA_VIZINHO

	if(len(sys.argv) < 3):
		sys.exit("Informe os argumentos <IPBIND> <PORTABIND> <IP_VIZINHO> <PORTA_VIZINHO> <PRIMEIRO>")

	IP_VIZINHO = UDP_IP#int(sys.argv[1])

	PORTA_VIZINHO = int(sys.argv[2])#int(sys.argv[2])	

	porta_bind = int(sys.argv[1])	

	sock = cria_socket(UDP_IP, porta_bind)

	id_server = sys.argv[3]

	primeiro_server = True if id_server == "1" else False
	
	mensagens = Queue()	
	
	esta_com_token = False

	if(primeiro_server):
		#garante a insercao de ao menos uma mensagem
		print "Digite a Mensagem"
		msg = get_mensagem_console()
		
		mensagens.put(msg)
		esta_com_token = True
		start_thread_tempo()
	
	#inicia Thread que popula fila com mensagens lidas
	start_thread_msg(mensagens)

	while True:
		try:			
			if(not esta_com_token):
				#recebe mensagem 
				#print "Esperando Mensagens..."
				msg, addr = sock.recvfrom(1024) 
				#print "Mensagem recebida", msg

				#verifica se o token esta vazio
				if (msg[:2] == "##"):
				
					#print "Recebeu Token"
					if(mensagens.qsize() > 0):
						#pega token para si
						esta_com_token = True
						start_thread_tempo()
						print "Pegou Token"
					else:
						#repassa token vazio
						time.sleep(2)
						#print "Repassando Token Vazio..."
						sock.sendto(msg, (IP_VIZINHO,PORTA_VIZINHO))

				else:
					#verifica destino maquina
					if(msg[:1] == id_server):
						print "***MENSAGEM RECEBIDA:\n " + msg[3:] + "\n***"
						sock.sendto(msg[:3], (IP_VIZINHO,PORTA_VIZINHO))
					else:												
						sock.sendto(msg, (IP_VIZINHO,PORTA_VIZINHO))


			else:
				#entra loop de envio de mensagens
				dono_token(mensagens, sock)
				#como terminou tempo seta que nao esta com token
				esta_com_token = False
				print "Nao esta mais com o Token"
			
		except Exception, e:
			pass
    


if __name__ == '__main__':
    	main()   
