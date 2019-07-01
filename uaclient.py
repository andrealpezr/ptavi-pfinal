#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Creamos uaclient para comunicarlo con proxy."""

import socket
import sys
import os
import time
from xml.sax import make_parser
from xml.sax.handler import ContentHandler


class XMLClient(ContentHandler):
    """Clase que extrae e imprime el xml del cliente."""

    def __init__(self):
        """Inicializa los diccionarios."""
        self.diccionario = {}
        self.dicc_ua1xml = {'account': ['username', 'passwd'],
                            'uaserver': ['ip', 'puerto'],
                            'rtpaudio': ['puerto'],
                            'regproxy': ['ip', 'puerto'],
                            'log': ['path'], 'audio': ['path']}

    def startElement(self, name, attrs):
        """Crea el diccionario con los valores del fichero xml."""
        if name in self.dicc_ua1xml:
            for atributo in self.dicc_ua1xml[name]:
                self.diccionario[name+'_'+atributo] = attrs.get(atributo, '')

    def get_tags(self):
        """Devuelve el diccionario creado."""
        return self.diccionario


def writelog(eventofile):
    """Escribe en el fichero Log."""
    hora = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time())) + ' '
    filelog = open(LOG_PATH, 'a+')  # Abro fichero
    filelog.write(str(hora) + ' ' + eventofile + '\r\n')  # Escribo fichero


