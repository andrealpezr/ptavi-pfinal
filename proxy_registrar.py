#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Programa del proxy."""

import socket
import socketserver
import sys
import os
import time
from xml.sax import make_parser
from xml.sax.handler import ContentHandler


class FicheroXML(ContentHandler):
    """Creamos la clase del proxy."""

    def __init__(self):
        """Inicializa los diccionarios."""
        self.diccionario = {}
        self.dicc_ua1xml = {'server': ['name', 'ip', 'puerto'],
                            'database': ['path', 'passwdpath'],
                            'log': ['path']}

    def startElement(self, name, attrs):
        """Crea el diccionario con los valores del fichero xml."""
        if name in self.dicc_ua1xml:
            # Recorre los atributos y los guarda en Dict
            for atributo in self.dicc_ua1xml[name]:  # Busco etiquetas=name
                # Guarda sin sustituir lo que habia dentro
                self.diccionario[name+'_'+atributo] = attrs.get(atributo, '')

    def get_tags(self):
        """Devuelve el diccionario creado."""
        return self.diccionario


def writelog(eventofile):
    """Escribe en el fichero Log."""
    hora = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time())) + ' '
    filelog = open(LOG_PATH, 'a+')  # Abro fichero
    filelog.write(str(hora) + ' ' + eventofile + '\r\n')  # Escribo fichero


