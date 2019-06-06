#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Hago el cliente para una comunicación SIP."""

import socket
import sys
import os
import time
import hashlib
from xml.sax import make_parser
from xml.sax.handler import ContentHandler


class UAclienthandler(ContentHandler):
    """Clase que extrae e imprime el xml del cliente """

    def __init__(self):
        """Inicializamos las variabes."""
        self.Lista = []

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
            for atrib in self.dicc_etiq[element]:
                Dict[atrib] = attrs.get(atrib, "")
                self.Lista.append([element, Dict])

    def get_tags(self):
        """Devuelve los datos del xml del cliente."""
        return self.Lista


if __name__ == "__main__":

    try:
        CONFIG_XML = sys.argv[1]
        METODO = sys.argv[2]
        OPCION = sys.argv[3]
    except(IndexError, ValueError):
        sys.exit('Usage: python3 uaclient.py config method option')
 
    # Creamos socket para parsear el XML
    parser = make_parser()
    cHandler = UAclienthandler()
    parser.setContentHandler(cHandler)
    parser.parse(open(CONFIG_XML))
    XML_list = cHandler.get_tags()
    
    # Damos valores a las variables del XML
    USERNAME = XML_list[0][1]['username']  # Es el nombre SIP
    USER_PASS = XML_list[0][1]['passwd']  # Es la contraseña SIP
    UASERV_IP = XML_list[2][1]['ip']  # Es el ip del servidor
    UASERV_PORT = XML_list[2][1]['puerto']  # Es el servidor del servidor
    RTP_PORT = XML_list[4][1]['puerto']  # Es el puerto del RTP
    PROXY_IP = XML_list[6][1]['ip']  # Es la IP del PROXY
    PROX_PORT = XML_list[6][1]['puerto']  # Es el puerto del PROXY
    LOG_PATH = XML_list[7][1]['path']  # Es el fichero log
    AUDIO_PATH = XML_list[8][1]['path']  # Es el audio log

    # Creamos el socket para conectarlo al proxy
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.connect((PROXY_IP, int(PROX_PORT)))

    h = hashlib.md5()
    Digest_Resp = h.hexdigest()

    if METODO == "REGISTER":
        TO_SEND = METODO + ' sip:' + USERNAME + ":" + UASERV_PORT
        TO_SEND += ' SIP/2.0\r\nExpires: ' + OPCION + '\r\n'
        print("Enviando:", TO_SEND)
        my_socket.send(bytes(TO_SEND, 'utf-8') + b'\r\n')
        DATA = my_socket.recv(1024)
        print('Recibido --', DATA.decode('utf-8'))
       
        list_rec = DATA.decode('utf-8').split()
        if list_rec[1] == "401":
            TO_SEND = METODO + " sip:" + USERNAME + ":" + UASERV_PORT
            TO_SEND += " " + "SIP/2.0\r\n" + "Expires: " + OPCION + " \r\n"
            TO_SEND += 'Authorizacion: Digest response= ' + Digest_Resp
            TO_SEND += "\r\n"
            print("Enviando:", TO_SEND)
            my_socket.send(bytes(TO_SEND, 'utf-8') + b'\r\n')
            datos = my_socket.recv(1024)
        print('Recibido --', datos.decode('utf-8'))

    elif METODO == "INVITE":
            TO_SEND = METODO + " sip:" + OPCION + ' ' + "SIP/2.0\r\n"
            TO_SEND += "Content-Type: application/sdp\r\n\r\n" + "v=0\r\n" + "o="
            TO_SEND += 'o' + USERNAME + ' ' + UASERV_IP + "\r\n" 
            TO_SEND += "s=misession\r\n" + "t=0\r\n" + "m=audio " + RTP_PORT 
            TO_SEND += " RTP\r\n\r\n"
            print("Enviando:", TO_SEND)
            my_socket.send(bytes(TO_SEND, 'utf-8') + b'\r\n')
            DATA = my_socket.recv(1024)
            print('Recibido --', DATA.decode('utf-8'))
            list_rec = DATA.decode('utf-8').split()
            if list_rec[1] == "100" and ((list_rec[4] == "180") and 
                                          (list_rec[7] == "200")):
                METODO = "ACK"
                TO_SEND = METODO + " sip:" + USERNAME + " SIP/2.0\r\n"
                print("Enviando", TO_SEND)
                my_socket.send(bytes(TO_SEND, 'utf-8') + b'\r\n')
                aEjecutar = "./mp32rtp -i " + UASERV_IP + " -p 23032 < "
                aEjecutar += AUDIO_PATH
                print("Vamos a ejecutar", aEjecutar)
                os.system(aEjecutar)

    elif METODO == "BYE":
            TO_SEND = METODO + " sip:" + USERNAME + ' ' + " SIP/2.0\r\n"
            print("Enviando", TO_SEND)
            my_socket.send(bytes(TO_SEND, 'utf-8') + b'\r\n')
            DATA = my_socket.recv(1024)
            print('Recibido --', DATA.decode('utf-8'))
    else:
        sys.exit("Usage: python uaclient.py config method option")
print("Terminando socket...")
