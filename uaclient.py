#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Realizamos el cliente """

import hashlib
import os
import socket
import sys
import time
import threading
from xml.sax import make_parser
from xml.sax.handler import ContentHandler

 
class UAclienthandler(ContentHandler):
    """Clase """

    def __init__(self):
        """Inicializamos las variables."""
        self.lista_etiq = {}
        self.dicc_etiq = {'account': ['username', 'passwd'],
                          'uaserver': ['ip', 'puerto'],
                          'rtpaudio': ['puerto'],
                          'regproxy': ['ip', 'puerto'],
                          'log': ['path'],
                          'audio': ['path']
                          }

    def startElement(self, element, attrs):
        """Crea los datos del xml del cliente."""
        if element in self.lista_etiq:
            for atrib in self.dicc_etiq[element]:
                self.lista_etiq[element+ '_' + atrib] = attrs.get(atrib, "")

    def get_tags(self):
        """Devuelve los datos del xml del cliente."""
        return self.lista_etiq




if __name__ == "__main__":

    if len(sys.argv) != 4:
       sys.exit('Usage: python3 uaclient.py config method option')

    CONFIGU = sys.argv[1]
    if not os.path.exists(CONFIGU):
        sys.exit('Config does not exists')

    METHOD = sys.argv[2]
    LIST = ['REGISTER', 'INVITE', 'BYE']
    if METHOD not in LIST:
        sys.exit('SIP/2.0 405 Method Not Allowed\r\n')

    OPTION = sys.argv[3]

    # sacamos el xml
    parser = make_parser()
    xmlHandler = UAclienthandler()
    parser.setContentHandler(xmlHandler)
    parser.parse(open(CONFIGU))
    XML_List = xmlHandler.get_tags()
  
 
