#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Programa para un Servidor de eco en UDP simple."""

import os
import sys
import socketserver
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

    USER = []

    def handle(self):
        """Escribe direccion y puerto del cliente."""
        while 1:
            # Lee linea a linea lo que recibe del cliente
            line = self.rfile.read()
            lines = line.decode('utf-8').split(' ')
            # Si hay linea en blanco sale del bucle
            if not lines:
                break
            reciv = ' '.join(lines)
            METOD = lines[0]
            if METOD == 'INVITE' or METOD == 'invite':
                # Lo envio tras recibir el INVITE del Proxy
                SEND = 'SIP/2.0 100 Trying...' + 'r\n\r\n'
                SEND += 'SIP/2.0 180 Ringing' + 'r\n\r\n'
                ok = 'SIP/2.0 200 OK' + '\r\n'
                sdp = ok
                sdp += 'Content-Type: application/sdp \r\n\r\n' + 'v=0 \r\n'
                sdp += "o=" + USERNAME + " " + UASERV_IP + '\r\n'
                sdp += 's=lasesion \r\n' + 't=0\r\n' + 'm=audio '
                sdp += RTP_PORT + ' RTP \r\n'
                # Envio peticion
                ALL = (SEND + sdp)
                print(ALL)
                self.wfile.write(bytes(ALL, 'utf-8'))
                IP_CLIENT = reciv.split('o=')[1].split(' ')[1].split('\r')[0]
                AUDIO_CLI = reciv.split('m=')[1].split(' ')[1].split(' R')[0]
                self.USER.append(IP_CLIENT)
                self.USER.append(AUDIO_CLI)
            if 'ACK' in lines:
                # Tras recibir el ack mando el rtp
                print(self.USER)
                print('He recibido el ACK, envio RTP')
                aEjecutar = './mp32rtp -i ' + self.USER[0] + " -p "
                aEjecutar += self.USER[1] + ' < ' + AUDIO_PATH
                print('Vamos a ejecutar ', aEjecutar)
                os.system(aEjecutar)
                print('La ejecucion  RTP ha finalizado \r\n')
            # En caso de recibir un BYE
            if METOD == 'BYE' or METOD == 'bye':
                print('Mando al proxy:\r\n SIP/2.0 200 OK\r\n\r\n')
                self.wfile.write(b'SIP/2.0 200 OK'+b'\r\n\r\n')
                break
            # En caso de introducir mal el metodo
            if METOD not in ['REGISTER', 'INVITE', 'BYE', 'ACK']:
                sys.exit('SIP/2.0 405 Method Not Allowed\r\n')
            if ConnectionRefusedError:
                self.wfile.write(b'SIP/2.0 Connection Refused'+b'\r\n\r\n')
                break
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
