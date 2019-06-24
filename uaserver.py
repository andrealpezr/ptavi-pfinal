#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Programa para un Servidor de eco en UDP simple."""

import os
import sys
import socketserver
import time
from xml.sax import make_parser
from xml.sax.handler import ContentHandler


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
            print('Recibo del proxy--' + lines)
            # Si hay linea en blanco sale del bucle
            if not lines:
                break
            mensaje = lines.split('\r\n')  
            linea = mensaje[0].split()
            METOD = linea[0]
            if METOD == 'INVITE' or METOD == 'invite':
               # Lo envio tras recibir el INVITE
               self.wfile.write(b'SIP/2.0 100 Trying' + b'\r\n\r\n')
               self.wfile.write(b'SIP/2.0 180 Ringing' + b'\r\n\r\n')
               ok = 'SIP/2.0 200 OK\r\n\r\n'
               sdp = 'Content-Type: application/sdp \r\n\r\n' + 'v=0 \r\n'
               sdp += "o=" + USERNAME + " " + UASERV_IP + '\r\n'
               sdp += 's=lasesion \r\n' + 't=0\r\n' + 'm=audio '
               sdp += str(RTP_PORT) + ' RTP \r\n\r\n'
               # Envio peticion
               peticion = ok + sdp
               self.wfile.write(bytes(peticion, 'utf-8'))
               print('Envio al proxy:\r\n', peticion)
            elif METOD == 'ACK' or METOD == 'ack':
                # Tras recibir el ack mando el rtp
                print('He recibido el ACK, envio RTP')
                aEjecutar = './mp32rtp -i ' + UASERV_IP + " -p "
                aEjecutar +=  UASERV_PORT + ' < ' + AUDIO_PATH
                print('Vamos a ejecutar', aEjecutar)
                os.system(aEjecutar)
                print('La ejecucion  RTP ha finalizado \r\n')
                aEjecutar_cvlc = 'cvlc rtp://' + str(UASERV_IP) + ':'
                aEjecutar_cvlc += str(UASERV_PORT) + ' 2> /dev/null'
                print('Vamos a ejecutar = ', aEjecutar_cvlc)
                os.system(aEjecutar_cvlc + '&')
            # En caso de recibir un BYE
            elif METOD == 'BYE' or METOD == 'bye':
                bye = b'SIP/2.0 200 OK\r\n\r\n'
                print('Mando al proxy:\r\n SIP/2.0 200 OK\r\n\r\n')
                self.wfile.write(bye)
            else:
                 self.wfile.write(b'SIP/2.0 400 Bad Request\r\n\r\n')


if __name__ == "__main__":
   
    if len(sys.argv) == 2:
        CONFIG = sys.argv[1]

        # Creo el socket para parsear el XML y trabajar con el
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
        # Defino el log para poner escribir en el fichero

        SERV = socketserver.UDPServer((UASERV_IP, int(UASERV_PORT)),
                                      EchoHandler)
        print('Listening...\r\n')
        try:
            SERV.serve_forever()
        except FileNotFoundError:
                sys.exit('File not found!')
        except IndexError:
                sys.exit("Usage: python3 uaserver.py config")
        except KeyboardInterrupt:
                print("\r\nFinalizado el servidor")
    else:
        sys.exit('Usage: python3 uaserver.py config')
