#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Programa del proxy."""

import socket
import socketserver
import sys
import os
import json
import time


from xml.sax import make_parser
from xml.sax.handler import ContentHandler


class FicheroXML(ContentHandler):
    """Creamos la clase."""

    def __init__(self):
        """Inicalizo variables."""
        self.config = []

    def startElement(self, name, attrs):
        """Se abre si tengo la etiqueta."""
        if name == 'server':
            USER = attrs.get('name', "")
            self.config.append(USER)
            IP = attrs.get('ip', "")
            self.config.append(IP)
            PORT = attrs.get('puerto', "")
            self.config.append(PORT)

        elif name == 'database':
            DAT_PATH = attrs.get('path', "")
            self.config.append(DAT_PATH)
            CONTR = attrs.get('passwdpath', "")
            self.config.append(CONTR)

        elif name == 'log':
            LOG_PATH = attrs.get('path', "")
            self.config.append(LOG_PATH)

    def get_tags(self):
        """Imprime la lista."""
        return self.config


class SIPRegisterHandler(socketserver.DatagramRequestHandler):
    """Poxy class."""

    Dicc = {}
    Dicc_password = {}

    def ServidorRegistro(self):
        fich_serv = open('passwords.txt', 'w')
        for user in self.Dicc.keys():
            us = self.Dicc[user][0]
            ip = self.Dicc[user][1]
            port = self.Dicc[user][2]
            register = self.Dicc[user][3]
            exp = self.Dicc[user][4]
            fich_serv.write("USUARIOS QUE ESTAN REGISTRADOS" + '\r\n')
            fich_serv.write(us + ' ' + ip + ' ' + port + ' '
                            + str(register) + ' ' + str(exp) + ';')

    def delete(self):
        """Borra usuarios si expira el tiempo."""
        conjunto = []
        for contr in self.Dicc:
            time_now = self.Dic[contr][-1]
            time_strp = time.strptime(time_now, '%Y-%m-%d %H:%M:%S')
            if time_strp <= time.gmtime(time.time()):
                conjunto.append(contr)
        for usuario in conjunto:
            del self.Dicc[usuario]
            print('Borrando', usuario)

    def handle(self):
        """Segun los metodos que hacer."""
        while 1:
            # Leo linea a linea lo que recibo del cliente
            line = self.rfile.read()
            lines = line.decode('utf-8')
            # En caso de haber linea en blanco salgo del bucle
            if not lines:
                break
            print("El cliente nos manda:\r\n" + lines)
            # Segun el metodo que reciba, envio una cosa diferente
            lista = lines.split('\r\n')
            metod = lista[0].split()
            met = metod[0]
            # En caso de recibir el metodo REGISTER
            if met == "REGISTER":
               nonce = "89898989897898989898989"
               if len(lines.split()) == 5:
                       Answer = 'SIP/2.0 401 Unauthorized' + '\r\n'
                       Answer += ('WWW Authenticate: ' + 'Digest nonce = ' +
                                  str(nonce) + '\r\n')
                       self.wfile.write(bytes(Answer, 'utf-8'))
               elif len(lines.split()) > 5:
                   Answer = "SIP/2.0 200 OK\r\n"
                   self.wfile.write(bytes(Answer, 'utf-8'))
            # En caso de recibir un INVITE
            elif met == "INVITE":
                # Nombre a quien envio el INVITE
                user = lines.split(' ')[1].split(':')[1]
                if user in self.Dicc:
                    # Cojo la IP y puerto del servidor del diccionario
                    IP = self.Dicc[user][1]
                    Puert = int(self.Dicc[user][2])
                    # Creo socket, y lo configuro
                    my_socket = socket.socket(socket.AF_INET,
                                              socket.SOCK_DGRAM)
                    my_socket.setsockopt(socket.SOL_SOCKET,
                                         socket.SO_REUSEADDR, 1)
                   # Lo ato al servidor
                    my_socket.connect((IP, int(Puert)))
                    print('Reenvio INVITE al servidor\r\n' + lines)
                    my_socket.send(bytes(lines, 'utf-8') + b'\r\n')
                    data = my_socket.recv(Puert)
                    dat = data.decode('utf-8')
                    print('Recibo del servidor...', dat)
                    self.wfile.write(bytes(dat, 'utf-8') + b'\r\n')
                    print('Reenvio al cliente...\r\n', dat)
                    self.wfile.write(bytes(dat, 'utf-8') + b'\r\n')
            elif met == 'ACK':
                user = lines.split(' ')[1].split(':')[1]
                if user in self.Dicc:
                    # Cojo la IP y puerto del servidor del diccionario
                    IP = self.Dicc[user][1]
                    Puert = int(self.Dicc[user][2])
                    # Creo socket, y lo configuro
                    my_socket = socket.socket(socket.AF_INET,
                                              socket.SOCK_DGRAM)
                    my_socket.setsockopt(socket.SOL_SOCKET,
                                         socket.SO_REUSEADDR, 1)
                   # Lo ato al servidor
                    my_socket.connect((IP, int(Puert)))
                    my_socket.send(bytes(lines, 'utf-8') + b'\r\n')
                    inv = my_socket.recv(self.client_address[1])
                    inv_dat = inv.decode('utf-8')
                    print('ACK recibido y reenviado a ' + user + '\r\n')
                    self.wfile.write(bytes(inv_dat, 'utf-8') + b'\r\n')
            elif met == 'BYE':
                user = lines.split(' ')[1].split(':')[1]
                if user in self.Dicc:
                    # Cojo la IP y puerto del servidor del diccionario
                    IP = self.Dicc[user][1]
                    Puert = int(self.Dicc[user][2])
                    # Creo socket, y lo configuro
                    my_socket = socket.socket(socket.AF_INET,
                                              socket.SOCK_DGRAM)
                    my_socket.setsockopt(socket.SOL_SOCKET,
                                         socket.SO_REUSEADDR, 1)
                   # Lo ato al servidor
                    my_socket.connect((IP, int(Puert)))
                    my_socket.send(bytes(lines, 'utf-8') + b'\r\n')
                    bye = my_socket.recv(Puert)
                    bye_send = bye.decode('utf-8')
                    print('BYE recibido --', bye_send)
                    self.wfile.write(bytes(bye_send, 'utf-8') + b'\r\n')
            elif met not in ['INVITE', 'BYE', 'ACK']:
                self.wfile.write(b"SIP/2.0 405 Method Not Allowed" +
                                 b"\r\n")

if __name__ == "__main__":
    datos = sys.argv
    if len(datos) == 2:
        CONFIG = datos[1]
    else:
        sys.exit("Usage: python proxy_registrar.py config")
    # Parseamos y separamos el fichero
    parser = make_parser()
    XMLHandler = FicheroXML()
    parser.setContentHandler(XMLHandler)

    try:
        parser.parse(open(CONFIG))
    except FileNotFoundError or IndexError:
            sys.exit("  Usage: python3 proxy_registrar.py config")
    except FileNotFoundError:
            sys.exit('  File not found!')
    except KeyboardInterrupt:
            print("\r\nFinalizado el servidor")
            sys.exit()
    # XML a mi dicc
    list_XML = XMLHandler.get_tags()
    # extracción de parámetros de XML
    prox_port = int(list_XML[2])

    serv = socketserver.UDPServer(('', int(list_XML[2])),
                                  SIPRegisterHandler)
    print("Server", list_XML[0], "listening at port",  list_XML[2] ,
          "..."+ "\r\n")
    serv.serve_forever()
