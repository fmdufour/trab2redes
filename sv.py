#!/usr/bin/env python
import socket
import time
import sys
import threading
from Queue import PriorityQueue

#
TOKEN_VAZIO = "$$$$$$$$$$"
TOKEN_RESERV = "$$$$$$$$$"

UDP_IP = "127.0.0.1"
UDP_PORT = 5005
ESGOTOU_TEMPO = False
PASSOU_1SEG = False
PORTA_VIZINHO = int(sys.argv[2])
IP_VIZINHO = UDP_IP

def get_mensagem_console():
	leu = False
	while(not leu):
		entrada = raw_input()

		campos = entrada.split(' ') 

		try:
			if(len(campos) >= 3):						
				int(campos[0])
				if(campos[0] < 0 and campos[0] > 4):
					print "O Destino deve ser um numero de 1 a 4"
					continue
				int(campos[1])
				return entrada		
			else:
				print "Digite a Mensagem no Formato <Destino> <Prioridade> <Msg>"		
			
		except:
			print "Digite a Mensagem no Formato <Destino> <Prioridade> <Msg>"		
			pass

def ler_mensagens(mensagens):
	while True:
		entrada = get_mensagem_console()	
		#formato msg = <destino><prioridade><priori_reserva><msg>
		destino = entrada.split(' ')[0] 
		prioridade = entrada.split(' ')[1]
		desc_msg = entrada[entrada.index(prioridade) + 2:]

		msg = ""
		msg += destino
		msg += prioridade
		msg += "0"
		msg += desc_msg

		prioridade = -int(prioridade)				
		mensagens.put((prioridade, msg))


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
	ESGOTOU_TEMPO = False
	time.sleep(10)	
	ESGOTOU_TEMPO = True	

#devolve a prioridade se tiver alguma msg
#ou devolve a menor prioridade = 9
def get_maior_priori(mensagens):
	return 0 if mensagens.qsize() == 0 else -mensagens.queue[0][0]


def dono_token(mensagens, sock):	
	global ESGOTOU_TEMPO
	while(not ESGOTOU_TEMPO):
		if(mensagens.qsize() > 0):			
			msg = mensagens.get()[1]	

			#print "Enviando Mensagem para " + IP_VIZINHO + ":" + str(PORTA_VIZINHO)
			while(mensagens.qsize() == 0 and not ESGOTOU_TEMPO):
				sock.sendto(msg, (IP_VIZINHO, PORTA_VIZINHO))

				msg, addr = sock.recvfrom(1024) 			
				
				priori_reserva = get_priori_reserva(msg)
				
				#se alguem com maior prioridade reservar o token libera o token
				if( priori_reserva > get_maior_priori(mensagens)):
					#manda token reservado pra quem tem maior prioridade	
					print "liberando TOKEN"			
					ESGOTOU_TEMPO = True
					sock.sendto("$$" + str(priori_reserva) + TOKEN_RESERV, (IP_VIZINHO, PORTA_VIZINHO))						
					return
				msg = "0" + msg[1:]		

			
			#print "Recebeu de Volta a Msg:" + msg
	#envia token ja que esgotou o tempo
	sock.sendto(TOKEN_VAZIO, (IP_VIZINHO, PORTA_VIZINHO))	
	
def get_destino(msg):
	return msg[:1]

def get_priori(msg):
	return int(msg[1:2])

def get_priori_reserva(msg):	
	return int(msg[2:3])

def get_msg(msg):
	return msg[3:]


def main():
	global IP_VIZINHO
	global PORTA_VIZINHO
	global ESGOTOU_TEMPO

	if(len(sys.argv) < 3):
		sys.exit("Informe os argumentos <IPBIND> <PORTABIND> <IP_VIZINHO> <PORTA_VIZINHO> <NUM_SERVIDOR>")

	IP_VIZINHO = UDP_IP#int(sys.argv[1])
	PORTA_VIZINHO = int(sys.argv[2])#int(sys.argv[2])	
	porta_bind = int(sys.argv[1])	

	sock = cria_socket(UDP_IP, porta_bind)

	id_server = sys.argv[3]

	primeiro_server = True if id_server == "1" else False
	
	mensagens = PriorityQueue()	

	if(primeiro_server):		
		raw_input("Aperte ENTER para comecar")					
		esta_com_token = True
		start_thread_tempo()
	else:
		esta_com_token = False
	
	#inicia Thread que popula fila com mensagens lidas
	start_thread_msg(mensagens)

	while True:
		try:			
			if(not esta_com_token):
				#recebe mensagem 
				#print "Esperando Mensagens..."
				msg, addr = sock.recvfrom(1024) 				
				
				#verifica se o token esta vazio
				if (msg == TOKEN_VAZIO):
				
					#print "Recebeu Token"
					if(mensagens.qsize() > 0):
						#pega token para si
						esta_com_token = True
						ESGOTOU_TEMPO = False
						start_thread_tempo()
						print "$$$$ Pegou Token $$$$"
					else:
						#repassa token vazio						
						#print "Repassando Token Vazio..."
						sock.sendto(msg, (IP_VIZINHO,PORTA_VIZINHO))

				elif(msg.endswith(TOKEN_RESERV)):
					if(get_maior_priori(mensagens) >= get_priori_reserva(msg)):
						#se entrou aqui eh pq tem msg com prioridade maior do que o digito de reserva
						esta_com_token = True
						ESGOTOU_TEMPO = False
						start_thread_tempo()
						print "$$$$ Pegou Token $$$$"
					else:
						sock.sendto(msg, (IP_VIZINHO,PORTA_VIZINHO))		
				else:
					#verifica se no tem alguma mensagem com prioridade maior para ser enviada
					
					maior_priori = get_maior_priori(mensagens)													

					if(maior_priori > get_priori(msg) and maior_priori > get_priori_reserva(msg)):
						#reserva token		
						msg = msg[:2] + str(maior_priori) + msg[3:]																	
					#verifica destino maquina
					if(get_destino(msg) == id_server):						
						print "===================\nMENSAGEM RECEBIDA:\n     " + get_msg(msg) + "\n==================="

						sock.sendto(msg[:3], (IP_VIZINHO,PORTA_VIZINHO))
					else:												
						sock.sendto(msg, (IP_VIZINHO,PORTA_VIZINHO))


			else:
				#entra loop de envio de mensagens
				dono_token(mensagens, sock)
				#como terminou tempo seta que nao esta com token
				esta_com_token = False
				print "$$$$--Perdeu Token--$$$$"
			
		except Exception, e:
			raise e
    


if __name__ == '__main__':
    	main()   
