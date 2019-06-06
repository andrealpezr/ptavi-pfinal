#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Realizamos el cliente """

import os
import socket
import sys
import time
from xml.sax import make_parser
from xml.sax.handler import ContentHandler


class UAclienthandler(ContentHandler):
    """Clase del xml del cliente """
    config = {}

    def __init__(self):
        """Inicializamos las variables."""
        self.dicc_etiq = {'account': ['username', 'passwd'],
                          'uaserver': ['ip', 'puerto'],
                          'rtpaudio': ['puerto'],
                          'regproxy': ['ip', 'puerto'],
                          'log': ['path'],
                          'audio': ['path']
                          }

    def startElement(self, element, attrs):
        """Crea los datos del xml del cliente."""
        if element in self.dicc_etiq:
            for atrib in self.dicc_etiq[element]:
                self.config[element+ '_' + atrib] = attrs.get(atrib, "")

    def get_tags(self):
        """Devuelve los datos del xml del cliente."""
        return self.config

    def log(self, accion, linea, fich_log):
        fich = open(fich_log, "a")
        now = time.gmtime(time.time())  
        hora = time.strftime('%Y%m%d%H%M%S', now)
        line = linea.split('\r\n')
        texto = ' '.join(line)

        fich.write(hora + "\t" + accion + "\t" + texto + "\r\n")



if __name__ == "__main__":

    try:
        CONFIG_XML = sys.argv[1]
        metodo = sys.argv[2]
        METODO = metodo.upper()
    except(IndexError, ValueError):
        sys.exit('Usage: python3 uaclient.py config method option')
 
    # Creamos socket para parsear el XML
    parser = make_parser()
    cHandler = UAclienthandler()
    parser.setContentHandler(cHandler)
    parser.parse(open(CONFIG_XML))
    lista_etiq = cHandler.get_tags()

