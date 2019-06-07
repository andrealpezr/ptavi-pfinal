#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Programa principal del proxy para comunicacion SIP."""

import socket
import socketserver
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import time
from datetime import date
import os


class UA_Proxy(ContentHandler):
    """Clase que extrae e imprime el xml del cliente """

    def __init__(self):
        """Inicializo las variabes."""
        self.Lista_prox = []

    def startElement(self, element, attrs):
        """Crea las etiquetas y tributos del xml."""
        self.dicc_etiq_prox = {'server': ['name', 'ip', 'puerto'],
                               'database': ['path', 'passdpath'],
                               'log': ['path']}
        if element in self.dicc_etiq_prox:
            Dict_prox = {}
            for atrib in self.dicc_etiq_prox[element]:
                Dict_prox[atrib] = attrs.get(atrib, "")
            self.Lista_prox.append([element, Dict_prox])

    def get_tags(self):
        """Devuelve los datos del xml del cliente."""
        return self.Lista_prox

   
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
            print("El cliente nos envia: " + read_line.decode('utf-8'))
            lines = read_line.decode('utf-8')
            METODO = lines.split(' ')[0]

            if METODO == "REGISTER":
                print(lines.split())


if __name__ == "__main__":

    try:
        CONFIG_XML = sys.argv[1]
    except(IndexError, ValueError):
        sys.exit('Usage: python3 proxy_registrar.py config')

    # Creamos socket para parsear el XML
    parser = make_parser()
    prox_Handler = UA_Proxy()
    parser.setContentHandler(prox_Handler)
    parser.parse(open(CONFIG_XML))
    XML_prox= prox_Handler.get_tags()

    # Damos valores a las variables del XML
    PROXY_IP = XML_prox[0][1]['ip']  # Es la IP del PROXY
    PROX_PORT = XML_prox[0][1]['puerto']  # Es el puerto del PROXY

    # Conecto socket al proxy
    my_socket_prox = socketserver.UDPServer((PROXY_IP, PROX_PORT),
                                             EchoHandler)
    print('Server MyServer listening at port 6002... \r\n')
    my_socket_prox.serve_forever()
