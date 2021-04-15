import json
import os
import socket
import subprocess
import sys
import threading
import time
from threading import Timer

import mininet.link
import mininet.log
import mininet.node
from flask import Flask, request
from flask_cors import CORS
from mininet.cli import CLI
from mininet.net import Mininet
from mininet.node import OVSSwitch, RemoteController
from mininet.topo import Topo

# Create a variable for the elements of topology
host_group = []
swithc_group = []
controller_group = []
link_group = []
port_group = []

host_container = []
switch_container = []
controller_container = []
link_container = []
link_array = []
link_dict = {}
port_container = []


linkeados = []

host_added = []
switch_added = []
controller_added = []
aux_array = []
aux = []

serversEnabled = False

name_files = []
name_files_server = []
#Variables para la generacion de trafico ITG

hots_receiver = None
host_sender = None

# Creacion de la red en Mininet
net = Mininet(build=False)


app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})



@app.route('/',methods=['GET'])
def get():
    return 'Este es el Sevidor Mininet'

@app.route('/',methods=['POST'])
def executor():
    global serversEnabled, aux_array, name_files, name_files_server, aux
    tstart = time.time()
    content = request.json
    contador = 0
    
    json_data = content

    answer_to_client = None 
    charge_array = {}
    traffic_array = {}
    dict_answer = {} #diccionario que se enviará como respuesta al Cliente
    
    # Leemos las opciones de operación 
    if 'action' in json_data:
        print('\nDatos: ',content)
        act = json_data['action']
        if act == "stop":
            print("Terminando Emulacion ...")
            for n in linkeados:
                print(n)
                net.link.delete(n)
            net.stop()
            os.system('echo %s|sudo -S %s' % ('Okm1234$','sudo mn -c'))
            os.system('echo %s|sudo -S %s' % ('Okm1234$', 'pkill -9 -f "sudo mnexec"'))


                


            ans = {}
            ans['emulacion'] = 'terminada'
            f = json.dumps(ans)
            serversEnabled = False
            print('Emulación Terminada')

        return ans
    elif 'TCP' in json_data:
        print('\nDatos: ',content)
        #Tipos de Distribucion del Tráfico
        if('global' in json_data):

            print('TCP Global ...')
            host_size= (len(host_added))-1
            port_list =[]
            initial_port = 5000

            #Datos del modo de transmision
            #Solo una de estas tres opciones
            time_e = str('0')
            number = '0k'
            block = '0k'

            interval = str(1)
            window = '500k'
            length = '1m'
            bw = '1k'
            


            dict_data_traffic = {}
            dict_data_traffic_server = {}

            file_traffic= []
            data_traffic={}
            procces_data={}
            data_gen= {}
            
            #Lista de Puertos
            for pt in range(host_size):
                initial_port = initial_port + 1
                port_list.append(str(initial_port))


            
            
            #Se colocan los host como servidor en el puerto indicado
            if(serversEnabled == True):
                print('Reiniciando el Servicio iperf3...')
                os.system('echo %s|sudo -S %s' % ('Okm1234$', 'pkill -9 iperf3'))
               # for serv in aux:
                #    serv[0].cmd('sudo kill 9 $(sudo lsoft -t -i:'+serv[1]+')')

            print('Estableciendo Servidores...')
            for host_server in host_added:
                for port in port_list:
                    host_server.cmd('iperf3 -s -p '+str(port)+' -J>'+str(host_server)+'_'+str(port)+'.json'+' &')
                    time.sleep(1)
                    name_files_server.append(str(host_server)+'_'+str(port))
                    aux = [host_server, port]
                    aux_array.append(aux)
            serversEnabled = True

            buffer_server = []
            for server in aux_array:
                for host_client in host_added:
                    if not (str(host_client)+'_'+str(server[0])) in buffer_server:
                        if not str(server) in buffer_server:
                            if str(server[0]) == str(host_client):
                                pass
                            else:
                                #Posibles casos de parametrizacion del Trafico en Iperf3.1
                                #Solo el parámetro de Tiempo 
                                if('t' in json_data and (not 'i' in json_data) and (not 'l' in json_data) and (not 'b' in json_data) and (not 'w' in json_data)):
                                    contador +=1
                                    time_e = str(json_data['t'])
                                    print('Secuencia ', contador, ' del Generador...')
                                    host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                    temp = str(host_client)+'_'+str(server[0])
                                    ax = str(server)
                                    buffer_server.append(temp)
                                    buffer_server.append(ax)
                                    name_files.append(str(host_client)+'_'+str(server[0]))
                                #Solo el parámetro de Tiempo con Intervalo 
                                elif('t' in json_data and ('i' in json_data) and (not 'l' in json_data) and (not 'b' in json_data) and (not 'w' in json_data)):
                                    time_e = str(json_data['t'])
                                    interval = str(json_data['i'])
                                    host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -i '+interval+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                    temp = str(host_client)+'_'+str(server[0])
                                    ax = str(server)
                                    buffer_server.append(temp)
                                    buffer_server.append(ax)
                                    name_files.append(str(host_client)+'_'+str(server[0]))
                                #Solo el parametro de Tiempo con Longitud 
                                elif('t' in json_data and (not 'i' in json_data) and ('l' in json_data) and (not 'b' in json_data) and (not 'w' in json_data)):
                                    time_e = str(json_data['t'])
                                    length = str(json_data['i'])
                                    host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -l '+length+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                    temp = str(host_client)+'_'+str(server[0])
                                    ax = str(server)
                                    buffer_server.append(temp)
                                    buffer_server.append(ax)
                                    name_files.append(str(host_client)+'_'+str(server[0]))
                                #Solo el parametro de Tiempo con Ancho de Banda
                                elif('t' in json_data and (not 'i' in json_data) and (not 'l' in json_data) and ('b' in json_data) and (not 'w' in json_data)):
                                    time_e = str(json_data['t'])
                                    bw = str(json_data['b'])
                                    host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -b '+bw+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                    temp = str(host_client)+'_'+str(server[0])
                                    ax = str(server)
                                    buffer_server.append(temp)
                                    buffer_server.append(ax)
                                    name_files.append(str(host_client)+'_'+str(server[0]))
                                    pass
                                #Solo el parametro de Tiempo con Ventana
                                elif('t' in json_data and (not 'i' in json_data) and (not 'l' in json_data) and (not 'b' in json_data) and ('w' in json_data)):
                                    time_e = str(json_data['t'])
                                    window = str(json_data['w'])
                                    host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                    temp = str(host_client)+'_'+str(server[0])
                                    ax = str(server)
                                    buffer_server.append(temp)
                                    buffer_server.append(ax)
                                    name_files.append(str(host_client)+'_'+str(server[0]))
                                #Solo el parametro de Tiempo con Intervalo y Longitud
                                elif('t' in json_data and ('i' in json_data) and ( 'l' in json_data) and (not 'b' in json_data) and (not 'w' in json_data)):
                                    time_e = str(json_data['t'])
                                    interval = str(json_data['i'])
                                    length =  str(json_data['l'])
                                    host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -i '+interval+' -l '+length+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                    temp = str(host_client)+'_'+str(server[0])
                                    ax = str(server)
                                    buffer_server.append(temp)
                                    buffer_server.append(ax)
                                    name_files.append(str(host_client)+'_'+str(server[0]))
                                #Solo el parametro de Tiempo con Intervalo y Ancho de Banda
                                elif('t' in json_data and ('i' in json_data) and ( not 'l' in json_data) and ('b' in json_data) and (not 'w' in json_data)):
                                    time_e = str(json_data['t'])
                                    interval = str(json_data['i'])
                                    bw =  str(json_data['b'])
                                    host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -i '+interval+' -b '+bw+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                    temp = str(host_client)+'_'+str(server[0])
                                    ax = str(server)
                                    buffer_server.append(temp)
                                    buffer_server.append(ax)
                                    name_files.append(str(host_client)+'_'+str(server[0]))
                                #Solo el parametro de Tiempo con Longitud y Ventana
                                elif('t' in json_data and (not 'i' in json_data) and ('l' in json_data) and (not 'b' in json_data) and ('w' in json_data)):
                                    time_e = str(json_data['t'])
                                    length = str(json_data['l'])
                                    window =  str(json_data['w'])
                                    host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -l '+length+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                    temp = str(host_client)+'_'+str(server[0])
                                    ax = str(server)
                                    buffer_server.append(temp)
                                    buffer_server.append(ax)
                                    name_files.append(str(host_client)+'_'+str(server[0]))
                                #Solo el parametro de Tiempo con  Ancho de Banda y Ventana
                                elif('t' in json_data and (not 'i' in json_data) and (not 'l' in json_data) and ('b' in json_data) and (not 'w' in json_data)):
                                    time_e = str(json_data['t'])
                                    window = str(json_data['w'])
                                    bw =  str(json_data['b'])
                                    host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -w '+window+' -b '+bw+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                    temp = str(host_client)+'_'+str(server[0])
                                    ax = str(server)
                                    buffer_server.append(temp)
                                    buffer_server.append(ax)
                                    name_files.append(str(host_client)+'_'+str(server[0]))

                                #Solo el parametro de Tiempo con Intervalo y Ventana 
                                elif('t' in json_data and ('i' in json_data) and ( not 'l' in json_data) and (not 'b' in json_data) and ('w' in json_data)):
                                    time_e = str(json_data['t'])
                                    interval = str(json_data['i'])
                                    window =  str(json_data['w'])
                                    host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -i '+interval+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                    temp = str(host_client)+'_'+str(server[0])
                                    ax = str(server)
                                    buffer_server.append(temp)
                                    buffer_server.append(ax)
                                    name_files.append(str(host_client)+'_'+str(server[0]))

                                #Solo el parametro de Tiempo con Intervalo Longitud  Ancho de Banda
                                elif('t' in json_data and ('i' in json_data) and ( 'l' in json_data) and ('b' in json_data) and (not 'w' in json_data)):
                                    time_e = str(json_data['t'])
                                    interval = str(json_data['i'])
                                    length =  str(json_data['l'])
                                    bw = str(json_data['b'])
                                    host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -i '+interval+' -l '+length+' -b '+bw+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                    temp = str(host_client)+'_'+str(server[0])
                                    ax = str(server)
                                    buffer_server.append(temp)
                                    buffer_server.append(ax)
                                    name_files.append(str(host_client)+'_'+str(server[0]))
                                #Solo el parametro de Tiempo con Intervalo Longitud  Ventana
                                elif('t' in json_data and ('i' in json_data) and ( 'l' in json_data) and (not 'b' in json_data) and ('w' in json_data)):
                                    time_e = str(json_data['t'])
                                    interval = str(json_data['i'])
                                    length =  str(json_data['l'])
                                    window = str(json_data['w'])
                                    host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -i '+interval+' -l '+length+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                    temp = str(host_client)+'_'+str(server[0])
                                    ax = str(server)
                                    buffer_server.append(temp)
                                    buffer_server.append(ax)
                                    name_files.append(str(host_client)+'_'+str(server[0]))
                                #Solo el parametro de Tiempo con Ancho de Banda Longitud  Ventana
                                elif('t' in json_data and (not 'i' in json_data) and ( 'l' in json_data) and ('b' in json_data) and ('w' in json_data)):
                                    time_e = str(json_data['t'])
                                    bw = str(json_data['b'])
                                    length =  str(json_data['l'])
                                    window = str(json_data['w'])
                                    host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -b '+bw+' -l '+length+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                    temp = str(host_client)+'_'+str(server[0])
                                    ax = str(server)
                                    buffer_server.append(temp)
                                    buffer_server.append(ax)
                                    name_files.append(str(host_client)+'_'+str(server[0]))
                                #Solo el parametro de Tiempo con Intervalo Longitud  Ancho de Banda Ventana
                                elif('t' in json_data and ('i' in json_data) and ( 'l' in json_data) and ('b' in json_data) and ('w' in json_data)):
                                    time_e = str(json_data['t'])
                                    interval = str(json_data['i'])
                                    length =  str(json_data['l'])
                                    bw = str(json_data['b'])
                                    window = str(json_data['w'])
                                    host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -i '+interval+' -l '+length+' -b '+bw+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                    temp = str(host_client)+'_'+str(server[0])
                                    ax = str(server)
                                    buffer_server.append(temp)
                                    buffer_server.append(ax)
                                    name_files.append(str(host_client)+'_'+str(server[0]))

                                #Solo el parámetro de Intervalo
                                elif(not 't' in json_data and ('i' in json_data) and (not 'l' in json_data) and (not 'b' in json_data) and (not 'w' in json_data)):
                                    interval = str(json_data['i'])
                                    host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -i '+interval+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                    temp = str(host_client)+'_'+str(server[0])
                                    ax = str(server)
                                    buffer_server.append(temp)
                                    buffer_server.append(ax)
                                    name_files.append(str(host_client)+'_'+str(server[0]))

                                #Solo el parámetro de Intervalo y Longitud
                                elif(not 't' in json_data and ('i' in json_data) and ('l' in json_data) and (not 'b' in json_data) and (not 'w' in json_data)):
                                    interval = str(json_data['i'])
                                    length = str(json_data['l'])
                                    host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -i '+interval+' -l ' +length+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                    temp = str(host_client)+'_'+str(server[0])
                                    ax = str(server)
                                    buffer_server.append(temp)
                                    buffer_server.append(ax)
                                    name_files.append(str(host_client)+'_'+str(server[0]))

                                #Solo el parámetro de Intervalo y Anchode Banda
                                elif(not 't' in json_data and ('i' in json_data) and (not 'l' in json_data) and ('b' in json_data) and (not 'w' in json_data)):
                                    interval = str(json_data['i'])
                                    bw = str(json_data['b'])
                                    host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -i '+interval+' -b '+bw+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                    temp = str(host_client)+'_'+str(server[0])
                                    ax = str(server)
                                    buffer_server.append(temp)
                                    buffer_server.append(ax)
                                    name_files.append(str(host_client)+'_'+str(server[0]))

                                #Solo el parámetro de Intervalo y Ventana
                                elif(not 't' in json_data and ('i' in json_data) and (not 'l' in json_data) and (not 'b' in json_data) and ('w' in json_data)):
                                    interval = str(json_data['i'])
                                    window = str(json_data['w'])
                                    host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -i '+interval+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                    temp = str(host_client)+'_'+str(server[0])
                                    ax = str(server)
                                    buffer_server.append(temp)
                                    buffer_server.append(ax)
                                    name_files.append(str(host_client)+'_'+str(server[0]))

                                #Solo el parámetro de Intervalo, Anchode Banda y Longitud
                                elif(not 't' in json_data and ('i' in json_data) and ('l' in json_data) and ('b' in json_data) and (not 'w' in json_data)):
                                    interval = str(json_data['i'])
                                    bw = str(json_data['b'])
                                    length = str(json_data['l'])
                                    host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -i '+interval+' -b '+bw+' -l '+length+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                    temp = str(host_client)+'_'+str(server[0])
                                    ax = str(server)
                                    buffer_server.append(temp)
                                    buffer_server.append(ax)
                                    name_files.append(str(host_client)+'_'+str(server[0]))

                                #Solo el parámetro de Intervalo, Anchode Banda y Window
                                elif(not 't' in json_data and ('i' in json_data) and (not 'l' in json_data) and ( 'b' in json_data) and ( 'w' in json_data)):
                                    interval = str(json_data['i'])
                                    bw = str(json_data['b'])
                                    window = str(json_data['w'])
                                    host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -i '+interval+' -b '+bw+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                    temp = str(host_client)+'_'+str(server[0])
                                    ax = str(server)
                                    buffer_server.append(temp)
                                    buffer_server.append(ax)
                                    name_files.append(str(host_client)+'_'+str(server[0]))

                                #Solo el parámetro de Intervalo, Longitud y Window
                                elif(not 't' in json_data and ('i' in json_data) and ('l' in json_data) and (not 'b' in json_data) and ( 'w' in json_data)):
                                    interval = str(json_data['i'])
                                    length = str(json_data['l'])
                                    window = str(json_data['w'])
                                    host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -i '+interval+' -l '+length+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                    temp = str(host_client)+'_'+str(server[0])
                                    ax = str(server)
                                    buffer_server.append(temp)
                                    buffer_server.append(ax)
                                    name_files.append(str(host_client)+'_'+str(server[0]))


                                #Solo el parámetro de Intervalo, Anchode Banda, Longitud y Window
                                elif(not 't' in json_data and ('i' in json_data) and ('l' in json_data) and ('b' in json_data) and ('w' in json_data)):
                                    interval = str(json_data['i'])
                                    bw = str(json_data['b'])
                                    length = str(json_data['l'])
                                    window = str(json_data['w'])
                                    host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -i '+interval+' -b '+bw+' -l '+length+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                    temp = str(host_client)+'_'+str(server[0])
                                    ax = str(server)
                                    buffer_server.append(temp)
                                    buffer_server.append(ax)
                                    name_files.append(str(host_client)+'_'+str(server[0]))

                              #Solo el parámetro de Longitud
                                elif(not 't' in json_data and (not 'i' in json_data) and ('n' in json_data) and (not 'b' in json_data) and (not 'w' in json_data)):
                                    length = str(json_data['n'])
                                    host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -n '+length+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                    temp = str(host_client)+'_'+str(server[0])
                                    ax = str(server)
                                    buffer_server.append(temp)
                                    buffer_server.append(ax)
                                    name_files.append(str(host_client)+'_'+str(server[0]))
                                    last_file = str(host_client)+'_'+str(server[0])+'.json'
                                    

                              #Solo el parámetro de Longitud y Ancho de Banda
                                elif(not 't' in json_data and (not 'i' in json_data) and ('l' in json_data) and ('b' in json_data) and (not 'w' in json_data)):
                                    length = str(json_data['l'])
                                    bw = str(json_data['b'])
                                    host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -l '+length+' -b '+bw+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                    temp = str(host_client)+'_'+str(server[0])
                                    ax = str(server)
                                    buffer_server.append(temp)
                                    buffer_server.append(ax)
                                    name_files.append(str(host_client)+'_'+str(server[0]))

                                #Solo el parámetro de Longitud y Ventana
                                elif(not 't' in json_data and (not 'i' in json_data) and ('l' in json_data) and (not 'b' in json_data) and ('w' in json_data)):
                                    length = str(json_data['l'])
                                    window = str(json_data['w'])
                                    host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -l '+length+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                    temp = str(host_client)+'_'+str(server[0])
                                    ax = str(server)
                                    buffer_server.append(temp)
                                    buffer_server.append(ax)
                                    name_files.append(str(host_client)+'_'+str(server[0]))
                                #Solo el parámetro de Longitud   Ancho de Banda y Ventana
                                elif(not 't' in json_data and (not 'i' in json_data) and ('l' in json_data) and ('b' in json_data) and ('w' in json_data)):
                                    length = str(json_data['l'])
                                    bw = str(json_data['b'])
                                    window = str(json_data['w'])
                                    host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -l '+length+' -b '+bw+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                    temp = str(host_client)+'_'+str(server[0])
                                    ax = str(server)
                                    buffer_server.append(temp)
                                    buffer_server.append(ax)
                                    name_files.append(str(host_client)+'_'+str(server[0]))
                                
                                #Solo el parámetro de Ancho de Banda
                                elif(not 't' in json_data and (not 'i' in json_data) and (not 'l' in json_data) and ('b' in json_data) and (not 'w' in json_data)):
                                    bw = str(json_data['b'])
                                    host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -b '+bw+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                    temp = str(host_client)+'_'+str(server[0])
                                    ax = str(server)
                                    buffer_server.append(temp)
                                    buffer_server.append(ax)
                                    name_files.append(str(host_client)+'_'+str(server[0]))

                                #Solo el parámetro de  Ancho de Banda y Ventana
                                elif(not 't' in json_data and (not 'i' in json_data) and (not 'l' in json_data) and ('b' in json_data) and ('w' in json_data)):
                                    
                                    bw = str(json_data['b'])
                                    window = str(json_data['w'])
                                    host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -b '+bw+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                    temp = str(host_client)+'_'+str(server[0])
                                    ax = str(server)
                                    buffer_server.append(temp)
                                    buffer_server.append(ax)
                                    name_files.append(str(host_client)+'_'+str(server[0]))

                                #Solo el parámetro de Longitud   Ancho de Banda y Ventana
                                elif(not 't' in json_data and (not 'i' in json_data) and ('l' in json_data) and ('b' in json_data) and ('w' in json_data)):
                                    length = str(json_data['l'])
                                    bw = str(json_data['b'])
                                    window = str(json_data['w'])
                                    host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -l '+length+' -b '+bw+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                    temp = str(host_client)+'_'+str(server[0])
                                    ax = str(server)
                                    buffer_server.append(temp)
                                    buffer_server.append(ax)
                                    name_files.append(str(host_client)+'_'+str(server[0]))

                                 #Solo el parametro de Tiempo Intervalo  Ancho de Banda Ventana
                                
                                elif('t' in json_data and ('i' in json_data) and (not 'l' in json_data) and ('b' in json_data) and ('w' in json_data)):
                                    time_e = str(json_data['t'])
                                    bw = str(json_data['b'])
                                    interval =  str(json_data['i'])
                                    window = str(json_data['w'])
                                    host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -b '+bw+' -i '+interval+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                    temp = str(host_client)+'_'+str(server[0])
                                    ax = str(server)
                                    buffer_server.append(temp)
                                    buffer_server.append(ax)
                                    name_files.append(str(host_client)+'_'+str(server[0]))

                                 #Solo el parametro de  Ventana
                                
                                elif(not 't' in json_data and (not 'i' in json_data) and (not'l' in json_data) and (not 'b' in json_data) and ('w' in json_data)):
                                    window = str(json_data['w'])
                                    host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                    temp = str(host_client)+'_'+str(server[0])
                                    ax = str(server)
                                    buffer_server.append(temp)
                                    buffer_server.append(ax)
                                    name_files.append(str(host_client)+'_'+str(server[0]))
    
                            #host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -i '+interval+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
            time.sleep(1)
            task_incomplete = True
            num_interval = 1
            archivo = ''
            #Comprobar que el ultimo archivo generado esta completo para seguir con la ejecucion 
            while task_incomplete == True:
                archivo = open(str(last_file)).read()
                if len(archivo) > 0:
                    json_last_file = json.loads(archivo)
                    if "sender_tcp_congestion" in json_last_file:
                        num_interval = len(json_last_file['intervals'])
                        print('Ja ', num_interval)
                        task_incomplete = False
                        break
            
            #Tiempo de espera para q se generen por completo los archivos JSON
            #if time_e != '0':
                #time.sleep(int(time_e) + 2)

            #Abre el archivo correspondiente al trafico de los clientes y lo pasa a Dict
            print('Leyendo Resultados de los Clientes...')
            for name in name_files:
                    
                    archive_json = json.loads(open(str(name)+'.json').read())
                    dict_data_traffic[str(name)] = archive_json
                    os.system('echo %s|sudo -S %s' % ('Okm1234$', 'rm -r '+str(name)+'.json'))

            #Abre el archivo correspondiente al trafico de los servidores y lo pasa a Dict
            print('Leyendo Resultados de los Servidores...')
            for name_server in name_files_server:
                    
                    archive_json_server = json.loads(open(str(name_server)+'.json').read())                    
                    dict_data_traffic_server[str(name_server)] = archive_json_server
                    os.system('echo %s|sudo -S %s' % ('Okm1234$', 'rm -r '+str(name_server)+'.json'))

            



            #Diccionario que almacena la respueta para Django
            traffic = {}
            #Carga los archivos del cliente a un dict para la respuesta del servidor a Django
            print('Generando Salida de los Servidores...')
            for name_server in name_files_server:
                #print(str(name))
                connected = dict_data_traffic_server[str(name_server)]['start']['connected'][0]
                #print('tipo: ', type(connected))

                #datos del host que actua como transmisor
                local_host = connected['local_host']
                local_port = connected['local_port']

                #datos del host que actua como servidor
                #remote_host = dict_data_traffic_server[str(name_server)]['start']['connecting_to']['host']
                #remote_port = dict_data_traffic_server[str(name_server)]['start']['connecting_to']['port']

                #datos de los parámetros del tráfico en la red
                tcp_mss_default = dict_data_traffic_server[str(name_server)]['start']['tcp_mss_default']
                sock_bufsize = dict_data_traffic_server[str(name_server)]['start']['sock_bufsize']
                sndbuf_actual = dict_data_traffic_server[str(name_server)]['start']['sndbuf_actual']
                rcvbuf_actual = dict_data_traffic_server[str(name_server)]['start']['rcvbuf_actual'] 

                #datos del inicio del Test
                protocol = dict_data_traffic_server[str(name_server)]['start']['test_start']['protocol']
                blksize =  dict_data_traffic_server[str(name_server)]['start']['test_start']['blksize']
                omit =  dict_data_traffic_server[str(name_server)]['start']['test_start']['omit']
                duration =  dict_data_traffic_server[str(name_server)]['start']['test_start']['duration']
                num_bytes =  dict_data_traffic_server[str(name_server)]['start']['test_start']['bytes']
                blocks =  dict_data_traffic_server[str(name_server)]['start']['test_start']['blocks']

                rang = 1
                #if time_e != '0' :
                    #Resultados del Tráfico generado
                    #rang = int(time_e)/int(interval)
                
                intervals = dict_data_traffic_server[str(name_server)]['intervals']
                #print(intervals)
                times = {}
                data_speciffic= {}

                for t in range(int(num_interval)):
                    streams = intervals[t]['streams'][0]
                    start = streams['start']
                    end = streams['end']
                    n_bytes = streams['bytes']
                    bits_per_second = streams['bits_per_second']
                    omitted = streams['omitted']
                    sender = streams['sender']

                    data_speciffic['start'] = start
                    data_speciffic['end'] = end
                    data_speciffic['n_bytes'] = n_bytes
                    data_speciffic['bits_per_second'] = bits_per_second
                    data_speciffic['omitted'] = str(omitted)
                    data_speciffic['sender'] = str(sender)

                    times['t_'+str(t)] = data_speciffic
                    data_speciffic = {}

                data_gen['local_host'] = local_host
                data_gen['local_port'] = local_port
                #data_gen['remote_host'] = remote_host
                #data_gen['remote_port'] = remote_port
                data_gen['tcp_mss_default'] = tcp_mss_default
                data_gen['sock_bufsize'] = sock_bufsize
                data_gen['sndbuf_actual'] = sndbuf_actual
                data_gen['rcvbuf_actual'] = rcvbuf_actual
                data_gen['protocol'] = protocol
                data_gen['blksize'] = blksize
                data_gen['omit'] = omit
                data_gen['duration'] = duration
                data_gen['num_bytes'] = num_bytes
                data_gen['blocks'] = blocks
                procces_data['speciffic'] = times
                procces_data['general']= data_gen
                
                traffic[str(name_server)] = procces_data
                
                data_gen= {}
                times = {}
                procces_data = {}
            name_files_server = []

            #Carga los archivos a un diccionario para la respuesta del servidor a Django
            print('Generando Salida de los Clientes...')
            for name in name_files:
                #print(str(name))
                connected = dict_data_traffic[str(name)]['start']['connected'][0]
                #print('tipo: ', type(connected))

                #datos del host que actua como transmisor
                local_host = connected['local_host']
                local_port = connected['local_port']

                #datos del host que actua como servidor
                remote_host = dict_data_traffic[str(name)]['start']['connecting_to']['host']
                remote_port = dict_data_traffic[str(name)]['start']['connecting_to']['port']

                #datos de los parámetros del tráfico en la red
                tcp_mss_default = dict_data_traffic[str(name)]['start']['tcp_mss_default']
                sock_bufsize = dict_data_traffic[str(name)]['start']['sock_bufsize']
                sndbuf_actual = dict_data_traffic[str(name)]['start']['sndbuf_actual']
                rcvbuf_actual = dict_data_traffic[str(name)]['start']['rcvbuf_actual'] 

                #datos del inicio del Test
                protocol = dict_data_traffic[str(name)]['start']['test_start']['protocol']
                blksize =  dict_data_traffic[str(name)]['start']['test_start']['blksize']
                omit =  dict_data_traffic[str(name)]['start']['test_start']['omit']
                duration =  dict_data_traffic[str(name)]['start']['test_start']['duration']
                num_bytes =  dict_data_traffic[str(name)]['start']['test_start']['bytes']
                blocks =  dict_data_traffic[str(name)]['start']['test_start']['blocks']
                    
                #Resultados del Tráfico generado
                rang = int(time_e)/int(interval)
                intervals = dict_data_traffic[str(name)]['intervals']
                times = {}
                data_speciffic= {}

                for t in range(int(num_interval)):
                    streams = intervals[t]['streams'][0]
                    start = streams['start']
                    end = streams['end']
                    n_bytes = streams['bytes']
                    bits_per_second = streams['bits_per_second']
                    retransmits = streams['retransmits']
                    snd_cwnd = streams['snd_cwnd']
                    rtt = streams['rtt']
                    rttvar = streams['rttvar']
                    pmtu = streams['pmtu']
                    omitted = streams['omitted']
                    sender = streams['sender']

                    data_speciffic['start'] = start
                    data_speciffic['end'] = end
                    data_speciffic['n_bytes'] = n_bytes
                    data_speciffic['bits_per_second'] = bits_per_second
                    data_speciffic['retransmits'] = retransmits
                    data_speciffic['snd_cwnd'] = snd_cwnd
                    data_speciffic['rtt'] = rtt
                    data_speciffic['rttvar'] = rttvar
                    data_speciffic['pmtu'] = pmtu
                    data_speciffic['omitted'] = str(omitted)
                    data_speciffic['sender'] = str(sender)

                    times['t_'+str(t)] = data_speciffic
                    data_speciffic = {}

                data_gen['local_host'] = local_host
                data_gen['local_port'] = local_port
                data_gen['remote_host'] = remote_host
                data_gen['remote_port'] = remote_port
                data_gen['tcp_mss_default'] = tcp_mss_default
                data_gen['sock_bufsize'] = sock_bufsize
                data_gen['sndbuf_actual'] = sndbuf_actual
                data_gen['rcvbuf_actual'] = rcvbuf_actual
                data_gen['protocol'] = protocol
                data_gen['blksize'] = blksize
                data_gen['omit'] = omit
                data_gen['duration'] = duration
                data_gen['num_bytes'] = num_bytes
                data_gen['blocks'] = blocks
                procces_data['speciffic'] = times
                procces_data['general']= data_gen
                
                traffic[str(name)] = procces_data
                
                data_gen= {}
                times = {}
                procces_data = {}
            name_files = []
            
            tend = time.time()
            totaltime = tend - tstart
            print('Tiempo de Ejecucion: ',totaltime)
            print('Proceso Finalizado...')

            return traffic

        elif('xtreme' in json_data):
            pass
        elif('specific' in json_data):
            pass
        pass
    elif 'UDP' in json_data:
        pass
    else:
        print('Creando el Arreglo de la Red ...')
        # Contiene el diccionario de la clave Items
        array_data = content['items']

        ipClient = content['IpClient']
        aux = ""
        for ip in ipClient:
            ip_sh = ip[0]
            aux = aux+ip
        # Establece en el Bash la direccion del cliente  en el DISPPLAY
        os.environ["DISPLAY"] = aux+':0.0'
        # w.start()
        for x in array_data:
            id = x['id'][0]
            if id == 'h':
                host_group.append(x)
            elif id == 's':
                swithc_group.append(x)
            elif id == 'c':
                controller_group.append(x)
            elif id == 'l':
                link_group.append(x)
            elif id == 'e':
                port_group.append(x)
            else:
                print("None")

        for x in host_group:
            host_container.append(x['id'])
        for y in swithc_group:
            switch_container.append(y['id'])
        for z in controller_group:
            controller_container.append(z['id'])
        for cn in link_group:
            link_container.append(cn['connection'])
            aux = {
                'cn': cn['connection'], 'intfName1': cn['intfName1'], 'intfName2': cn['intfName2']}
            link_array.append(aux)
        

        
        print('Creacion de la Red ...')


        for b in host_container:
            host_added.append(net.addHost(b))
        print('Hosts Creados ...')

        for d in switch_container:
            switch_added.append(net.addSwitch(d))
        print('Switchs Creados ...')
        for f in controller_container:
            # controller_added.append(net.addController(
            #    name=f, controller=RemoteController, ip='10.556.150', port=6633))
            controller_added.append(net.addController(f))
        print('Controladores Creados ...')
        for n in link_array:
            l = n['cn'].split(",")

        for n in link_array:
            l = n['cn'].split(",")
            for m in switch_added:
                if l[0] == m.name:
                    for j in host_added:
                        if l[1] == j.name:
                            linkeados.append(net.addLink(
                                m, j, intfName1=n['intfName1'], intfName2=n['intfName2']))

        print('Links Creados ...')
        net.start()
        print('RED INICIADA!! ...')

        at = {}
        at['red'] = 'creada'
        return at
    



if __name__ == '__main__':
    app.run(debug= True, host='10.55.6.188')


