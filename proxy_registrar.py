#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Programa del proxy."""

import socket
import socketserver
import sys
import os
import json
import random
import hashlib
import time
from xml.sax import make_parser
from xml.sax.handler import ContentHandler


class FicheroXML(ContentHandler):
    """Creamos la clase."""

    def __init__(self):
        """Inicializa los diccionarios."""
        self.diccionario = []
        self.dicc_ua1 = {'server': ['name', 'ip', 'puerto'],
                         'database': ['path', 'passwdpath'],
                         'log': ['path'],}

    def startElement(self, nam, attrs):
        """Crea las etiquetas del fichero xml."""
        if nam in self.dicc_ua1:
            Dicc = {}
            for atrib in self.dicc_ua1[nam]:
                Dicc[atrib] = attrs.get(atrib, "")
            self.diccionario.append([nam, Dicc])

    def get_tags(self):
        """Devuelve el diccionario creado."""
        return self.diccionario


def register2json(self):
    """Creo json file."""
    with open('registered.json', 'w') as fichero:
        json.dump(self.clientes, fichero, indent='\t')

def json2register(self):
    """Abre el fichero Json y nos da el diccionario anterior."""
    try:
        with open('registered.json', 'r') as fich:
            self.clientes = json.load(fich)
    except(FileNotFoundError or ValueError):
        self.register2json()


class SIPRegisterHandler(socketserver.DatagramRequestHandler):
    """Proxy class."""
    clientes = []
    user_add = []
    port = []

    def handle(self):
        """Segun los metodos que hacer."""
        while 1:
            # Leo linea a linea lo que recibo del cliente
            line = self.rfile.read()
            lines = line.decode('utf-8')
            # En caso de haber linea en blanco salgo del bucle
            if not lines:
                break
            print("El cliente nos manda..." + '\r\n' + lines)
            lista = lines.split(' ')
            # Segun el metodo que reciba, envio una cosa diferente
            met = lista[0]
            # En caso de recibir el metodo REGISTER
            if met == "REGISTER":
                if len(lista) < 6:
                    nonce = '879879897897978979989979\r\n'
                    Answer = 'SIP/2.0 401 Unauthorized' + '\r\n'
                    Answer += ('WWW Authenticate: ' + 'Digest nonce = ' +
                               str(nonce))
                    self.wfile.write(bytes(Answer, 'utf-8'))
                    print('Enviando al cliente...' + '\n' + Answer)
                elif len(lista) >= 5:
                   # Direccion del usuario
                   to_send = "SIP/2.0 200 OK\r\n"
                   self.wfile.write(bytes(to_send, 'utf-8'))
            # En caso de recibir un INVITE
            elif met == "INVITE":
                # Nombre a quien envio el INVITE
                PORT = lista[1][4:]
                for clien in self.clientes:
                    if clien[0] == PORT:
                        # Cojo la IP y puerto d el servidor del diccionario
                        IP = clien[1]['address']
                        Puert = int(clien[1]['port'])
                        try:
                            # Creo socket, y lo configuro
                            my_socket = socket.socket(socket.AF_INET,
                                                      socket.SOCK_DGRAM)
                            my_socket.setsockopt(socket.SOL_SOCKET,
                                                 socket.SO_REUSEADDR, 1)
                            # Lo ato al servidor
                            my_socket.connect((IP, int(Puert)))
                            self.user_add.append(IP)
                            self.port.append(Puert)
                            my_socket.send(bytes(lines, 'utf-8'))
                            data = my_socket.recv(int(Puert))
                            dat = data.decode('utf-8')
                            print('Recibo del servidor...', dat)
                            self.wfile.write(bytes(data.decode('utf-8'), 
                                                   'utf-8') + b'\r\n')
                        except ConnectionRefusedError:
                            envio = ('Error: no server listening at' + IP + 'port'
                                     + Puert)
                            print(envio)
                            self.wfile.write(bytes(envio, 'utf-8') + b'\r\n')
                    else:
                        self.wfile.write(bytes("SIP/2.0 404 User not found",
                                               'utf-8') + b'\r\n\r\n')
            elif met == 'ACK':
                user = lista[1].split(':')[1]
                # Cojo la IP y puerto del servidor del diccionario
                IP = self.Dicc[user][0]
                Puert = int(self.clientes[user][1])
                # Creo socket, y lo configuro
                my_socket = socket.socket(socket.AF_INET,
                                          socket.SOCK_DGRAM)
                my_socket.setsockopt(socket.SOL_SOCKET,
                                     socket.SO_REUSEADDR, 1)
                # Lo ato al servidor
                my_socket.connect((IP, int(Puert)))
                my_socket.send(bytes(lines, 'utf-8') + b'\r\n')
            elif met == 'BYE':
                user = lista[1].split(':')[1]
                # Cojo la IP y puerto del servidor del diccionario
                IP = self.clientes[user][0]
                Puert = int(self.ckientes[user][1])
                # Creo socket, y lo configuro
                my_socket = socket.socket(socket.AF_INET,
                                          socket.SOCK_DGRAM)
                my_socket.setsockopt(socket.SOL_SOCKET,
                                     socket.SO_REUSEADDR, 1)
                # Lo ato al servidor
                my_socket.connect((IP, int(Puert)))
                my_socket.send(bytes(lines, 'utf-8') + b'\r\n')
                bye = my_socket.recv(int(Puert))
                bye_send = bye.decode('utf-8')
                print('BYE recibido --', bye_send)
                self.wfile.write(bytes(bye_send, 'utf-8') + b'\r\n\r\n')
            elif met not in ['REGISTER', 'INVITE', 'BYE', 'ACK']:
                sys.exit('SIP/2.0 405 Method Not Allowed\r\n')
            else:
                self.wfile.write(b"SIP/2.0 400 Bad Request" + b"\r\n" +
                                 b"\r\n")
        