if __name__ == "__main__":
    # Argumentos y errores
    if len(sys.argv) == 4:
        try:
            CONFIG = sys.argv[1]  # Fichero XML
            METHOD = sys.argv[2]  # Metodo SIP (es la cadena de Metodos)
            OPTION = sys.argv[3]  # Metodo opcional
        except(IndexError, ValueError):
            sys.exit('Usage: python3 uaclient.py config method opcion')

        # En caso de introducir mal el metodo
        METODOS = ['REGISTER', 'INVITE', 'BYE']
        if METHOD not in METODOS:
            sys.exit('SIP/2.0 405 Method Not Allowed\r\n')

        # Creo el socket para parsear el XML y trabajar con el
        PARSER = make_parser()
        HANDLER = XMLClient()
        PARSER.setContentHandler(HANDLER)
        PARSER.parse(open(CONFIG))
        DATOS_XML = HANDLER.get_tags()  # Dicc con atributos

        # Extraigo el fichero XML de los uaxml
        USERNAME = DATOS_XML['account_username']  # Es el nombre SIP
        USER_PASS = DATOS_XML['account_passwd']
        RTP_PORT = str(DATOS_XML['rtpaudio_puerto'])  # Es el puerto del RTP
        PROX_PORT = str(DATOS_XML['regproxy_puerto'])  # Es el puerto del PROXY
        LOG_PATH = DATOS_XML['log_path']  # Es el fichero log
        AUDIO_PATH = DATOS_XML['audio_path']  # Es el audio log
        UASERV_PORT = str(DATOS_XML['uaserver_puerto'])  # Es el port del serv
        if DATOS_XML['uaserver_ip'] == '':  # En caso de no tener IP el servido
            UASERV_IP = '127.0.0.1'  # Por defecto es 127.0.0.1
        else:
            UASERV_IP = DATOS_XML['uaserver_ip']  # Si no esta vacia, es xml
        if DATOS_XML['regproxy_ip'] == '':  # En caso de no tener IP el Proxy
            PROXY_IP = '127.0.0.1'  # Por defecto es 127.0.0.1
        else:
            PROXY_IP = DATOS_XML['regproxy_ip']  # Si no esta vacia, es ip xml

        # Creo y configuro socket
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
            # Conecto al proxy
            my_socket.connect((PROXY_IP, int(PROX_PORT)))
            # Dependiendo del metodo envia diferentes mensajes
            if METHOD == "REGISTER":
                SEND = METHOD + ' sip:' + USERNAME + ':' + UASERV_PORT
                SEND += ' SIP/2.0\r\n' + 'Expires: ' + OPTION + '\r\n\r\n'
                # Envio la peticion al Proxy
                my_socket.send(bytes(SEND, 'utf-8'))  # a bytes
                print("Enviando al Proxy..." + '\r\n' + SEND)
                #  Escribo en el fichero el mensaje a enviar
                MENS = 'Enviando a ' + PROXY_IP + ':' + PROX_PORT + ': ' + SEND
                writelog(MENS)
                # Recibo la respuesta del Proxy
                DATA = my_socket.recv(1024).decode('utf-8')
                print('Recibo del Proxy...' + '\r\n' + DATA)
                RECV = DATA.split()
                # Escribo en el fichero el mensaje recibido
                MENS = 'Recibo de ' + PROXY_IP + ':' + PROX_PORT + ': ' + SEND
                writelog(MENS)
                if RECV[1] == '401':
                    SEND = METHOD + ' sip:' + USERNAME + ':' + UASERV_PORT
                    SEND += ' SIP/2.0\r\n' + 'Expires: ' + OPTION + "\r\n"
                    NONCE = '1231231231212312123123123\r\n'
                    AUTHORIZO = 'Authorization: Digest response = '
                    AUTHORIZO += NONCE + '\r\n\r\n'
                    ALL = SEND + AUTHORIZO
                    # Lo envio al proxy
                    print("Enviando al proxy..." + "\r\n" + ALL)
                    my_socket.send(bytes(ALL, 'utf-8'))
                    #  Escribo en el fichero el mensaje a enviar
                    MENS = ('Envio a ' + PROXY_IP + ':' + PROX_PORT + ': ' +
                            SEND)
                    writelog(MENS)
                    # Recibo respuesta
                    DATA = my_socket.recv(1024).decode('utf-8')
                    print('Recibido del proxy...' + "\r\n" + DATA)
                    # Escribo en el fichero el mensaje recibido
                    MENS = ('Recibo de ' + PROXY_IP + ':' + PROX_PORT + ': ' +
                            SEND)
                    writelog(MENS)
            # En caso de recibir un INVITE
            if METHOD == "INVITE":
                SEND = METHOD + ' sip:' + OPTION + ' SIP/2.0\r\n'
                SEND += 'Content-Type: application/sdp\r\n\r\n' + 'v=0\r\n'
                SEND += 'o=' + USERNAME + ' ' + UASERV_IP + '\r\n'
                SEND += 's=lasesion\r\n' + 't=0\r\n' + 'm=audio '
                SEND += str(RTP_PORT) + ' RTP\r\n\r\n'
                # Enviamos el mensaje al Proxy
                my_socket.send(bytes(SEND, 'utf-8'))  # paso a bytes
                print("Enviando al Proxy..." + "\r\n" + SEND)
                #  Escribo en el fichero el mensaje a enviar
                MENS = ('Enviando a ' + PROXY_IP + ':' + PROX_PORT + ': ' +
                        SEND)
                writelog(MENS)
                # Recibo respuesta del Proxy
                DATA = my_socket.recv(1024).decode('utf-8')
                RECV = DATA.split()
                # Escribo en el fichero el mensaje recibido
                MENS = ('Recibo de ' + PROXY_IP + ':' + PROX_PORT + ': ' +
                        SEND)
                writelog(MENS)
                # Analizo si recibo el 404 o el 200 OK del Proxy
                if RECV[1] == '404':
                    print('Recibido del servidor:' + "\r\n" + DATA)
                elif RECV[7] == "200":
                    print('Recibido del servidor:' + "\r\n" + DATA)
                    # Voy a enviar el ACK
                    SEND = 'ACK sip:' + OPTION + ' SIP/2.0\r\n\r\n'
                    # Envio al Proxy el ACk
                    my_socket.send(bytes(SEND, 'utf-8'))
                    print('Enviando al Proxy...' + '\r\n' + SEND)
                    # Escribo en el fichero el mensaje a enviar
                    MENS = ('Envio a ' + PROXY_IP + ':' + PROX_PORT + ': ' +
                            SEND)
                    writelog(MENS)
                    # Envio mp3
                    print('He enviado el ACK, mando RTP')
                    AEJECUTAR = './mp32rtp -i ' + UASERV_IP + ' -p '
                    AEJECUTAR += str(RTP_PORT) + ' < ' + AUDIO_PATH
                    print('Vamos a ejecutar = ' + AEJECUTAR)
                    os.system(AEJECUTAR)
                    print('La transmision RTP ha finalizado')
            # En caso de recibir un ACK
            elif METHOD == "BYE":
                SEND = METHOD + " sip:" + OPTION + " SIP/2.0\r\n\r\n"
                # Enviamos el BYE
                my_socket.send(bytes(SEND, 'utf-8'))
                print('Enviando al Proxy...' + '\r\n' + SEND)
                # Recibo respusta del Proxy
                DAT = my_socket.recv(1024).decode('utf-8')
                RECV = DAT.split()
                if RECV[1] == '200':
                    print('Enviando al Proxy...' + "\r\n" + DAT)
                # Escribo en el fichero el ACK recibido
                MENS = 'Recibo de ' + PROXY_IP + ':' + PROX_PORT + ': ' + SEND
                writelog(MENS)
    else:
        sys.exit('Usage: python3 uaclient.py config method opcion')
    print('Terminando socket...')
    my_socket.close()
