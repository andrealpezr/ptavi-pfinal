#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Creamos uaclient para comunicarlo con proxy."""

import socket
import sys
import os
import time
import hashlib
from xml.sax import make_parser
from xml.sax.handler import ContentHandler

# Argumentos y errores
if len(sys.argv) == 4:
   CONFIG = sys.argv[1]
   METHOD = sys.argv[2]
   OPTION = sys.argv[3]
else:
    sys.exit("Usage: python3 uaclient.py config method option")


class XMLClient(ContentHandler):
    """Clase que extrae e imprime el xml del cliente."""

    def __init__(self):
        """Inicializo las variabes."""
        self.Lista_client = []

    def startElement(self, element, attrs):
        """Crea las etiquetas y tributos del xml."""
        self.dicc_etiq_server = {'account': ['username', 'passwd'],
                                 'uaserver': ['ip', 'puerto'],
                                 'rtpaudio': ['puerto'],
                                 'regproxy': ['ip', 'puerto'],
                                 'log': ['path'],
                                 'audio': ['path']
                                 }
        if element in self.dicc_etiq_server:
            Dict_server = {}
            # Recorre los atributos y los guarda en Dict_server
            for atrib in self.dicc_etiq_server[element]:
                Dict_server[atrib] = attrs.get(atrib, "")
            # Guarda sin sustituir lo que habia dentro
            self.Lista_client.append([element, Dict_server])

    def get_tags(self):
        """Devuelve los datos del xml del cliente."""
        return self.Lista_client


# Creo el socket para parsear el XML y trabajar con el
parser = make_parser()
Handler = XMLClient()
parser.setContentHandler(Handler)
parser.parse(open(CONFIG))
datos_XML = Handler.get_tags()

# Extraigo el fichero XML de los uaxml
USERNAME = datos_XML[0][1]['username']  # Es el nombre SIP
USER_PASS = datos_XML[0][1]['passwd']  # Es la contraseña SIP
UASERV_IP = datos_XML[1][1]['ip']  # Es el ip del servidor
UASERV_PORT = datos_XML[1][1]['puerto']  # Es el servidor del servidor
RTP_PORT = datos_XML[2][1]['puerto']  # Es el puerto del RTP
PROXY_IP = datos_XML[3][1]['ip']  # Es la IP del PROXY
PROX_PORT = datos_XML[3][1]['puerto']  # Es el puerto del PROXY
log_path = datos_XML[4][1]['path']  # Es el fichero log
AUDIO_PATH = datos_XML[5][1]['path']  # Es el audio log 

# Creo socket, y lo conecto al proxy
my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
my_socket.connect((PROXY_IP, int(PROX_PORT)))


# Defino el log para poner escribir en el fichero
def Wlog(log_path, tiempo, event):
    """utilizo "a" para no sobreescribir el contenido."""
    fich = open(log_path, "a")
    tiempo = time.gmtime(float(tiempo))
    fich.write = time.strftime('%Y%m%d%H%M%S', tiempo)
    event = event.replace('\r\n', ' ')
    fich.write(event + '\r\n')
    fich.close()


# Inicializo el Log
event = 'Empezando...'
tiempo = time.time()
Wlog(log_path, tiempo, event)

# Dependiendo del metodo envia diferentes mensajes 
if METHOD == "REGISTER":
    SEND = "REGISTER sip:" + USERNAME + ":" + UASERV_PORT
    SEND += " SIP/2.0\r\n" + "Expires: " + OPTION + "\r\n"
    # Añado el contenido en el log 
    tiempo = time.time()
    event = "Envio a " + PROXY_IP + ':' + PROX_PORT + ':' + SEND
    Wlog(log_path, tiempo, event)
    print('Enviando...:', SEND)
    my_socket.send(bytes(SEND, 'utf-8') + b'\r\n\r\n')  # lo pasamos a bytes   
    DAT = my_socket.recv(1024)
    recv = DAT.decode('utf-8')
    DATA = recv.split()
    print('Recibo del proxy...', recv)
    # Añado la respuesta en el fichero log 
    event = "Recibo de " + PROXY_IP + ':' + PROX_PORT + ':' + SEND
    tiempo = time.time()
    Wlog(log_path, tiempo, event)
    # Voy a mandar la autentificacion del usuario
    if DATA[1] == '401':
       # Creo el nonce para enviarlo
       env_nonce = recv.split(' ')[2].split(':')[0].split('=')[1]
       nonces = bytes(str(env_nonce), 'utf-8')
       contra = bytes(USER_PASS, 'utf-8')
       # Creo el response
       m = hashlib.md5()
       m.update(contra + nonces)
       response = m.hexdigest()
       # Mando la respuesta con el response y nonce
       SEND = METHOD + " sip:" + USERNAME + ":" + UASERV_PORT
       SEND += " SIP/2.0\r\n" + "Expires: " + OPTION + "\r\n"
       SEND += 'Authorization: Digest response=' + str(response) + " "
       SEND += 'nonce' + env_nonce + '\r\n'
       # Lo envio al proxy
       print("Enviando al proxy -- ", SEND)
       my_socket.send(bytes(SEND, 'utf-8') + b'\r\n\r\n')
       # Lo guardo en el log
       event = "Envio a " + PROXY_IP + ':' + PROX_PORT + ':' + SEND
       tiempo = time.time()
       Wlog(log_path, tiempo, event)
       DAT = my_socket.recv(int(PROX_PORT))
       recv = DAT.decode('utf-8')
       print('Recibido...', recv)
       # Lo escribo en el log
       event = "Recibo de " + PROXY_IP + ':' + PROX_PORT + ':' + SEND
       tiempo = time.time()
       Wlog(log_path, tiempo, event)
       linea = recv.split('\r\n')
       nrecv = linea[0].split(' ')[1]
       
