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


class XMLClient(ContentHandler):
    """Clase que extrae e imprime el xml del cliente."""

    def __init__(self):
        """Inicializo las variabes."""
        self.Lista_client = []

    def startElement(self, element, attrs):
        """Crea las etiquetas y tributos del xml."""
        self.dicc_etiq = {'account': ['username', 'passwd'],
                          'uaserver': ['ip', 'puerto'],
                          'rtpaudio': ['puerto'],
                          'regproxy': ['ip', 'puerto'],
                          'log': ['path'],
                          'audio': ['path']
                         }
        if element in self.dicc_etiq:
            Dict = {}
            # Recorre los atributos y los guarda en Dict_server
            for atrib in self.dicc_etiq[element]:
                Dict[atrib] = attrs.get(atrib, "")
            # Guarda sin sustituir lo que habia dentro
            self.Lista_client.append([element, Dict])

    def get_tags(self):
        """Devuelve los datos del xml del cliente."""
        return self.Lista_client


if __name__ == "__main__":
    # Argumentos y errores
    if len(sys.argv) == 4:
        try:
            CONFIG = sys.argv[1]
            METHOD = sys.argv[2]
            OPTION = sys.argv[3]
        except:
         sys.exit('Usage: python3 uaclient.py config metho opcion')

        # Creo el socket para parsear el XML y trabajar con el
        parser = make_parser()
        Handler = XMLClient()
        parser.setContentHandler(Handler)
        parser.parse(open(CONFIG))
        datos_XML = Handler.get_tags() # Dicc con atributos

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

        # Creo y configuro socket
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Conecto al proxy
        my_socket.connect((PROXY_IP, int(PROX_PORT)))
        # Dependiendo del metodo envia diferentes mensajes 
        DATOS = []
        if METHOD == "REGISTER":
            SEND = METHOD + ' sip:' + USERNAME + ':' + UASERV_PORT
            SEND += ' SIP/2.0\r\n' + 'Expires: ' + OPTION + '\r\n\r\n'
            # Envio peticion
            print("Enviando al Proxy:\r\n", SEND)
            my_socket.send(bytes(SEND, 'utf-8'))  # pasamos a bytes
            # Recibo respuesta
            DATA = my_socket.recv(1024)
            recv = DATA.decode('utf-8')
            print("Recibo del proxy:\r\n", recv)
            DATAS = DATA.decode('utf-8').split()
            # Voy a mandar la autentificacion del usuario
            if DATAS[1] == "401":
                nonce = DATA.decode('utf-8').split()[-1].split("=")[-1]
                H = hashlib.sha224(bytes(USER_PASS, 'utf-8'))
                H.update(bytes(nonce, 'utf-8'))
                resp = H.hexdigest()
                SEND = METHOD + ' sip:' + USERNAME + ":" + UASERV_PORT
                SEND += ' SIP/2.0\r\n' + 'Expires: ' + OPTION + '\r\n'
                SEND += 'Authorization: Digest response = '
                SEND += resp + '\r\n\r\n'
                # Lo envio al proxy
                print("Enviando al proxy...\r\n", SEND)
                my_socket.send(bytes(SEND, 'utf-8') + b'\r\n')
                # Recibo respuesta y antes lo compruebo
                DATA = my_socket.recv(1024)
                recv = DATA.decode('utf-8')
                print('Recibido del proxy...\r\n', recv)
        # En caso de recibir un INVITE
        elif METHOD == "INVITE":
             SEND = METHOD + ' sip:' + OPTION + ' SIP/2.0\r\n\r\n'
             SEND += 'Content-Type: application/sdp\r\n' + 'v=0\r\n'
             SEND += 'o=' + USERNAME + ' ' + UASERV_IP + '\r\n'
             SEND += 's=lasesion \r\n' + 't=0\r\n' + 'm=audio '
             SEND += str(RTP_PORT) + ' RTP \r\n'
             # Envio peticion
             print('Enviando:\r\n', SEND)
             my_socket.send(bytes(SEND, 'utf-8') + b'\r\n') # pasamos a bytes
             # Recibo respuesta
             DATA = my_socket.recv(1024)
             print('Recibido...', DATA.decode('utf-8'))
             DATS = DATA.decode('utf-8').split()
             # Segun lo que reciba mando diferentes cosas                      
             if DATS[1] == "100" and DATS[4] == "180" and DATS[7] == "200":
                # Vamos a enviar el ACK
                SEND = 'ACK sip:' + USERNAME + ' SIP/2.0 \r\n'
                print('Enviando:', SEND)
                my_socket.send(bytes(SEND, 'utf-8') + b'\r\n\r\n')
                # Envio mp3
                print('He enviado el ACK, mando RTP')
                aEjecutar = './mp32rtp -i ' + UASERV_IP + ' -p ' + UASERV_PORT 
                aEjecutar += ' < ' + AUDIO_PATH
                print('Vamos a ejecutar = ', aEjecutar)
                os.system(aEjecutar)
                print('La transmision RTP ha finalizado')
                aEjecutar_cvlc = 'cvlc rtp://' + str(UASERV_IP) + ':'
                aEjecutar_cvlc += str(UASERV_PORT) + ' 2> /dev/null'
                print('Vamos a ejecutar = ', aEjecutar_cvlc)
                os.system(aEjecutar_cvlc + '&')
        # En caso de recibir un BYE
        elif METHOD == "BYE":
            SEND = METHOD + " sip:" + USERNAME + " SIP/2.0\r\n"
            print('Enviando:\r\n', SEND)
            my_socket.send(bytes(SEND, 'utf-8') + b'\r\n\r\n')
            DATA = my_socket.recv(1024)
            print('Recibido ---', DATA.decode('utft-8')) 
        else:
            sys.exit("Solo puedes enviar = REGISTER, INVITE o BYE")
            # Terminamos el socket   
            print('Finalizando...')
        print('Terminando socket...')
        my_socket.close()