if __name__ == "__main__":
    # Argumentos y errores
    if len(sys.argv) != 2:
        sys.exit("Usage: python proxy_registrar.py config")
    try: 
        CONFIG = sys.argv[1]
    except(IndexError, ValueError):
        sys.exit("Usage: python proxy_registrar.py config")
    if not os.path.exists(CONFIG):
        sys.exit("Config_file doesn't exists")
    # Parseamos y separamos el fichero
    parser = make_parser()
    XMLHandler = FicheroXML()
    parser.setContentHandler(XMLHandler)

    try:
        parser.parse(open(CONFIG))
    except FileNotFoundError or IndexError:
            sys.exit("Usage: python3 proxy_registrar.py config")
    except FileNotFoundError:
            sys.exit('\r\nFile not found!')
    except KeyboardInterrupt:
            print("\r\nFinalizado el servidor")
            sys.exit()

    # XML a mi dicc
    list_XML = XMLHandler.get_tags()
    # Extracción de parámetros de XML
    PROX_NAME = list_XML[0][1]['name']  # Es el nombre del Proxy
    if list_XML[0][1]['ip'] is None:  # Si no se ha asignado IP al Proxy
       PROX_IP = '127.0.0.1'  # Por defecto ponemos esta IP
    else:  # Si tuviera IP asignada
       PROX_IP = list_XML[0][1]['ip']  # La extrae del XML
    PROX_PORT = int(list_XML[0][1]['puerto'])  # Es el puerto del PROXY
    LOG_PATH = list_XML[2][1]['path']  # Es el fichero log
    DAT_PATH = list_XML[1][1]['path']
    PASSW = str(list_XML[1][1]['passwdpath'])  # Es el fichero con contras
    # Creo para que el servidor escuche
    serv = socketserver.UDPServer((PROX_IP, PROX_PORT),
                                  SIPRegisterHandler)
    print("Server", PROX_NAME, "listening at port",  str(PROX_PORT),
          "..."+ "\r\n")
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print("\r\nFinalizado el servidor")
        sys.exit()
