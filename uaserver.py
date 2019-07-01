#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Programa para un Servidor de eco en UDP simple."""

import os
import sys
import time
import socketserver
from xml.sax import make_parser
from xml.sax.handler import ContentHandler


class XMLSERVER(ContentHandler):
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


class EchoHandler(socketserver.DatagramRequestHandler):
    """Metodo del servidor que establece conexion con el cliente y proxy."""

    USER = []
    PORT = []

    def handle(self):
        """Escribe direccion y puerto del cliente."""
        # Lee linea a linea lo que recibe del cliente
        recibo = self.rfile.read().decode('utf-8')
        lines = recibo.split()
        print('Recibo del Proxy...' + '\r\n' + recibo)
        # Cojo la IP y puerto del cliente
        ipcliente = str(self.client_address[0])
        portcliente = str(self.client_address[1])
        # Escribo en el fichero Log el mensaje recibido
        mens = 'Recibo de ' + ipcliente + ':' + portcliente + ':' + recibo
        writelog(mens)
        metodo = lines[0]
        if metodo == 'INVITE' or metodo == 'invite':
            self.USER.append(lines[7])
            self.PORT.append(lines[11])
            # Lo envio tras recibir el INVITE del Proxy
            enviando = 'SIP/2.0 100 Trying\r\n\r\n'
            enviando += 'SIP/2.0 180 Ringing\r\n\r\n'
            enviando += 'SIP/2.0 200 OK\r\n\r\n'
            sdp = 'Content-Type: application/sdp\r\n\r\n' + 'v=0 \r\n'
            sdp += "o=" + USERNAME + " " + UASERV_IP + '\r\n'
            sdp += 's=lasesion\r\n' + 't=0\r\n' + 'm=audio '
            sdp += str(RTP_PORT) + ' RTP\r\n\r\n'
            todo = enviando + sdp
            #  Envio al Proxy
            self.wfile.write(bytes(todo, 'utf-8'))
            print('Enviamos al Proxy...' + '\r\n' + todo)
            # Escribo en el LOG el mensaje a enviar
            enviar = 'Envio a ' + ipcliente + ':' + portcliente + ':' + todo
            writelog(enviar)
        elif metodo == 'ACK' or metodo == 'ACK':
            # Tras recibir el ack mando el rtp
            print('He recibido el ACK, envio RTP')
            aejecutar = './mp32rtp -i ' + UASERV_IP + " -p "
            aejecutar += str(RTP_PORT) + ' < ' + AUDIO_PATH
            print('Vamos a ejecutar ' + aejecutar)
            os.system(aejecutar)
            print('La ejecucion  RTP ha finalizado')
            # Escribo en el LOG el RTP
            ejec = 'Vamos a ejecutar RTP a ' + ipcliente + ':' + portcliente
            writelog(ejec)
            # En caso de recibir un BYE
        elif metodo == 'BYE' or metodo == 'bye':
            okmens = 'SIP/2.0 200 OK\r\n\r\n'
            self.wfile.write(bytes(okmens, 'utf-8'))
            print('Enviamos al Proxy...' + '\r\n' + okmens)
            # Escribo en el LOG el OK
            recibo = ('Recibo de ' + ipcliente + ':' + portcliente + ':' +
                      'SIP/2.0 200 OK')
            writelog(recibo)
        # En caso de introducir mal el metodo
        elif metodo not in ['REGISTER', 'INVITE', 'BYE']:
            mal_metodo = 'SIP/2.0 405 Method Not Allowed\r\n\r\n'
            self.wfile.write(bytes(mal_metodo))
            # Escribo en el LOG el mensaje de metodo mal formulado
            recibo = ('Recibo de ' + ipcliente + ':' + portcliente + ':' +
                      'SIP/2.0 200 OK')
            writelog(recibo)
        else:
            self.wfile.write(b'SIP/2.0 400 Bad Request\r\n\r\n')
            # Escribo en el LOG el error de pregunta
            request = ('Recibo de ' + ipcliente + ':' + portcliente + ':' +
                       'SIP/2.0 400 Bad Request')
            writelog(request)


if __name__ == "__main__":

    if len(sys.argv) == 2:
        try:
            CONFIG = sys.argv[1]
        except IndexError:
            sys.exit("Usage: python3 uaserver.py config")
        # Creo el socket para parsear el XML y trabajar con el
        PARSER = make_parser()
        U2HANDLER = XMLSERVER()
        PARSER.setContentHandler(U2HANDLER)
        try:
            PARSER.parse(open(CONFIG))
        except(IndexError, ValueError):
            sys.exit('Usage: python3 uaserver.py config')
        DATOS_XML = U2HANDLER.get_tags()

        # Extraigo el fichero XML
        USERNAME = DATOS_XML['account_username']  # Es el nombre SIP
        RTP_PORT = int(DATOS_XML['rtpaudio_puerto'])  # Es el puerto del RTP
        PROX_PORT = int(DATOS_XML['regproxy_puerto'])  # Es el puerto del PROXY
        LOG_PATH = DATOS_XML['log_path']  # Es el fichero log
        AUDIO_PATH = DATOS_XML['audio_path']  # Es el audio log
        UASERV_PORT = DATOS_XML['uaserver_puerto']  # Es el port del servidor
        if DATOS_XML['uaserver_ip'] == '':  # En caso de no tener IP el servido
            UASERV_IP = '127.0.0.1'  # Por defecto es 127.0.0.1
        else:
            UASERV_IP = DATOS_XML['uaserver_ip']  # Si no esta vacia, es xml

        if DATOS_XML['regproxy_ip'] == '':  # En caso de no tener IP el Proxy
            PROXY_IP = '127.0.0.1'  # Por defecto es 127.0.0.1
        else:
            PROXY_IP = DATOS_XML['regproxy_ip']  # Si no esta vacia, es ip xml

        SERVI = socketserver.UDPServer((UASERV_IP, int(UASERV_PORT)),
                                       EchoHandler)
        print('Listening...\r\n')
        try:
            SERVI.serve_forever()
        except IndexError:
            sys.exit("Usage: python3 uaserver.py config")
        except KeyboardInterrupt:
            print("\r\nFinalizado el servidor")
    else:
        sys.exit('Usage: python3 uaserver.py config')
