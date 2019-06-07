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
        """Metodo para recibir y establecer comunicación SIP."""
        # Escribe dirección y puerto del cliente (de tupla client_address)
        client_ip = str(self.client_address[0])
        client_port = str(self.client_address[1])
        print("IP cliente: " + client_ip + "| Puerto cliente: " + client_port)

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
    Serv_Handler = UAServerhandler()
    parser.setContentHandler(Serv_Handler)
    parser.parse(open(CONFIG_XML))
    XML_Server = Serv_Handler.get_tags()
