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
        self.Lista_serv = []

    def startElement(self, element, attrs):
        """Crea las etiquetas y tributos del xml. Busca nombres, no guarda."""
        self.dicc_etiq = {'account': ['username', 'passwd'],
                          'uaserver': ['ip', 'puerto'],
                          'rtpaudio': ['puerto'],
                          'regproxy': ['ip', 'puerto'],
                          'log': ['path'],
                          'audio': ['path']}
        if element in self.dicc_etiq:
            Dict = {}
            # Recorre los atributos y los guarda en Dict
            for atrib in self.dicc_etiq[element]:  # Busco en etiquetas=element
                Dict[atrib] = attrs.get(atrib, "")
            # Guarda sin sustituir lo que habia dentro
            self.Lista_serv.append([element, Dict])

    def get_tags(self):
        """Devuelve los datos del xml del cliente."""
        return self.Lista_serv


class EchoHandler(socketserver.DatagramRequestHandler):
    """Client handler requests."""

    USER = []
    PORT = []

    def handle(self):
        """Escribe direccion y puerto del cliente."""
        # Lee linea a linea lo que recibe del cliente
        line = self.rfile.read()
        recibo = line.decode('utf-8')
        lines = recibo.split()
        print('Recibo del Proxy...' + 'r\n' + recibo)
        METOD = lines[0]
        if METOD == 'INVITE' or METOD == 'invite':
            self.USER.append(lines[7])
            self.PORT.append(lines[11])
            # Lo envio tras recibir el INVITE del Proxy
            SEND = 'SIP/2.0 100 Trying' + 'r\n\r\n'
            SEND += 'SIP/2.0 180 Ringing' + 'r\n\r\n'
            ok = 'SIP/2.0 200 OK' + '\r\n'
            sdp = ok
            sdp += 'Content-Type: application/sdp \r\n\r\n' + 'v=0 \r\n'
            sdp += "o=" + USERNAME + " " + UASERV_IP + '\r\n'
            sdp += 's=lasesion \r\n' + 't=0\r\n' + 'm=audio '
            sdp += RTP_PORT + ' RTP \r\n'
            # Envio peticion
            ALL = (SEND + sdp)
            self.wfile.write(bytes(ALL, 'utf-8') + b'\r\n')
            print('Enviamos al cliente...' + '\r\n' + ALL)
        elif METOD == 'ACK' or METOD == 'ack':
            # Tras recibir el ack mando el rtp
            print('He recibido el ACK, envio RTP')
            aEjecutar = './mp32rtp -i ' + UASERV_IP + " -p "
            aEjecutar += RTP_PORT + ' < ' + AUDIO_PATH
            print('Vamos a ejecutar ', aEjecutar)
            os.system(aEjecutar)
            print('La ejecucion  RTP ha finalizado')
            # En caso de recibir un BYE
        elif METOD == 'BYE' or METOD == 'bye':
            ok = 'SIP/2.0 200 OK\r\n'
            self.wfile.write(bytes(ok, 'utf-8') + b'\r\n')
            print('Enviamos al Proxy...' + '\r\n' + ok)
            # En caso de introducir mal el metodo
        elif METOD not in ['REGISTER', 'INVITE', 'BYE', 'ACK']:
            mal_metodo = 'SIP/2.0 405 Method Not Allowed\r\n\r\n'
            self.wfile.write(bytes(mal_metodo))
        elif ConnectionRefusedError:
            self.wfile.write(b'SIP/2.0 Connection Refused' + b'\r\n\r\n')
            sys.exit()
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
        print('Listening...\n')
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
