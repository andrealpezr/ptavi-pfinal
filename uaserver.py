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
        """Metodo para establecer comunicación SIP."""
        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read()

            # Si no hay más líneas salimos del bucle infinito
            if not line:
                break
            else:
                # Evaluación de los parámetros que nos envía el cliente
                print ("Recibido:\n" + line)


if __name__ == "__main__":

    try:
        CONFIG_XML = sys.argv[1]
        METODO = sys.argv[2]
        OPCION = sys.argv[3]
    except(IndexError, ValueError):
        sys.exit('Usage: python uaserver.py config')

    # Creamos socket para parsear el XML
    parser = make_parser()
    cHandler = UAServerhandler()
    parser.setContentHandler(cHandler)
    parser.parse(open(CONFIG_XML))
    XML_serv = cHandler.get_tags()

    # Doy valores a las variables del XML
    USERNAME = XML_serv[0][1]['username']  # Es el nombre SIP
    USER_PASS = XML_serv[0][1]['passwd']  # Es la contraseña SIP
    UASERV_IP = XML_serv[2][1]['ip']  # Es el ip del servidor
    UASERV_PORT = XML_serv[2][1]['puerto']  # Es el servidor del servidor
    RTP_PORT = XML_serv[4][1]['puerto']  # Es el puerto del RTP
    PROXY_IP = XML_serv[6][1]['ip']  # Es la IP del PROXY
    PROX_PORT = XML_serv[6][1]['puerto']  # Es el puerto del PROXY
    LOG_PATH = XML_serv[7][1]['path']  # Es el fichero log
    AUDIO_PATH = XML_serv[8][1]['path']  # Es el audio log


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
