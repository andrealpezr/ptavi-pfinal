#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import time
from datetime import date, datetime
import os

config = sys.argv[1]
metodo = sys.argv[2]
opcion = sys.argv[3]

class uaCLIENT(ContentHandler):

    def __init__ (self):

        self.Lista = []
        self.Diccionario = {'account': ['username', 'passwd'],
                            'uaserver': ['ip', 'puerto'],
                            'rtpaudio': ['puerto'], 'regproxy':['ip', 'puerto'],
                            'log':['path'], 'audio':['path']}

    def startElement(self, etiqueta, atrib):
        if etiqueta in self.Diccionario:
            Dicc = {}
            for atributo in self.Diccionario[etiqueta]:
                Dicc[atributo] = atrib.get(atributo, "")
            self.Lista.append([etiqueta, Dicc])

    def get_tags(self):
        return self.Lista

if __name__ == "__main__":
    if len(sys.argv) == 4:
        parser = make_parser()
        MyHandler = uaCLIENT()
        parser.setContentHandler(MyHandler)
        parser.parse(open(config))
        Lista_xml = MyHandler.get_tags()
        account_us = Lista_xml[0][1]['username']
        account_passwd = Lista_xml[0][1]['passwd']
        uaserver_ip = Lista_xml[1][1]['ip']
        uaserver_puerto = Lista_xml[1][1]['puerto']
        rtpaudio_puerto = Lista_xml[2][1]['puerto']
        regproxy_ip = Lista_xml[3][1]['ip']
        regproxy_puerto = Lista_xml[3][1]['puerto']
        log_path = Lista_xml[4][1]['path']
        audio_path = Lista_xml[5][1]['path']

        my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_socket.connect((regproxy_ip, int(regproxy_puerto))) #Conecto conproxy

    #def log(evento, regproxy_ip, regproxy_puerto, linea):
        #fichero = open(fichero, 'a')
        #hora_actual = datetime.now()
        #hora = fich.write(hora_actual())

        #if evento == "enviar":
            #fichero.write(' Sent to ' + regproxy_ip + ":" + str(regproxy_puerto) + ": " + linea + '\r\n')
        #elif evento == "recibir":
            #fichero.write(' Received from ' + regproxy_ip + ":" + str(regproxy_puerto) + ": " + linea + '\r\n')
        #elif evento == "error":
            #fichero.write(' Error: ' + linea + '\r\n')
        #elif evento == "Comenzar":
            #fichero.write(' Starting... ')
        #elif evento == "Finalizar":
            #fichero.write(' Finishing. \r\n')

        #fichero.close()

        if metodo == "REGISTER":
            #linea = ""
            #log(log_path, "starting", uaserver_ip, uaserver_puerto, linea)
            #envío petición con el puerto y la ip de mi cliente
            peticion = metodo + " sip:" + account_us + ":" + uaserver_puerto + " "
            peticion += "SIP/2.0\r\n" + "Expires: " + opcion + "\r\n"
            print("Enviando:", peticion)
            my_socket.send(bytes(peticion, 'utf-8') + b'\r\n')
            data = my_socket.recv(1024)
            print('Recibido --', data.decode('utf-8'))

            list_rec = data.decode('utf-8').split()
            if list_rec[1] == "401":
                peticion = metodo + " sip:" + account_us + ":" + uaserver_puerto
                peticion += " " + "SIP/2.0\r\n" + "Expires: " + opcion + " \r\n"
                peticion += "Authorizacion: Digest response=123123212312321212123"
                peticion += "\r\n"
                print("Enviando:", peticion)
                my_socket.send(bytes(peticion, 'utf-8') + b'\r\n')
                datos = my_socket.recv(1024)
            print('Recibido --', datos.decode('utf-8'))

        elif metodo == "INVITE":
            peticion = metodo + " sip:" + opcion + ' ' + "SIP/2.0\r\n"
            peticion += "Content-Type: application/sdp\r\n\r\n" + "v=0\r\n" + "o="
            peticion += account_us + ' ' + uaserver_ip + "\r\n" + "s=misession\r\n"
            peticion +="t=0\r\n" + "m=audio " + rtpaudio_puerto + " RTP\r\n\r\n"
            print("Enviando:", peticion)
            my_socket.send(bytes(peticion, 'utf-8') + b'\r\n')
            data = my_socket.recv(1024)
            print('Recibido --', data.decode('utf-8'))
            list_rec = data.decode('utf-8').split()
            if list_rec[1] == "100" and list_rec[4] == "180" and list_rec[7] == "200":
                metodo = "ACK"
                peticion = metodo + " sip:" + account_us + " SIP/2.0\r\n"
                print("Enviando", peticion)
                my_socket.send(bytes(peticion, 'utf-8') + b'\r\n')
                aEjecutar = "./mp32rtp -i " + uaserver_ip + " -p 23032 < "
                aEjecutar += audio_path
                print("Vamos a ejecutar", aEjecutar)
                os.system(aEjecutar)

        elif metodo == "BYE":
            peticion = metodo + " sip:" + account_us + ' ' + " SIP/2.0\r\n"
            print("Enviando", peticion)
            my_socket.send(bytes(peticion, 'utf-8') + b'\r\n')
            data = my_socket.recv(1024)
            print('Recibido --', data.decode('utf-8'))
    else:
        sys.exit("Usage: python uaclient.py config method option")
print("Terminando socket...")


