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


















