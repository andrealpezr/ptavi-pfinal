#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Programa para un Servidor de eco en UDP simple."""

import os
import sys
import socketserver
import time
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from uaclient import Wlog


class XMLServer(ContentHandler):
    """Clase que extrae e imprime el xml del servidor."""

    def __init__(self):
        """Inicializo las variabes."""
        self.Lista_server = []

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
            for atrib in self.dicc_etiq_server[element]:
                Dict_server[atrib] = attrs.get(atrib, "")
            self.Lista_server.append([element, Dict_server])

    def get_tags(self):
        """Devuelve los datos del xml del cliente."""
        return self.Lista_server


class EchoHandler(socketserver.DatagramRequestHandler):
    """Client handler requests."""

    def handle(self):
        """Escribe direccion y puerto del cliente."""
        while 1:
            # Lee linea a linea lo que recibe del cliente
            line = self.rfile.read()
            lines = line.decode('utf-8')
            print('Recibido del cliente--' + lines)
            # Añado lo que recibo en el fichero log 
            event = "Recibo de " + PROXY_IP + ':' + PROX_PORT + ':' + lines
            tiempo = time.time()
            Wlog(log_path, tiempo, event)
            lin = lines.split(' ')            
            METOD = lin[0]
            if METOD == 'INVITE' or METOD == 'invite':
               to_send = ('SIP/2.0 100 Trying\r\n\r\n' +
                          'SIP/2.0 180 Ringing\r\n\r\n' +
                          'SIP/2.0 200 OK\r\n\r\n')
                   # SDP con el 200 ok
               sdp = ("Content-Type: application/sdp\r\n\r\n" +
                      'v=0\r\n' + "o=" + USERNAME + ' ' + UASERV_IP +
                      '\r\n' + 's=lasesion\r\n' + 'm=audio ' + 
                      str(RTP_PORT) + ' RTP\r\n\r\n')
               mensaje = to_send + sdp
               self.wfile.write(bytes(mensaje, 'utf-8'))
               event = ("Recibo de " + PROXY_IP + ':' + PROX_PORT + ':' + 
                        mensaje)
               tiempo = time.time()
               Wlog(log_path, tiempo, event)               

            elif METOD == 'ACK' or METOD == 'ack':
                 aEjecutarVLC = 'cvlc rtp://@127.0.0.1:'
                 aEjecutarVLC += RTP_PORT + '2> /dev/null '
                 os.system(aEjecutarVLC)
                 aEjecutar = './mp32rtp -i ' + UASERV_IP
                 aEjecutar = aEjecutar + ' -p ' + RTP_PORT + '<' + AUDIO_PATH
                 print("Vamos a ejecutar", aEjecutar)
                 os.system(aEjecutar)
                 print('La ejecucion ha terminado')
            elif METOD == 'BYE' or METOD == 'BYE':
                to_send = 'SIP/2.0 200 OK\r\n\r\n'
            else:
                to_send = 'SIP/2.0 400 Bad Request\r\n\r\n'

    
if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python3 uaserver.py config")

    CONFIG = sys.argv[1]
    parser = make_parser()
    Handler = XMLServer()
    parser.setContentHandler(Handler)
    parser.parse(open(CONFIG))
    datos_XML = Handler.get_tags()

    # Extraigo el fichero XML
    USERNAME = datos_XML[0][1]['username']  # Es el nombre SIP
    USER_PASS = datos_XML[0][1]['passwd']  # Es la contraseña SIP
    UASERV_IP = datos_XML[1][1]['ip']  # Es el ip del servidor
    UASERV_PORT = datos_XML[1][1]['puerto']  # Es el servidor del servidor
    RTP_PORT = datos_XML[2][1]['puerto']  # Es el puerto del RTP
    PROXY_IP = datos_XML[3][1]['ip']  # Es la IP del PROXY
    PROX_PORT = datos_XML[3][1]['puerto']  # Es el puerto del PROXY
    log_path = datos_XML[4][1]['path']  # Es el fichero log
    AUDIO_PATH = datos_XML[5][1]['path']  # Es el audio log 

    SERV = socketserver.UDPServer((UASERV_IP, int(UASERV_PORT)), EchoHandler)
    print('Listening...\r\n')
    try:
        SERV.serve_forever()
    except FileNotFoundError:
            sys.exit('File not found!')
    except IndexError:
            sys.exit("Usage: python3 uaserver.py config")
    except KeyboardInterrupt:
            print("\r\nFinalizado el servidor")