# En caso de recibir un INVITE

elif METHOD == "INVITE":
     SEND = METHOD + " sip:" + OPTION + " SIP/2.0 \r\n\r\n"
     SEND += "Content-Type: application/sdp \r\n" + "v=0 \r\n"
     SEND += "o=" + USERNAME + " " + UASERV_IP + "\r\n"
     SEND += "s=lasesion \r\n" + "t=0 \r\n" + "m=audio "
     SEND += AUDIO_PATH + " RTP \r\n\r\n"
     # Lo envio al proxy
     print("Enviando -- ", SEND)
     my_socket.send(bytes(SEND, 'utf-8') + b'\r\n')
     # Lo guardo en el log
     event = "Envio a " + PROXY_IP + ':' + PROX_PORT + ':' + SEND
     tiempo = time.time()
     Wlog(log_path, tiempo, event)
     DAT = my_socket.recv(int(PROX_PORT))
     recv = DAT.decode('utf-8')
     print('Recibido...', recv)
     # Lo escribo en el log
     event = "Recibo de " + PROXY_IP + ':' + PROX_PORT + ':' + SEND
     tiempo = time.time()
     Wlog(log_path, tiempo, event)
     linea = recv.split('\r\n')
     nrecv = linea[0].split(' ')[1]
     # Vamos a enviar el ACK
     if METHOD == 'INVITE' and int(nrecv) == 100:
         in1 = nrecv.split()[1]  # Recibo 100
         in2 = nrecv.split()[4]  # Recibo 180
         in3 = nrecv.split()[7]  #Recibo un 200
     if in1 == '100' and in2 == '200' and in3 == '200':
         SEND = "ACK sip:" + OPTION + " SIP/2.0 \r\n"
         print('Enviando:' + SEND)
         # Lo guardo en el log
         event = "Envio a " + PROXY_IP + ':' + PROX_PORT + ':' + SEND
         tiempo = time.time()
         Wlog(log_path, tiempo, event)
         DAT = my_socket.send(bytes(SEND, 'utf-8') + b'\r\n\r\n')
         aEjecutar = ("./mp32rtp -i " + UASERV_IP + " -p " + UASERV_PORT + '< '
                      + AUDIO_PATH)
         print('Vamos a ejecutar', aEjecutar)
         os.system(aEjecutar)
         print('La ejecucion ha acabado')  
 # En caso de enviar un BYE   
elif METHOD == 'BYE':
     SEND = METHOD + " sip:" + OPTION + " SIP/2.0 \r\n\r\n"
     print("Enviando -- ", SEND)
     # Lo guardo en el log
     event = "Envio a " + PROXY_IP + ':' + PROX_PORT + ':' + SEND
     tiempo = time.time()
     Wlog(log_path, tiempo, event)   
     my_socket.send(bytes(SEND, 'utf-8') + b'\r\n\r\n')
     DAT = my_socket.recv(int(PROX_PORT))
     recv = DAT.decode('utf-8')
     print('Recibido...', recv)   
     # Lo guardo en el log
     event = "Recibo de " + PROXY_IP + ':' + PROX_PORT + ':' + SEND
     tiempo = time.time()
     Wlog(log_path, tiempo, event)

   
else:
     SEND = METHOD + " sip:" + OPTION + " SIP/2.0 \r\n\r\n"
     error = ("SIP/2.0 400  Bad Request\r\n\r\n")
     event = "Error: " + error
     tiempo = time.time()
     Wlog(log_path, tiempo, event)

# Terminamos el socket   
print('Terminando Socket...')
my_socket.close()
event = 'Finzalizando...'
tiempo = time.time()
Wlog(log_path, tiempo, event)