class SIPRegisterHandler(socketserver.DatagramRequestHandler):
    """Proxy class."""

    dicc_users = {}
    dicc_contr = {}

    def write_database(self):
        """Metodo que guarda usuarios en database."""
        fich = open('registro', "w")
        for user in self.dicc_users.keys():
            fich.write('USUARIOS QUE SE HAN REGISTRADO:' + '\r\n')
            line = (self.dicc_users[user][0] + ' ' +
                    self.dicc_users[user][1] + ' ' +
                    str(self.dicc_users[user][2]) + ' ')
            fich.write(line)

    def handle(self):
        """Segun los metodos que hacer."""
        while 1:
            # Leo linea a linea lo que recibo del cliente
            lines = self.rfile.read().decode('utf-8')
            # En caso de haber linea en blanco salgo del bucle
            if not lines:
                break
            print("El cliente nos manda..." + '\r\n' + lines)
            # Cojo la IP y puerto del cliente
            ipclient = str(self.client_address[0])
            portclie = str(self.client_address[1])
            # Escribo en el fichero Log el mensaje recibido del cliente
            recibo = 'Recibo de ' + ipclient + ':' + portclie + ':' + lines
            writelog(recibo)
            lista = lines.split(' ')
            # Segun el metodo que reciba, envio una cosa diferente
            met = lista[0]
            # En caso de recibir el metodo REGISTER
            if met == "REGISTER":
                nam = lines.split(' ')[1].split(':')[1]
                ipclient = str(self.client_address[0])
                puert = lines.split(' ')[1].split(':')[2]
                exp = lines.split(' ')[3]
                if len(lista) < 6:
                    nonce = '879879897897978979989979\r\n'
                    answer = 'SIP/2.0 401 Unauthorized' + '\r\n'
                    answer += ('WWW Authenticate: ' + 'Digest nonce = ' +
                               str(nonce) + '\r\n\r\n')
                    self.wfile.write(bytes(answer, 'utf-8'))
                    print('Enviando al cliente...' + '\r\n' + answer)
                elif len(lista) >= 5:
                    # Direccion del usuario
                    to_send = "SIP/2.0 200 OK" + "\r\n\r\n"
                    self.wfile.write(bytes(to_send, 'utf-8'))
                    self.dicc_users[nam] = [nam, ipclient, puert, exp]
            # En caso de recibir un INVITE
            elif met == "INVITE":
                # Nombre a quien envio el INVITE
                nam = lines.split(' ')[1].split(':')[1]
                if nam in self.dicc_users:
                    # Cojo la IP y puerto d el servidor del diccionario
                    ipclien = self.dicc_users[nam][1]
                    puert = int(self.dicc_users[nam][2])
                    try:
                        # Creo socket, y lo configuro
                        my_socket = socket.socket(socket.AF_INET,
                                                  socket.SOCK_DGRAM)
                        my_socket.setsockopt(socket.SOL_SOCKET,
                                             socket.SO_REUSEADDR, 1)
                        # Lo ato al servidor
                        my_socket.connect((ipclien, int(puert)))
                        print('Reenvio el INVITE al Server...' + '\r\n' +
                              lines)
                        my_socket.send(bytes(lines, 'utf-8') + b'\r\n\r\n')
                        data = my_socket.recv(int(puert))
                        dat = data.decode('utf-8')
                        print('Recibo del servidor...' + '\r\n' + dat)
                        self.wfile.write(bytes((dat), 'utf-8') + b'\r\n\r\n')
                        print('Reenvio al cliente...' + '\r\n' + dat)
                        self.wfile.write(bytes(dat, 'utf-8'))
                    except ConnectionRefusedError:
                        envio = ('Error: no server listening at' + ipclien)
                        self.wfile.write(bytes(envio, 'utf-8') + b'\r\n\r\n')
                else:
                    mensaj = "SIP/2.0 404 User not found"
                    self.wfile.write(bytes(mensaj, 'utf-8') + b'\r\n\r\n')
                    # Escribo en el LOG que el usuario no lo encuentra
                    not_found = ('Envio a ' + ipclient + ':' + portclie + ':' +
                                 "SIP/2.0 404 User not found")
                    writelog(not_found)
            elif met == 'ACK':
                # Nombre a quien envio el ACK
                nam = lines.split(' ')[1].split(':')[1]
                if nam in self.dicc_users:
                    # Cojo la IP y puerto del diccionario
                    ipclien = self.dicc_users[nam][1]
                    puert = int(self.dicc_users[nam][2])
                    try:
                        # Creo socket, y lo configuro
                        my_socket = socket.socket(socket.AF_INET,
                                                  socket.SOCK_DGRAM)
                        my_socket.setsockopt(socket.SOL_SOCKET,
                                             socket.SO_REUSEADDR, 1)
                        # Lo ato al servidor
                        my_socket.connect((ipclien, int(puert)))
                        print('Reenvio al Servidor...' + '\r\n' + lines)
                        my_socket.send(bytes(lines, 'utf-8') + b'\r\n\r\n')
                        dats = my_socket.recv(self.client_address[1])
                        dat = dats.decode('utf-8')
                        print('Recibo del servidor...' + '\r\n', dat)
                        self.wfile.write(bytes((dat), 'utf-8') + b'\r\n')
                    except ConnectionRefusedError:
                        envio = ('Error: no server listening at' + ipclien)
                        self.wfile.write(bytes(envio, 'utf-8') + b'\r\n\r\n')
                else:
                    self.wfile.write(bytes("SIP/2.0 404 User not found",
                                           'utf-8') + b'\r\n\r\n')
                    # Escribo en el LOG que el usuario no lo encuentra
                    not_found = ('Envio a ' + ipclient + ':' + portclie + ':' +
                                 'SIP/2.0 404 User not found')
                    writelog(not_found)
            elif met == 'BYE':
                nam = lines.split(' ')[1].split(':')[1]
                if nam in self.dicc_users:
                    # Cojo la IP y puerto d el servidor del diccionario
                    ipclien = self.dicc_users[nam][1]
                    puert = int(self.dicc_users[nam][2])
                    try:
                        # Creo socket, y lo configuro
                        my_socket = socket.socket(socket.AF_INET,
                                                  socket.SOCK_DGRAM)
                        my_socket.setsockopt(socket.SOL_SOCKET,
                                             socket.SO_REUSEADDR, 1)
                        # Lo ato al servidor
                        my_socket.connect((ipclien, int(puert)))
                        my_socket.send(bytes(lines, 'utf-8') + b'\r\n\r\n')
                        data = my_socket.recv(puert)
                        dat = data.decode('utf-8')
                        print('Recibo del servidor...' + '\r\n', dat)
                        self.wfile.write(bytes((dat), 'utf-8') + b'\r\n\r\n')
                    except ConnectionRefusedError:
                        envio = ('Error: no server listening at' + ipclien)
                        self.wfile.write(bytes(envio, 'utf-8') + b'\r\n\r\n')
                        # Escribo en el LOG que no hay servidor escuchando
                        envia = ('Envio a ' + ipclient + ':' + portclie + ':' +
                                 'Error: no server listening')
                        writelog(envia)
                else:
                    self.wfile.write(bytes("SIP/2.0 404 User not found",
                                           'utf-8') + b'\r\n\r\n')
                    # Escribo en el LOG que el usuario no lo encuentra
                    envia = ('Envio a ' + ipclient + ':' + portclie + ':' +
                             'SIP/2.0 404 User not found')
                    writelog(envia)
            elif met not in ['REGISTER', 'INVITE', 'BYE', 'ACK']:
                sys.exit('SIP/2.0 405 Method Not Allowed\r\n\r\n')
                # Escribo en el LOG el metodo no encontrado
                mens = ('Envio a ' + ipclient + ':' + portclie + ':' +
                        'SIP/2.0 405 Method Not Allowed')
                writelog(mens)
            else:
                self.wfile.write(b"SIP/2.0 400 Bad Request" + b"\r\n\r\n")
                # Escribo en el LOG la respuesta mal hecha
                malmens = ('Envio a ' + ipclient + ':' + portclie + ':' +
                           'SIP/2.0 400 Bad Request')
                writelog(malmens)
            self.write_database()


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
    PARSER = make_parser()
    XMLHANDLER = FicheroXML()
    PARSER.setContentHandler(XMLHANDLER)

    try:
        PARSER.parse(open(CONFIG))
    except IndexError:
        sys.exit("Usage: python3 proxy_registrar.py config")
    except KeyboardInterrupt:
        print("\r\nFinalizado el servidor")
        sys.exit()

    # XML a mi dicc
    LIST_XML = XMLHANDLER.get_tags()
    # Extracción de parámetros de XML
    PROX_NAME = LIST_XML['server_name']  # Es el nombre del Proxy
    if LIST_XML['server_ip'] is None:  # Si no se ha asignado IP al Proxy
        PROX_IP = '127.0.0.1'  # Por defecto ponemos esta IP
    else:  # Si tuviera IP asignada
        PROX_IP = LIST_XML['server_ip']  # La extrae del XML
    PROX_PORT = str(LIST_XML['server_puerto'])  # Es el puerto del PROXY
    LOG_PATH = LIST_XML['log_path']  # Es el fichero log
    DAT_PATH = LIST_XML['database_path']
    PASSW = str(LIST_XML['database_passwdpath'])  # Es el fichero con contras
    # Creo para que el servidor escuche
    SERVIDOR = socketserver.UDPServer((PROX_IP, int(PROX_PORT)),
                                      SIPRegisterHandler)
    print("Server " + PROX_NAME + "listening at port " + str(PROX_PORT) +
          "..." + "\r\n")
    try:
        SERVIDOR.serve_forever()
    except KeyboardInterrupt:
        print("\r\nFinalizado el servidor")
        sys.exit()
