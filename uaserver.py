#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hago el servidor para una comunicacion SIP."""

import socket
import socketserver
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import time
from datetime import date
import os


class UAServerhandler(ContentHandler):
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
    """Echo server class."""

    def handle(self):
        """Metodo para establecer comunicacion SIP."""
        while 1:
            # Lee línea a línea lo que nos envía el cliente
            read_line = self.rfile.read()
            # Si no hay más líneas salimos del bucle infinito
            if not read_line:
                break
            # Evaluación de los parámetros que nos envía el proxy
            print("El proxy nos manda: " + read_line.decode('utf-8'))
            lines = read_line.decode('utf-8')
            print(lines.split())
            METODO = lines.split(' ')[0]
            if METODO == "INVITE":
                ok = "SIP/2.0 200 OK" + '\r\n' + '\r\n'
                TO_SEND = ok
                TO_SEND += "Content-Type: application/sdp\r\n\r\n"
                TO_SEND += "v=0\r\n" + "o=" + USERNAME + ' '
                TO_SEND += UASERV_IP + "\r\n" + "s=misession\r\n"
                TO_SEND += "t=0\r\n" + "m=audio " + RTP_PORT
                TO_SEND += " RTP\r\n\r\n"
                self.wfile.write(b"SIP/2.0 100 Trying" + b"\r\n"
                                 b"SIP/2.0 180 Ring" + b"\r\n")
                self.wfile.write(bytes(TO_SEND, 'utf-8'))
            elif METODO == "ACK":
                aEjecutar = './mp32rtp -i " + UASERV_IP + " -p 23032 < '
                aEjecutar += AUDIO_PATH
                print("Vamos a ejecutar", aEjecutar)
                os.system(aEjecutar)
            elif METODO == "BYE":
                self.wfile.write(b"SIP/2.0 200 OK" + b"\r\n")
            elif METODO != "REGISTER" or "INVITE" or "ACK":
                self.wfile.write(b"SIP/2.0 405 Method Not Allowed" + b"\r\n")
            else:
                self.wfile.write(b"SIP/2.0 400 Bad Request" + b"\r\n")


if __name__ == "__main__":

    try:
        CONFIG_XML = sys.argv[1]
    except(IndexError, ValueError):
        sys.exit('Usage: python uaserver.py config')

    # Creamos socket para parsear el XML
    parser = make_parser()
    cHandler = UAServerhandler()
    parser.setContentHandler(cHandler)
    parser.parse(open(CONFIG_XML))
    XML_serv = cHandler.get_tags()

    # Damos valores a las variables del XML
    USERNAME = XML_serv[0][1]['username']  # Es el nombre SIP
    USER_PASS = XML_serv[0][1]['passwd']  # Es la contraseña SIP
    UASERV_IP = XML_serv[1][1]['ip']  # Es el ip del servidor
    UASERV_PORT = XML_serv[1][1]['puerto']  # Es el servidor del servidor
    RTP_PORT = XML_serv[2][1]['puerto']  # Es el puerto del RTP
    PROXY_IP = XML_serv[3][1]['ip']  # Es la IP del PROXY
    PROX_PORT = XML_serv[3][1]['puerto']  # Es el puerto del PROXY
    LOG_PATH = XML_serv[4][1]['path']  # Es el fichero log
    AUDIO_PATH = XML_serv[5][1]['path']  # Es el audio log

    # Creo socket para parsear el XML
    parser = make_parser()
    Serv_Handler = UAServerhandler()
    parser.setContentHandler(Serv_Handler)
    parser.parse(open(CONFIG_XML))
    XML_Server = Serv_Handler.get_tags()

    # Conecto socket al servidor
    my_socket_server = socketserver.UDPServer((UASERV_IP, int(UASERV_PORT)),
                                              UAServerhandler)
    print("Listening")
    my_socket_server.serve_forever()
