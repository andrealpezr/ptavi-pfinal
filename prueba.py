#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Creamos uaclient para comunicarlo con proxy."""

import socket
import sys
import os
import hashlib
from xml.sax import make_parser
from xml.sax.handler import ContentHandler


class XMLClient(ContentHandler):
    """Clase que extrae e imprime el xml del cliente."""

    def __init__(self):
        """Inicializo las variabes."""
        self.Lista_client = []
        self.dicc_etiq = {'account': ['username', 'passwd'],
                          'uaserver': ['ip', 'puerto'],
                          'rtpaudio': ['puerto'],
                          'regproxy': ['ip', 'puerto'],
                          'log': ['path'],
                          'audio': ['path']}

    def startElement(self, element, attrs):
        """Crea las etiquetas y tributos del xml. Busca nombres, no guarda."""
        if element in self.dicc_etiq:
            Dict = {}
            # Recorre los atributos y los guarda en Dict
            for atrib in self.dicc_etiq[element]:  # Busco en etiquetas=element
                Dict[atrib] = attrs.get(atrib, "")
            # Guarda sin sustituir lo que habia dentro
            self.Lista_client.append([element, Dict])

    def get_tags(self):
        """Devuelve los datos del xml del cliente."""
        return self.Lista_client


if __name__ == "__main__":
    # Argumentos y errores
    if len(sys.argv) == 4:
        try:
            CONFIG = sys.argv[1]  # Fichero XML
            METHOD = sys.argv[2]  # Metodo SIP (es la cadena de Metodos)
            OPTION = sys.argv[3]  # Metodo opcional
        except(IndexError, ValueError, PermissionError):
            sys.exit('Usage: python3 uaclient.py config metho opcion')

        # En caso de introducir mal el metodo
        METODOS = ['REGISTER', 'INVITE', 'BYE']
        if METHOD not in METODOS:
            sys.exit('SIP/2.0 405 Method Not Allowed\r\n')

        # Creo el socket para parsear el XML y trabajar con el
        parser = make_parser()
        Handler = XMLClient()
        parser.setContentHandler(Handler)
        parser.parse(open(CONFIG))
        datos_XML = Handler.get_tags()  # Dicc con atributos

        # Extraigo el fichero XML de los uaxml
        USERNAME = datos_XML[0][1]['username']  # Es el nombre SIP
        USER_PASS = datos_XML[0][1]['passwd']  # Es la contraseña SIP
        UASERV_IP = datos_XML[1][1]['ip']  # Es el ip del servidor
        UASERV_PORT = datos_XML[1][1]['puerto']  # Es el servidor del servidor
        RTP_PORT = datos_XML[2][1]['puerto']  # Es el puerto del RTP
        log_path = datos_XML[4][1]['path']  # Es el fichero log
        AUDIO_PATH = datos_XML[5][1]['path']  # Es el audio log
        PROX_PORT = datos_XML[3][1]['puerto']  # Es el puerto del PROXY
        if datos_XML[3][1]['ip'] is None:   # Si no se ha asignado IP del Proxy
            PROXY_IP = "127.0.0.1"  # Por defecto ponemos la IP 127.0.0.1
        else:  # En el caso de tener IP
            PROXY_IP = datos_XML[3][1]['ip']  # La extraemos del XML
        # Creo y configuro socket
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
            # Conecto al proxy
            my_socket.connect((PROXY_IP, int(PROX_PORT)))
            # Dependiendo del metodo envia diferentes mensajes
            if METHOD == "REGISTER":
                SEND = METHOD + ' sip:' + USERNAME + ':' + UASERV_PORT
                SEND += ' SIP/2.0\r\n' + 'Expires: ' + OPTION
                # Envio la peticion al Proxy
                print("Enviando al Proxy..." + '\n' + SEND)
                my_socket.send(bytes(SEND, 'utf-8') + b'\r\n')  # a bytes
                # Recibo la respuesta del Proxy
                DATA = my_socket.recv(1024).decode('utf-8')
                print('Recibo del Proxy...', DATA)
                RECV = DATA.split()
                # Voy a mandar la Authorization Digest response al Proxy
                if RECV[1] == '401':
                    SEND = METHOD + ' sip:' + USERNAME + ':' + UASERV_PORT
                    SEND += ' SIP/2.0\r\n' + 'Expires: ' + OPTION + 'r\n'
                    nonce = '1231231231212312123123123\r\n'
                    autho = 'Authorization: Digest response = '
                    autho += nonce
                    ALL = SEND + autho
                    # Lo envio al proxy
                    print("Enviando al proxy..." + "\n" + ALL)
                    my_socket.send(bytes(ALL, 'utf-8') + b'\r\n')
                    # Recibo respuesta
                    DATA = my_socket.recv(1024).decode('utf-8')
                    print('Recibido del proxy...', DATA)
            # En caso de recibir un INVITE
            if METHOD == "INVITE":
                SEND = METHOD + ' sip:' + USERNAME + ' SIP/2.0\r\n'
                SEND += 'Content-Type: application/sdp\r\n\r\n' + 'v=0\r\n'
                SEND += 'o=' + USERNAME + ' ' + UASERV_IP + '\r\n'
                SEND += 's=lasesion \r\n' + 't=0\r\n' + 'm=audio '
                SEND += RTP_PORT + ' RTP\r\n'
                my_socket.send(bytes(SEND, 'utf-8') + b'\r\n')  # paso a bytes
                print("Enviando al Proxy..." + "r\n" + SEND)
                # Recibo respuesta del Proxy
                DATA = my_socket.recv(1024).decode('utf-8')
                recv = DATA.split()
                # Analizo si recibo el 404 o el 200 OK del Proxy
                if recv[1] == '404':
                    print('Recibido del servidor:', DATA)
                elif recv[7] == "200":
                    print('Recibido del servidor:', DATA)
                    # Vamos a enviar el ACK
                    SEND = 'ACK sip:' + OPTION + ' SIP/2.0 \r\n'
                    my_socket.send(bytes(SEND, 'utf-8') + b'\r\n')
                    print('Enviando al Proxy...' + 'r\n' + SEND)
                    # Envio mp3
                    print('He enviado el ACK, mando RTP')
                    aEjecutar = './mp32rtp -i ' + UASERV_IP + ' -p '
                    aEjecutar += RTP_PORT + ' < ' + AUDIO_PATH
                    print('Vamos a ejecutar = ', aEjecutar)
                    os.system(aEjecutar)
                    print('La transmision RTP ha finalizado')
            # En caso de recibir un ACK
            elif METHOD == "BYE":
                SEND = METHOD + " sip:" + USERNAME + " SIP/2.0\r\n"
                # Enviamos el BYE
                my_socket.send(bytes(SEND, 'utf-8') + b'\r\n')
                print('Enviando al Proxy...' + 'r\n' + SEND)
                # Recibo respusta del Proxy
                DAT = my_socket.recv(1024).decode('utf-8')
                recv = DAT.split()
                if recv[1] == '200':
                    print('Enviando al Proxy...', DAT)
                    print('Terminando socket...')
                    my_socket.close()
    else:
        sys.exit('Usage: python3 uaclient.py config method opcion')
    print('Terminando socket...')
    my_socket.close()
