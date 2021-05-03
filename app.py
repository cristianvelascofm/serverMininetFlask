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

tstart = None
initial_port = 5000

linkeados = []

host_added = []
switch_added = []
controller_added = []
aux_array = []
aux = []

serversEnabled = False

name_files = []
name_files_server = []
json_data = ''
#Variables para la generacion de trafico ITG

hots_receiver = None
host_sender = None

# Creacion de la red en Mininet
net = Mininet(build=False)


app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})



def wireshark_launcher():
    run_wireshark = subprocess.call(['wireshark-gtk', '-S'])
        


# Creacion del hilo para lanzar Wireshark
w = threading.Thread(target=wireshark_launcher,)


@app.route('/',methods=['GET'])
def get():
    return 'Este es el Sevidor Mininet'

@app.route('/',methods=['POST'])
def executor():
    global serversEnabled, aux_array, name_files, name_files_server, aux, json_data, tstart
    print('\n * Hora ',time.localtime().tm_hour,':',time.localtime().tm_min,':',time.localtime().tm_sec)
    tstart = time.time()
    content = request.json
    contador = 0
    
    json_data = content

    answer_to_client = None 
    charge_array = {}
    traffic_array = {}
    dict_answer = {} #diccionario que se enviará como respuesta al Cliente
    name_files = []
    name_files_server = []
    # Leemos las opciones de operación 
    if 'action' in json_data:
        print(' * Datos: ',content)
        act = json_data['action']
        if act == "stop":
            print(" * Terminando Emulacion ...")
            net.stop()
            os.system('echo %s|sudo -S %s' % ('Okm1234$','sudo mn -c'))
            os.system('echo %s|sudo -S %s' % ('Okm1234$', 'pkill -9 -f "sudo mnexec"'))
            ans = {}
            ans['emulacion'] = 'terminada'
            f = json.dumps(ans)
            serversEnabled = False
            reset_variables()
            print(' * Emulación Terminada')

        return ans
    elif 'TCP' in json_data:
        print(' * Datos: ',content)
        if 'all_for_all' in json_data:
            return tcp_all_for_all_traffic_mode()
        elif 'one_for_all' in json_data:
            return tcp_one_for_all_traffic_mode()
        #Tipos de Distribucion del Tráfico
    elif 'UDP' in json_data:
        pass
    else:
        print(' * Creando el Arreglo de la Red ...')
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
        

        
        print(' * Creacion de la Red ...')


        for b in host_container:
            host_added.append(net.addHost(b))
        print(' * Hosts Creados ...')

        for d in switch_container:
            switch_added.append(net.addSwitch(d))
        print(' * Switchs Creados ...')
        for f in controller_container:
            # controller_added.append(net.addController(
            #    name=f, controller=RemoteController, ip='10.556.150', port=6633))
            controller_added.append(net.addController(f))
        print(' * Controladores Creados ...')
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

        print(' * Links Creados ...')
        net.start()
        print(' * RED INICIADA!! ...')

        at = {}
        at['red'] = 'creada'
        return at
    
def reset_variables():
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
    hots_receiver = None
    host_sender = None
    net = Mininet(build=False)

def reset_traffic(host_client, host_server, port):
    global json_data
    print('Reset_Traffic')
    host_server.cmd('fuser -k -n tcp '+str(port))
    host_server.cmd('iperf3 -s -p '+str(port)+' -J>'+str(host_server)+'_'+str(port)+'.json'+' &')
    time.sleep(1)
    #Solo el parámetro de Tiempo
    if('t' in json_data and (not 'i' in json_data) and (not 'n' in json_data) and (not 'b' in json_data) and (not 'w' in json_data)):
        time_e = str(json_data['t'])
        host_client.cmd('iperf3 -c '+str(host_server.IP())+' -p '+str(port)+' -t '+time_e+' -J>'+str(host_client)+'_'+str(host_server)+'.json'+' &')
    #Solo el parámetro de Tiempo con Intervalo 
    elif('t' in json_data and ('i' in json_data) and (not 'n' in json_data) and (not 'b' in json_data) and (not 'w' in json_data)):
        time_e = str(json_data['t'])
        interval = str(json_data['i'])
        host_client.cmd('iperf3 -c '+str(host_server.IP())+' -p '+str(port)+' -t '+time_e+' -i '+interval+' -J>'+str(host_client)+'_'+str(host_server)+'.json'+' &')
    #Solo el parametro de Tiempo con Longitud 
    elif('t' in json_data and (not 'i' in json_data) and ('n' in json_data) and (not 'b' in json_data) and (not 'w' in json_data)):
        time_e = str(json_data['t'])
        length = str(json_data['n'])
        host_client.cmd('iperf3 -c '+str(host_server.IP())+' -p '+str(port)+' -t '+time_e+' -n '+length+' -J>'+str(host_client)+'_'+str(host_server)+'.json'+' &')
    #Solo el parametro de Tiempo con Ancho de Banda
    elif('t' in json_data and (not 'i' in json_data) and (not 'n' in json_data) and ('b' in json_data) and (not 'w' in json_data)):
        time_e = str(json_data['t'])
        bw = str(json_data['b'])
        host_client.cmd('iperf3 -c '+str(host_server.IP())+' -p '+str(port)+' -t '+time_e+' -b '+bw+' -J>'+str(host_client)+'_'+str(host_server)+'.json'+' &')
    #Solo el parametro de Tiempo con Ventana
    elif('t' in json_data and (not 'i' in json_data) and (not 'n' in json_data) and (not 'b' in json_data) and ('w' in json_data)):
        traffic_mode = 't-w'
        time_e = str(json_data['t'])
        window = str(json_data['w'])
        host_client.cmd('iperf3 -c '+str(host_server.IP())+' -p '+str(port)+' -t '+time_e+' -w '+window+' -J>'+str(host_client)+'_'+str(host_server)+'.json'+' &')
    #Solo el parametro de Tiempo con Intervalo y Longitud
    elif('t' in json_data and ('i' in json_data) and ( 'n' in json_data) and (not 'b' in json_data) and (not 'w' in json_data)):
        time_e = str(json_data['t'])
        interval = str(json_data['i'])
        length =  str(json_data['n'])
        host_client.cmd('iperf3 -c '+str(host_server.IP())+' -p '+str(port)+' -t '+time_e+' -i '+interval+' -n '+length+' -J>'+str(host_client)+'_'+str(host_server)+'.json'+' &')
    #Solo el parametro de Tiempo con Intervalo y Ancho de Banda
    elif('t' in json_data and ('i' in json_data) and ( not 'n' in json_data) and ('b' in json_data) and (not 'w' in json_data)):
        time_e = str(json_data['t'])
        interval = str(json_data['i'])
        bw =  str(json_data['b'])
        host_client.cmd('iperf3 -c '+str(host_server.IP())+' -p '+str(port)+' -t '+time_e+' -i '+interval+' -b '+bw+' -J>'+str(host_client)+'_'+str(host_server)+'.json'+' &')
    #Solo el parametro de Tiempo con Longitud y Ventana
    elif('t' in json_data and (not 'i' in json_data) and ('n' in json_data) and (not 'b' in json_data) and ('w' in json_data)):
        time_e = str(json_data['t'])
        length = str(json_data['n'])
        window =  str(json_data['w'])
        host_client.cmd('iperf3 -c '+str(host_server.IP())+' -p '+str(port)+' -t '+time_e+' -l '+length+' -w '+window+' -J>'+str(host_client)+'_'+str(host_server)+'.json'+' &')
    #Solo el parametro de Tiempo con  Ancho de Banda y Ventana
    elif('t' in json_data and (not 'i' in json_data) and (not 'n' in json_data) and ('b' in json_data) and ('w' in json_data)):
        time_e = str(json_data['t'])
        window = str(json_data['w'])
        bw =  str(json_data['b'])
        host_client.cmd('iperf3 -c '+str(host_server.IP())+' -p '+str(port)+' -t '+time_e+' -w '+window+' -b '+bw+' -J>'+str(host_client)+'_'+str(host_server)+'.json'+' &')
    #Solo el parametro de Tiempo con Intervalo y Ventana 
    elif('t' in json_data and ('i' in json_data) and ( not 'n' in json_data) and (not 'b' in json_data) and ('w' in json_data)):
        time_e = str(json_data['t'])
        interval = str(json_data['i'])
        window =  str(json_data['w'])
        host_client.cmd('iperf3 -c '+str(host_server.IP())+' -p '+str(port)+' -t '+time_e+' -i '+interval+' -w '+window+' -J>'+str(host_client)+'_'+str(host_server)+'.json'+' &')
    #Solo el parametro de Tiempo con Intervalo Longitud  Ancho de Banda
    elif('t' in json_data and ('i' in json_data) and ( 'n' in json_data) and ('b' in json_data) and (not 'w' in json_data)):
        time_e = str(json_data['t'])
        interval = str(json_data['i'])
        length =  str(json_data['n'])
        bw = str(json_data['b'])
        host_client.cmd('iperf3 -c '+str(host_server.IP())+' -p '+str(port)+' -t '+time_e+' -i '+interval+' -n '+length+' -b '+bw+' -J>'+str(host_client)+'_'+str(host_server)+'.json'+' &')
    #Solo el parametro de Tiempo con Intervalo Longitud  Ventana
    elif('t' in json_data and ('i' in json_data) and ( 'n' in json_data) and (not 'b' in json_data) and ('w' in json_data)):
        time_e = str(json_data['t'])
        interval = str(json_data['i'])
        length =  str(json_data['l'])
        window = str(json_data['w'])
        host_client.cmd('iperf3 -c '+str(host_server.IP())+' -p '+str(port)+' -t '+time_e+' -i '+interval+' -n '+length+' -w '+window+' -J>'+str(host_client)+'_'+str(host_server)+'.json'+' &')
    #Solo el parametro de Tiempo con Ancho de Banda Longitud  Ventana
    elif('t' in json_data and (not 'i' in json_data) and ( 'n' in json_data) and ('b' in json_data) and ('w' in json_data)):
        time_e = str(json_data['t'])
        bw = str(json_data['b'])
        length =  str(json_data['n'])
        window = str(json_data['w'])
        host_client.cmd('iperf3 -c '+str(host_server.IP())+' -p '+str(port)+' -t '+time_e+' -b '+bw+' -n '+length+' -w '+window+' -J>'+str(host_client)+'_'+str(host_server)+'.json'+' &')
    #Solo el parametro de Tiempo con Intervalo Longitud  Ancho de Banda Ventana
    elif('t' in json_data and ('i' in json_data) and ( 'n' in json_data) and ('b' in json_data) and ('w' in json_data)):
        time_e = str(json_data['t'])
        interval = str(json_data['i'])
        length =  str(json_data['n'])
        bw = str(json_data['b'])
        window = str(json_data['w'])
        host_client.cmd('iperf3 -c '+str(host_server.IP())+' -p '+str(port)+' -t '+time_e+' -i '+interval+' -n '+length+' -b '+bw+' -w '+window+' -J>'+str(host_client)+'_'+str(host_server)+'.json'+' &')
    #Solo el parámetro de Intervalo
    elif(not 't' in json_data and ('i' in json_data) and (not 'n' in json_data) and (not 'b' in json_data) and (not 'w' in json_data)):
        interval = str(json_data['i'])
        host_client.cmd('iperf3 -c '+str(host_server.IP())+' -p '+str(port)+' -i '+interval+' -J>'+str(host_client)+'_'+str(host_server)+'.json'+' &')
    #Solo el parámetro de Intervalo y Longitud
    elif(not 't' in json_data and ('i' in json_data) and ('n' in json_data) and (not 'b' in json_data) and (not 'w' in json_data)):
        interval = str(json_data['i'])
        length = str(json_data['n'])
        host_client.cmd('iperf3 -c '+str(host_server.IP())+' -p '+str(port)+' -i '+interval+' -n ' +length+' -J>'+str(host_client)+'_'+str(host_server)+'.json'+' &')
    #Solo el parámetro de Intervalo y Anchode Banda
    elif(not 't' in json_data and ('i' in json_data) and (not 'n' in json_data) and ('b' in json_data) and (not 'w' in json_data)):
        interval = str(json_data['i'])
        bw = str(json_data['b'])
        host_client.cmd('iperf3 -c '+str(host_server.IP())+' -p '+str(port)+' -i '+interval+' -b '+bw+' -J>'+str(host_client)+'_'+str(host_server)+'.json'+' &')
    #Solo el parámetro de Intervalo y Ventana
    elif(not 't' in json_data and ('i' in json_data) and (not 'n' in json_data) and (not 'b' in json_data) and ('w' in json_data)):
        interval = str(json_data['i'])
        window = str(json_data['w'])
        host_client.cmd('iperf3 -c '+str(host_server.IP())+' -p '+str(port)+' -i '+interval+' -w '+window+' -J>'+str(host_client)+'_'+str(host_server)+'.json'+' &')
    #Solo el parámetro de Intervalo, Anchode Banda y Longitud
    elif(not 't' in json_data and ('i' in json_data) and ('n' in json_data) and ('b' in json_data) and (not 'w' in json_data)):
        interval = str(json_data['i'])
        bw = str(json_data['b'])
        length = str(json_data['n'])
        host_client.cmd('iperf3 -c '+str(host_server.IP())+' -p '+str(port)+' -i '+interval+' -b '+bw+' -n '+length+' -J>'+str(host_client)+'_'+str(host_server)+'.json'+' &')
    #Solo el parámetro de Intervalo, Anchode Banda y Window
    elif(not 't' in json_data and ('i' in json_data) and (not 'n' in json_data) and ( 'b' in json_data) and ( 'w' in json_data)):
        interval = str(json_data['i'])
        bw = str(json_data['b'])
        window = str(json_data['w'])
        host_client.cmd('iperf3 -c '+str(host_server.IP())+' -p '+str(port)+' -i '+interval+' -b '+bw+' -w '+window+' -J>'+str(host_client)+'_'+str(host_server)+'.json'+' &')
       

    #Solo el parámetro de Intervalo, Longitud y Window
    elif(not 't' in json_data and ('i' in json_data) and ('n' in json_data) and (not 'b' in json_data) and ( 'w' in json_data)):
        interval = str(json_data['i'])
        length = str(json_data['n'])
        window = str(json_data['w'])
        host_client.cmd('iperf3 -c '+str(host_server.IP())+' -p '+str(port)+' -i '+interval+' -n '+length+' -w '+window+' -J>'+str(host_client)+'_'+str(host_server)+'.json'+' &')



    #Solo el parámetro de Intervalo, Anchode Banda, Longitud y Window
    elif(not 't' in json_data and ('i' in json_data) and ('n' in json_data) and ('b' in json_data) and ('w' in json_data)):
        interval = str(json_data['i'])
        bw = str(json_data['b'])
        length = str(json_data['n'])
        window = str(json_data['w'])
        host_client.cmd('iperf3 -c '+str(host_server.IP())+' -p '+str(port)+' -i '+interval+' -b '+bw+' -n '+length+' -w '+window+' -J>'+str(host_client)+'_'+str(host_server)+'.json'+' &')

    #Solo el parámetro de Longitud
    elif(not 't' in json_data and (not 'i' in json_data) and ('n' in json_data) and (not 'b' in json_data) and (not 'w' in json_data)):
        length = str(json_data['n'])
        host_client.cmd('iperf3 -c '+str(host_server.IP())+' -p '+str(port)+' -n '+length+' -J>'+str(host_client)+'_'+str(host_server)+'.json'+' &')


    #Solo el parámetro de Longitud y Ancho de Banda
    elif(not 't' in json_data and (not 'i' in json_data) and ('n' in json_data) and ('b' in json_data) and (not 'w' in json_data)):
        length = str(json_data['n'])
        bw = str(json_data['b'])
        host_client.cmd('iperf3 -c '+str(host_server.IP())+' -p '+str(port)+' -n '+length+' -b '+bw+' -J>'+str(host_client)+'_'+str(host_server)+'.json'+' &')


    #Solo el parámetro de Longitud y Ventana
    elif(not 't' in json_data and (not 'i' in json_data) and ('n' in json_data) and (not 'b' in json_data) and ('w' in json_data)):
        
        length = str(json_data['n'])
        window = str(json_data['w'])
        host_client.cmd('iperf3 -c '+str(host_server.IP())+' -p '+str(port)+' -n '+length+' -w '+window+' -J>'+str(host_client)+'_'+str(host_server)+'.json'+' &')
        

    #Solo el parámetro de Longitud   Ancho de Banda y Ventana
    elif(not 't' in json_data and (not 'i' in json_data) and ('n' in json_data) and ('b' in json_data) and ('w' in json_data)):
        
        length = str(json_data['n'])
        bw = str(json_data['b'])
        window = str(json_data['w'])
        host_client.cmd('iperf3 -c '+str(host_server.IP())+' -p '+str(port)+' -n '+length+' -b '+bw+' -w '+window+' -J>'+str(host_client)+'_'+str(host_server)+'.json'+' &')
        

    #Solo el parámetro de Ancho de Banda
    elif(not 't' in json_data and (not 'i' in json_data) and (not 'n' in json_data) and ('b' in json_data) and (not 'w' in json_data)):
        
        bw = str(json_data['b'])
        host_client.cmd('iperf3 -c '+str(host_server.IP())+' -p '+str(port)+' -b '+bw+' -J>'+str(host_client)+'_'+str(host_server)+'.json'+' &')
        

    #Solo el parámetro de  Ancho de Banda y Ventana
    elif(not 't' in json_data and (not 'i' in json_data) and (not 'n' in json_data) and ('b' in json_data) and ('w' in json_data)):
        
        bw = str(json_data['b'])
        window = str(json_data['w'])
        host_client.cmd('iperf3 -c '+str(host_server.IP())+' -p '+str(port)+' -b '+bw+' -w '+window+' -J>'+str(host_client)+'_'+str(host_server)+'.json'+' &')
        

    #Solo el parámetro de Longitud   Ancho de Banda y Ventana
    elif(not 't' in json_data and (not 'i' in json_data) and ('n' in json_data) and ('b' in json_data) and ('w' in json_data)):
        
        length = str(json_data['n'])
        bw = str(json_data['b'])
        window = str(json_data['w'])
        host_client.cmd('iperf3 -c '+str(host_server.IP())+' -p '+str(port)+' -n '+length+' -b '+bw+' -w '+window+' -J>'+str(host_client)+'_'+str(host_server)+'.json'+' &')
        

    #Solo el parametro de Tiempo Intervalo  Ancho de Banda Ventana
    elif('t' in json_data and ('i' in json_data) and (not 'n' in json_data) and ('b' in json_data) and ('w' in json_data)):
        
        time_e = str(json_data['t'])
        bw = str(json_data['b'])
        interval =  str(json_data['i'])
        window = str(json_data['w'])
        host_client.cmd('iperf3 -c '+str(host_server.IP())+' -p '+str(port)+' -t '+time_e+' -b '+bw+' -i '+interval+' -w '+window+' -J>'+str(host_client)+'_'+str(host_server)+'.json'+' &')
       

    #Solo el parametro de  Ventana
    elif(not 't' in json_data and (not 'i' in json_data) and (not 'n' in json_data) and (not 'b' in json_data) and ('w' in json_data)):
        
        window = str(json_data['w'])
        host_client.cmd('iperf3 -c '+str(host_server.IP())+' -p '+str(port)+' -w '+window+' -J>'+str(host_client)+'_'+str(host_server)+'.json'+' &')


def tcp_all_for_all_traffic_mode():
    global serversEnabled,name_files,name_files_server,json_data, tstart, initial_port
    if('global' in json_data):
        print(' * All for All : TCP')
        host_size= (len(host_added))-1
        port_list =[]
        # Tiempo : t , Intervalo : i, Numero Bytes: n, Ancho de Banda: b,   Ventana: w, Tamaño bloque: l
        #Datos del modo de transmision
        #Solo una de estas tres opciones
        time_e = str('0') #t
        number = '0k'#n
        block = '0k' #k -no used
        interval = str(1) #i
        window = '500k' #w
        length = '1m' #l
        bw = '1k' # b
        traffic_mode = ''
        wait_time = 1
        dict_data_traffic = {}
        dict_data_traffic_server = {}
        file_traffic= []
        data_traffic={}
        procces_data={}
        data_gen= {}
        list_validation = []

        #Lista de Puertos
        for pt in range(host_size):
            initial_port = initial_port + 1
            port_list.append(str(initial_port))

        #Se colocan los host como servidor en el puerto indicado
        if(serversEnabled == True):
            print(' * Reiniciando el Servicio iperf3...')
            os.system('echo %s|sudo -S %s' % ('Okm1234$', 'pkill -9 iperf3'))
            # for serv in aux:
            #    serv[0].cmd('sudo kill 9 $(sudo lsoft -t -i:'+serv[1]+')')

        print(' * Estableciendo Servidores...')
        for host_server in host_added:
            for port in port_list:
                host_server.cmd('iperf3 -s -p '+str(port)+' -J>'+str(host_server)+'_'+str(port)+'.json'+' &')
                time.sleep(0.5)
                name_files_server.append(str(host_server)+'_'+str(port))
                aux = [host_server, port]
                aux_array.append(aux)

        serversEnabled = True
        time.sleep(1)
        buffer_server = []

        print(' * Escablaciendo Clientes...')
        size_host_added = len(host_added)
        size_server = len(aux_array)
        size_port = len(port_list)
        for server in aux_array:
            for host_client in host_added:
                if not (str(host_client)+'_'+str(server[0])) in buffer_server:
                    if not str(server) in buffer_server:
                        if str(server[0]) == str(host_client):
                            pass
                        else:
                            #Posibles casos de parametrizacion del Trafico en Iperf3.1
                            # Solo Tiempo
                            if('t' in json_data and (not 'i' in json_data) and (not 'n' in json_data) and (not 'b' in json_data) and (not 'w' in json_data) and (not 'l' in json_data)):
                                time_e = str(json_data['t'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Tiempo e Intervalo
                            elif('t' in json_data and ('i' in json_data) and (not 'n' in json_data) and (not 'b' in json_data) and (not 'w' in json_data) and (not 'l' in json_data)):
                                time_e = str(json_data['t'])
                                interval = str(json_data['i'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -i '+interval+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Tiempo e Ancho de banda
                            elif('t' in json_data and (not 'i' in json_data) and (not 'n' in json_data) and ('b' in json_data) and (not 'w' in json_data) and (not 'l' in json_data)):
                                time_e = str(json_data['t'])
                                bw = str(json_data['b'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -b '+bw+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Tiempo e tamaño bloque
                            elif('t' in json_data and (not 'i' in json_data) and (not 'n' in json_data) and (not 'b' in json_data) and (not 'w' in json_data) and ('l' in json_data)):
                                time_e = str(json_data['t'])
                                length = str(json_data['l'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -l '+length+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Tiempo y ventana
                            elif('t' in json_data and (not 'i' in json_data) and (not 'n' in json_data) and (not 'b' in json_data) and ('w' in json_data) and (not 'l' in json_data)):
                                traffic_mode = 't-w'
                                time_e = str(json_data['t'])
                                window = str(json_data['w'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Tiempo e intervalo e ancho de bnda
                            elif('t' in json_data and ('i' in json_data) and (not 'n' in json_data) and ('b' in json_data) and (not 'w' in json_data) and (not 'l' in json_data)):
                                time_e = str(json_data['t'])
                                interval = str(json_data['i'])
                                bw =  str(json_data['b'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -i '+interval+' -b '+bw+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Tiempo e intervalo e ventana
                            elif('t' in json_data and ('i' in json_data) and (not 'n' in json_data) and (not 'b' in json_data) and ('w' in json_data) and (not 'l' in json_data)):
                                time_e = str(json_data['t'])
                                interval = str(json_data['i'])
                                window =  str(json_data['w'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -i '+interval+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Tiempo e intervalo e tamaño bloque
                            elif('t' in json_data and ('i' in json_data) and (not 'n' in json_data) and (not 'b' in json_data) and (not 'w' in json_data) and ('l' in json_data)):
                                time_e = str(json_data['t'])
                                interval = str(json_data['i'])
                                length =  str(json_data['l'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -i '+interval+' -l '+length+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                           # Solo Tiempo e intervalo e ancho de banda e ventana
                            elif('t' in json_data and ('i' in json_data) and (not 'n' in json_data) and ('b' in json_data) and ('w' in json_data) and (not 'l' in json_data)):
                                time_e = str(json_data['t'])
                                interval = str(json_data['i'])
                                bw =  str(json_data['b'])
                                window = str(json_data['w'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -i '+interval+' -b '+bw+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Tiempo e intervalo e ancho de banda e tamaño bloque
                            elif('t' in json_data and ('i' in json_data) and (not 'n' in json_data) and ('b' in json_data) and (not 'w' in json_data) and ('l' in json_data)):
                                time_e = str(json_data['t'])
                                interval = str(json_data['i'])
                                bw =  str(json_data['b'])
                                length = str(json_data['l'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -i '+interval+' -b '+bw+' -l '+length+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Tiempo e intervalo e ancho de banda e ventana y tamaño bloque
                            elif('t' in json_data and ('i' in json_data) and (not 'n' in json_data) and ('b' in json_data) and ('w' in json_data) and ('l' in json_data)):
                                time_e = str(json_data['t'])
                                interval = str(json_data['i'])
                                bw =  str(json_data['b'])
                                length = str(json_data['l'])
                                window = str(json_data['w'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -i '+interval+' -b '+bw+' -l '+length+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Intervalo
                            elif(not 't' in json_data and ('i' in json_data) and (not 'n' in json_data) and (not 'b' in json_data) and (not 'w' in json_data) and (not 'l' in json_data)):
                                interval = str(json_data['i'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -i '+interval+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Intervalo - Número de Bytes
                            elif(not 't' in json_data and ('i' in json_data) and ('n' in json_data) and (not 'b' in json_data) and (not 'w' in json_data) and (not 'l' in json_data)):
                                interval = str(json_data['i'])
                                number = str(json_data['n'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -i '+interval+' -n '+number+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Intervalo - Ventana
                            elif(not 't' in json_data and ('i' in json_data) and (not 'n' in json_data) and (not 'b' in json_data) and ('w' in json_data) and (not 'l' in json_data)):
                                interval = str(json_data['i'])
                                window = str(json_data['w'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -i '+interval+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                             # Solo Intervalo - Tamaño Bloque
                            elif(not 't' in json_data and ('i' in json_data) and (not 'n' in json_data) and (not 'b' in json_data) and (not 'w' in json_data) and ('l' in json_data)):
                                interval = str(json_data['i'])
                                length = str(json_data['l'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -i '+interval+' -l '+length+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Intervalo - Número de Bytes - Ancho de banda
                            elif(not 't' in json_data and ('i' in json_data) and ('n' in json_data) and ('b' in json_data) and (not 'w' in json_data) and (not 'l' in json_data)):
                                interval = str(json_data['i'])
                                bw = str(json_data['b'])
                                number = str(json_data['n'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -i '+interval+' -b '+bw+' -n '+number+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Intervalo - Número de Bytes - Ventana
                            elif(not 't' in json_data and ('i' in json_data) and ('n' in json_data) and (not 'b' in json_data) and ('w' in json_data) and (not 'l' in json_data)):
                                interval = str(json_data['i'])
                                window = str(json_data['w'])
                                number = str(json_data['n'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -i '+interval+' -w '+window+' -n '+number+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Intervalo - Número de Bytes - Tamaño Bloque
                            elif(not 't' in json_data and ('i' in json_data) and ('n' in json_data) and (not 'b' in json_data) and (not 'w' in json_data) and ('l' in json_data)):
                                interval = str(json_data['i'])
                                length = str(json_data['l'])
                                number = str(json_data['n'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -i '+interval+' -l '+length+' -n '+number+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Intervalo - Número de Bytes - Ancho de banda - ventana
                            elif(not 't' in json_data and ('i' in json_data) and ('n' in json_data) and ('b' in json_data) and ('w' in json_data) and (not 'l' in json_data)):
                                interval = str(json_data['i'])
                                bw = str(json_data['b'])
                                number = str(json_data['n'])
                                window = str(json_data['w'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -i '+interval+' -b '+bw+' -n '+number+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Intervalo - Número de Bytes - Ancho de banda - Tamaño Bloque
                            elif(not 't' in json_data and ('i' in json_data) and ('n' in json_data) and ('b' in json_data) and (not 'w' in json_data) and ('l' in json_data)):
                                interval = str(json_data['i'])
                                bw = str(json_data['b'])
                                number = str(json_data['n'])
                                length = str(json_data['l'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -i '+interval+' -b '+bw+' -n '+number+' -l '+length+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Intervalo - Número de Bytes - Ancho de banda - Ventana - Tamaño Bloque
                            elif(not 't' in json_data and ('i' in json_data) and ('n' in json_data) and ('b' in json_data) and ('w' in json_data) and ('l' in json_data)):
                                interval = str(json_data['i'])
                                bw = str(json_data['b'])
                                number = str(json_data['n'])
                                length = str(json_data['l'])
                                window = str(json_data['w'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -i '+interval+' -b '+bw+' -n '+number+' -l '+length+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Número de Bytes
                            elif(not 't' in json_data and (not 'i' in json_data) and ('n' in json_data) and (not 'b' in json_data) and (not 'w' in json_data) and (not 'l' in json_data)):
                                number = str(json_data['n'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -n '+number+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Número de Bytes - Ancho de banda
                            elif(not 't' in json_data and (not 'i' in json_data) and ('n' in json_data) and ('b' in json_data) and (not 'w' in json_data) and (not 'l' in json_data)):
                                number = str(json_data['n'])
                                bw = str(json_data['b'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -n '+number+' -b '+bw+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Número de Bytes - Ventana
                            elif(not 't' in json_data and (not 'i' in json_data) and ('n' in json_data) and (not 'b' in json_data) and ('w' in json_data) and (not 'l' in json_data)):
                                number = str(json_data['n'])
                                window = str(json_data['w'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -n '+number+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Número de Bytes - Tamaño Bloque
                            elif(not 't' in json_data and (not 'i' in json_data) and ('n' in json_data) and (not 'b' in json_data) and (not 'w' in json_data) and ('l' in json_data)):
                                number = str(json_data['n'])
                                length = str(json_data['l'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -n '+number+' -l '+length+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Número de Bytes - Ancho de Banda - Ventana
                            elif(not 't' in json_data and (not 'i' in json_data) and ('n' in json_data) and ('b' in json_data) and ('w' in json_data) and (not 'l' in json_data)):
                                number = str(json_data['n'])
                                bw = str(json_data['b'])
                                window = str(json_data['w'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -n '+number+' -b '+bw+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                           # Solo Número de Bytes - Ancho de Banda - Tamaño Bloque
                            elif(not 't' in json_data and (not 'i' in json_data) and ('n' in json_data) and ('b' in json_data) and (not 'w' in json_data) and ('l' in json_data)):
                                number = str(json_data['n'])
                                bw = str(json_data['b'])
                                length = str(json_data['l'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -n '+number+' -b '+bw+' -l '+length+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Número de Bytes - Ancho de Banda - Ventana - Tamaño Bloque
                            elif(not 't' in json_data and (not 'i' in json_data) and ('n' in json_data) and ('b' in json_data) and ('w' in json_data) and ('l' in json_data)):
                                number = str(json_data['n'])
                                bw = str(json_data['b'])
                                window = str(json_data['w'])
                                length = str(json_data['l'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -n '+number+' -b '+bw+' -l '+length+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Ancho de Banda
                            elif(not 't' in json_data and (not 'i' in json_data) and (not 'n' in json_data) and ('b' in json_data) and (not 'w' in json_data) and (not 'l' in json_data)):
                                bw = str(json_data['b'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -b '+bw+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Ancho de Banda - Ventana
                            elif(not 't' in json_data and (not 'i' in json_data) and (not 'n' in json_data) and ('b' in json_data) and ('w' in json_data) and (not 'l' in json_data)):
                                bw = str(json_data['b'])
                                window = str(json_data['w'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -b '+bw+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Ancho de Banda - Tmaño Bloque 
                            elif(not 't' in json_data and (not 'i' in json_data) and (not 'n' in json_data) and ('b' in json_data) and (not 'w' in json_data) and ('l' in json_data)):
                                bw = str(json_data['b'])
                                length = str(json_data['l'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -b '+bw+' -l '+length+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Ancho de Banda - Ventana - Tmaño Bloque 
                            elif(not 't' in json_data and (not 'i' in json_data) and (not 'n' in json_data) and ('b' in json_data) and ('w' in json_data) and ('l' in json_data)):
                                length = str(json_data['l'])
                                bw = str(json_data['b'])
                                window = str(json_data['w'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -l '+length+' -b '+bw+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Ventana 
                            elif(not 't' in json_data and (not 'i' in json_data) and (not 'n' in json_data) and (not 'b' in json_data) and ('w' in json_data) and (not 'l' in json_data)):
                                window = str(json_data['w'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Ventana - Tamaño Bloque
                            elif(not 't' in json_data and (not 'i' in json_data) and (not 'n' in json_data) and (not 'b' in json_data) and ('w' in json_data) and ('l' in json_data)):
                                window = str(json_data['w'])
                                length = str(json_data['l'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -w '+window+' -l '+length+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Tamaño Bloque
                            elif(not 't' in json_data and (not 'i' in json_data) and (not 'n' in json_data) and (not 'b' in json_data) and (not 'w' in json_data) and ('l' in json_data)):
                                length = str(json_data['l'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -l '+length+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
        time.sleep(1);
        contador_end = 0
        contador_receiver = 0
        count = 0;
        list_end = []
        list_receiver = []
        name_files_size = len(name_files)
        temporal_file_list = []
        traffic_incomplete = True
        print(" * Generando Tráfico...")
        while traffic_incomplete:
            for element in list_validation:
                file_name = r''+str(element[0])+'_'+str(element[1])+'.json'
                # Si el archivo existe lo lee y revisa si esta completo
                if os.path.exists(file_name):
                    read_file = open(file_name).read()
                    if read_file == '':
                        pass
                    else:
                        try:
                            json_temporal_file = json.loads(read_file)
                        except:
                            pass
                        if 'end' in json_temporal_file :
                            if element in list_end:
                                pass
                            else:
                                list_end.append(element)
                                contador_end += 1
                        if 'receiver_tcp_congestion' in json_temporal_file['end']:
                            if element in list_receiver:
                                pass
                            else:
                                list_receiver.append(element)
                                contador_receiver += 1
                # Si el archivo no existe que reinicie el trafico, creandolo de nuevo en ese par Cliente-Servidor
                else:
                    reset_traffic(element[0], element[1], element[2])
            print('end: ',contador_end,' rec: ',contador_receiver) 
            if contador_receiver == name_files_size and contador_end == contador_receiver :
                traffic_incomplete = False
                break      
            elif (contador_end  == name_files_size and contador_receiver < contador_end) or (contador_end  == name_files_size and contador_receiver > contador_end) :
                resp = {}
                resp['error']: 'Imposible Crear el Tráfico'
                tend = time.time()
                totaltime = tend - tstart
                print('Tiempo de Ejecucion: ',totaltime)
                print('Proceso Finalizado...')
                return(resp)
                break
        

        #Comprobar que los archivos  generados están completos para seguir con la ejecución 
        print(' * Comprobando Archivos Generados...')
        name_files_server_size = len(name_files_server)
        conta = 0
        temporal_file_list_server= []
        while conta < name_files_server_size:
            for server_file in name_files_server:
                read_file = open(str(server_file)+'.json').read()
                if read_file == '':
                    pass
                else :
                    try:

                        json_temporal_file = json.loads(read_file);
                    except:
                        print(server_file)
                        pass
                    
                    if 'receiver_tcp_congestion' in json_temporal_file['end']:
                        if str(server_file) in temporal_file_list_server:
                            pass
                        else:
                            temporal_file_list_server.append(str(server_file))
                            conta += 1
                    else:
                        pass

        time.sleep(1)

        #Abre el archivo correspondiente al trafico de los clientes y lo pasa a Dict
        print(' * Leyendo Resultados de los Clientes...')
        for name in name_files:
            archive_json = json.loads(open(str(name)+'.json').read())
            dict_data_traffic[str(name)] = archive_json
            os.system('echo %s|sudo -S %s' % ('Okm1234$', 'rm -r '+str(name)+'.json'))

        #Abre el archivo correspondiente al trafico de los servidores y lo pasa a Dict
        print(' * Leyendo Resultados de los Servidores...')
        for name_server in name_files_server:
            print(str(name_server))
            archive_json_server = json.loads(open(str(name_server)+'.json').read())                    
            dict_data_traffic_server[str(name_server)] = archive_json_server
            os.system('echo %s|sudo -S %s' % ('Okm1234$', 'rm -r '+str(name_server)+'.json'))

        #Diccionario que almacena la respueta para Django
        traffic = {}
        #Carga los archivos del cliente a un dict para la respuesta del servidor a Django
        print(' * Generando Salida de los Servidores...')
        for name_server in name_files_server:
            print(str(name_server))
            connected = dict_data_traffic_server[str(name_server)]['start']['connected'][0]

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
            
            intervals = dict_data_traffic_server[str(name_server)]['intervals']
            #print(intervals)
            times = {}
            data_speciffic= {}
            number_of_intervals = len(intervals)

            for t in range(int(number_of_intervals)):
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
        print(' * Generando Salida de los Clientes...')
        for name in name_files:
            print(str(name))
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
            number_of_intervals = len(intervals)
            for t in range(int(number_of_intervals)):
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

    elif('specific' in json_data):
        pass
    elif('xtreme' in json_data):
        pass



def tcp_one_for_all_traffic_mode():
    global serversEnabled,name_files,name_files_server,json_data, tstart, initial_port
    if('global' in json_data):
        print(' * One for All : TCP')
        host_size= (len(host_added))-1
        port_list =[]
        # Tiempo : t , Intervalo : i, Numero Bytes: n, Ancho de Banda: b,   Ventana: w, Tamaño bloque: l
        #Datos del modo de transmision
        #Solo una de estas tres opciones
        time_e = str('0') #t
        number = '0k'#n
        block = '0k' #k -no used
        interval = str(1) #i
        window = '500k' #w
        length = '1m' #l
        bw = '1k' # b
        traffic_mode = ''
        wait_time = 1
        dict_data_traffic = {}
        dict_data_traffic_server = {}
        file_traffic= []
        data_traffic={}
        procces_data={}
        data_gen= {}
        list_validation = []

        #Lista de Puertos
        for pt in range(host_size):
            initial_port = initial_port + 1
            port_list.append(str(initial_port))

        #Se colocan los host como servidor en el puerto indicado
        if(serversEnabled == True):
            print(' * Reiniciando el Servicio iperf3...')
            os.system('echo %s|sudo -S %s' % ('Okm1234$', 'pkill -9 iperf3'))
            # for serv in aux:
            #    serv[0].cmd('sudo kill 9 $(sudo lsoft -t -i:'+serv[1]+')')

        print(' * Estableciendo Servidores...')
        for host_server in host_added:
            for port in port_list:
                host_server.cmd('iperf3 -s -p '+str(port)+' -J>'+str(host_server)+'_'+str(port)+'.json'+' &')
                time.sleep(0.5)
                name_files_server.append(str(host_server)+'_'+str(port))
                aux = [host_server, port]
                aux_array.append(aux)

        serversEnabled = True
        time.sleep(1)
        buffer_server = []

        print(' * Escablaciendo Clientes...')
        size_host_added = len(host_added)
        size_server = len(aux_array)
        size_port = len(port_list)
        for server in aux_array:
            for host_client in host_added:
                if not (str(host_client)+'_'+str(server[0])) in buffer_server:
                    if not str(server) in buffer_server:
                        if str(server[0]) == str(host_client):
                            pass
                        else:
                            #Posibles casos de parametrizacion del Trafico en Iperf3.1
                            # Solo Tiempo
                            if('t' in json_data and (not 'i' in json_data) and (not 'n' in json_data) and (not 'b' in json_data) and (not 'w' in json_data) and (not 'l' in json_data)):
                                time_e = str(json_data['t'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -J>'+str(host_client)+'_'+str(server[0])+'.json')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Tiempo e Intervalo
                            elif('t' in json_data and ('i' in json_data) and (not 'n' in json_data) and (not 'b' in json_data) and (not 'w' in json_data) and (not 'l' in json_data)):
                                time_e = str(json_data['t'])
                                interval = str(json_data['i'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -i '+interval+' -J>'+str(host_client)+'_'+str(server[0])+'.json')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Tiempo e Ancho de banda
                            elif('t' in json_data and (not 'i' in json_data) and (not 'n' in json_data) and ('b' in json_data) and (not 'w' in json_data) and (not 'l' in json_data)):
                                time_e = str(json_data['t'])
                                bw = str(json_data['b'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -b '+bw+' -J>'+str(host_client)+'_'+str(server[0])+'.json')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Tiempo e tamaño bloque
                            elif('t' in json_data and (not 'i' in json_data) and (not 'n' in json_data) and (not 'b' in json_data) and (not 'w' in json_data) and ('l' in json_data)):
                                time_e = str(json_data['t'])
                                length = str(json_data['l'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -l '+length+' -J>'+str(host_client)+'_'+str(server[0])+'.json')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Tiempo y ventana
                            elif('t' in json_data and (not 'i' in json_data) and (not 'n' in json_data) and (not 'b' in json_data) and ('w' in json_data) and (not 'l' in json_data)):
                                traffic_mode = 't-w'
                                time_e = str(json_data['t'])
                                window = str(json_data['w'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Tiempo e intervalo e ancho de bnda
                            elif('t' in json_data and ('i' in json_data) and (not 'n' in json_data) and ('b' in json_data) and (not 'w' in json_data) and (not 'l' in json_data)):
                                time_e = str(json_data['t'])
                                interval = str(json_data['i'])
                                bw =  str(json_data['b'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -i '+interval+' -b '+bw+' -J>'+str(host_client)+'_'+str(server[0])+'.json')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Tiempo e intervalo e ventana
                            elif('t' in json_data and ('i' in json_data) and (not 'n' in json_data) and (not 'b' in json_data) and ('w' in json_data) and (not 'l' in json_data)):
                                time_e = str(json_data['t'])
                                interval = str(json_data['i'])
                                window =  str(json_data['w'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -i '+interval+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Tiempo e intervalo e tamaño bloque
                            elif('t' in json_data and ('i' in json_data) and (not 'n' in json_data) and (not 'b' in json_data) and (not 'w' in json_data) and ('l' in json_data)):
                                time_e = str(json_data['t'])
                                interval = str(json_data['i'])
                                length =  str(json_data['l'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -i '+interval+' -l '+length+' -J>'+str(host_client)+'_'+str(server[0])+'.json')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                           # Solo Tiempo e intervalo e ancho de banda e ventana
                            elif('t' in json_data and ('i' in json_data) and (not 'n' in json_data) and ('b' in json_data) and ('w' in json_data) and (not 'l' in json_data)):
                                time_e = str(json_data['t'])
                                interval = str(json_data['i'])
                                bw =  str(json_data['b'])
                                window = str(json_data['w'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -i '+interval+' -b '+bw+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Tiempo e intervalo e ancho de banda e tamaño bloque
                            elif('t' in json_data and ('i' in json_data) and (not 'n' in json_data) and ('b' in json_data) and (not 'w' in json_data) and ('l' in json_data)):
                                time_e = str(json_data['t'])
                                interval = str(json_data['i'])
                                bw =  str(json_data['b'])
                                length = str(json_data['l'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -i '+interval+' -b '+bw+' -l '+length+' -J>'+str(host_client)+'_'+str(server[0])+'.json')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Tiempo e intervalo e ancho de banda e ventana y tamaño bloque
                            elif('t' in json_data and ('i' in json_data) and (not 'n' in json_data) and ('b' in json_data) and ('w' in json_data) and ('l' in json_data)):
                                time_e = str(json_data['t'])
                                interval = str(json_data['i'])
                                bw =  str(json_data['b'])
                                length = str(json_data['l'])
                                window = str(json_data['w'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -t '+time_e+' -i '+interval+' -b '+bw+' -l '+length+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Intervalo
                            elif(not 't' in json_data and ('i' in json_data) and (not 'n' in json_data) and (not 'b' in json_data) and (not 'w' in json_data) and (not 'l' in json_data)):
                                interval = str(json_data['i'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -i '+interval+' -J>'+str(host_client)+'_'+str(server[0])+'.json')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Intervalo - Número de Bytes
                            elif(not 't' in json_data and ('i' in json_data) and ('n' in json_data) and (not 'b' in json_data) and (not 'w' in json_data) and (not 'l' in json_data)):
                                interval = str(json_data['i'])
                                number = str(json_data['n'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -i '+interval+' -n '+number+' -J>'+str(host_client)+'_'+str(server[0])+'.json')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Intervalo - Ventana
                            elif(not 't' in json_data and ('i' in json_data) and (not 'n' in json_data) and (not 'b' in json_data) and ('w' in json_data) and (not 'l' in json_data)):
                                interval = str(json_data['i'])
                                window = str(json_data['w'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -i '+interval+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                             # Solo Intervalo - Tamaño Bloque
                            elif(not 't' in json_data and ('i' in json_data) and (not 'n' in json_data) and (not 'b' in json_data) and (not 'w' in json_data) and ('l' in json_data)):
                                interval = str(json_data['i'])
                                length = str(json_data['l'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -i '+interval+' -l '+length+' -J>'+str(host_client)+'_'+str(server[0])+'.json')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Intervalo - Número de Bytes - Ancho de banda
                            elif(not 't' in json_data and ('i' in json_data) and ('n' in json_data) and ('b' in json_data) and (not 'w' in json_data) and (not 'l' in json_data)):
                                interval = str(json_data['i'])
                                bw = str(json_data['b'])
                                number = str(json_data['n'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -i '+interval+' -b '+bw+' -n '+number+' -J>'+str(host_client)+'_'+str(server[0])+'.json')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Intervalo - Número de Bytes - Ventana
                            elif(not 't' in json_data and ('i' in json_data) and ('n' in json_data) and (not 'b' in json_data) and ('w' in json_data) and (not 'l' in json_data)):
                                interval = str(json_data['i'])
                                window = str(json_data['w'])
                                number = str(json_data['n'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -i '+interval+' -w '+window+' -n '+number+' -J>'+str(host_client)+'_'+str(server[0])+'.json')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Intervalo - Número de Bytes - Tamaño Bloque
                            elif(not 't' in json_data and ('i' in json_data) and ('n' in json_data) and (not 'b' in json_data) and (not 'w' in json_data) and ('l' in json_data)):
                                interval = str(json_data['i'])
                                length = str(json_data['l'])
                                number = str(json_data['n'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -i '+interval+' -l '+length+' -n '+number+' -J>'+str(host_client)+'_'+str(server[0])+'.json')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Intervalo - Número de Bytes - Ancho de banda - ventana
                            elif(not 't' in json_data and ('i' in json_data) and ('n' in json_data) and ('b' in json_data) and ('w' in json_data) and (not 'l' in json_data)):
                                interval = str(json_data['i'])
                                bw = str(json_data['b'])
                                number = str(json_data['n'])
                                window = str(json_data['w'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -i '+interval+' -b '+bw+' -n '+number+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Intervalo - Número de Bytes - Ancho de banda - Tamaño Bloque
                            elif(not 't' in json_data and ('i' in json_data) and ('n' in json_data) and ('b' in json_data) and (not 'w' in json_data) and ('l' in json_data)):
                                interval = str(json_data['i'])
                                bw = str(json_data['b'])
                                number = str(json_data['n'])
                                length = str(json_data['l'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -i '+interval+' -b '+bw+' -n '+number+' -l '+length+' -J>'+str(host_client)+'_'+str(server[0])+'.json')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Intervalo - Número de Bytes - Ancho de banda - Ventana - Tamaño Bloque
                            elif(not 't' in json_data and ('i' in json_data) and ('n' in json_data) and ('b' in json_data) and ('w' in json_data) and ('l' in json_data)):
                                interval = str(json_data['i'])
                                bw = str(json_data['b'])
                                number = str(json_data['n'])
                                length = str(json_data['l'])
                                window = str(json_data['w'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -i '+interval+' -b '+bw+' -n '+number+' -l '+length+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Número de Bytes
                            elif(not 't' in json_data and (not 'i' in json_data) and ('n' in json_data) and (not 'b' in json_data) and (not 'w' in json_data) and (not 'l' in json_data)):
                                number = str(json_data['n'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -n '+number+' -J>'+str(host_client)+'_'+str(server[0])+'.json'+' &')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Número de Bytes - Ancho de banda
                            elif(not 't' in json_data and (not 'i' in json_data) and ('n' in json_data) and ('b' in json_data) and (not 'w' in json_data) and (not 'l' in json_data)):
                                number = str(json_data['n'])
                                bw = str(json_data['b'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -n '+number+' -b '+bw+' -J>'+str(host_client)+'_'+str(server[0])+'.json')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Número de Bytes - Ventana
                            elif(not 't' in json_data and (not 'i' in json_data) and ('n' in json_data) and (not 'b' in json_data) and ('w' in json_data) and (not 'l' in json_data)):
                                number = str(json_data['n'])
                                window = str(json_data['w'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -n '+number+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Número de Bytes - Tamaño Bloque
                            elif(not 't' in json_data and (not 'i' in json_data) and ('n' in json_data) and (not 'b' in json_data) and (not 'w' in json_data) and ('l' in json_data)):
                                number = str(json_data['n'])
                                length = str(json_data['l'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -n '+number+' -l '+length+' -J>'+str(host_client)+'_'+str(server[0])+'.json')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Número de Bytes - Ancho de Banda - Ventana
                            elif(not 't' in json_data and (not 'i' in json_data) and ('n' in json_data) and ('b' in json_data) and ('w' in json_data) and (not 'l' in json_data)):
                                number = str(json_data['n'])
                                bw = str(json_data['b'])
                                window = str(json_data['w'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -n '+number+' -b '+bw+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                           # Solo Número de Bytes - Ancho de Banda - Tamaño Bloque
                            elif(not 't' in json_data and (not 'i' in json_data) and ('n' in json_data) and ('b' in json_data) and (not 'w' in json_data) and ('l' in json_data)):
                                number = str(json_data['n'])
                                bw = str(json_data['b'])
                                length = str(json_data['l'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -n '+number+' -b '+bw+' -l '+length+' -J>'+str(host_client)+'_'+str(server[0])+'.json')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Número de Bytes - Ancho de Banda - Ventana - Tamaño Bloque
                            elif(not 't' in json_data and (not 'i' in json_data) and ('n' in json_data) and ('b' in json_data) and ('w' in json_data) and ('l' in json_data)):
                                number = str(json_data['n'])
                                bw = str(json_data['b'])
                                window = str(json_data['w'])
                                length = str(json_data['l'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -n '+number+' -b '+bw+' -l '+length+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Ancho de Banda
                            elif(not 't' in json_data and (not 'i' in json_data) and (not 'n' in json_data) and ('b' in json_data) and (not 'w' in json_data) and (not 'l' in json_data)):
                                bw = str(json_data['b'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -b '+bw+' -J>'+str(host_client)+'_'+str(server[0])+'.json')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Ancho de Banda - Ventana
                            elif(not 't' in json_data and (not 'i' in json_data) and (not 'n' in json_data) and ('b' in json_data) and ('w' in json_data) and (not 'l' in json_data)):
                                bw = str(json_data['b'])
                                window = str(json_data['w'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -b '+bw+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Ancho de Banda - Tmaño Bloque 
                            elif(not 't' in json_data and (not 'i' in json_data) and (not 'n' in json_data) and ('b' in json_data) and (not 'w' in json_data) and ('l' in json_data)):
                                bw = str(json_data['b'])
                                length = str(json_data['l'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -b '+bw+' -l '+length+' -J>'+str(host_client)+'_'+str(server[0])+'.json')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Ancho de Banda - Ventana - Tmaño Bloque 
                            elif(not 't' in json_data and (not 'i' in json_data) and (not 'n' in json_data) and ('b' in json_data) and ('w' in json_data) and ('l' in json_data)):
                                length = str(json_data['l'])
                                bw = str(json_data['b'])
                                window = str(json_data['w'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -l '+length+' -b '+bw+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Ventana 
                            elif(not 't' in json_data and (not 'i' in json_data) and (not 'n' in json_data) and (not 'b' in json_data) and ('w' in json_data) and (not 'l' in json_data)):
                                window = str(json_data['w'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -w '+window+' -J>'+str(host_client)+'_'+str(server[0])+'.json')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Solo Ventana - Tamaño Bloque
                            elif(not 't' in json_data and (not 'i' in json_data) and (not 'n' in json_data) and (not 'b' in json_data) and ('w' in json_data) and ('l' in json_data)):
                                window = str(json_data['w'])
                                length = str(json_data['l'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -w '+window+' -l '+length+' -J>'+str(host_client)+'_'+str(server[0])+'.json')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
                            # Tamaño Bloque
                            elif(not 't' in json_data and (not 'i' in json_data) and (not 'n' in json_data) and (not 'b' in json_data) and (not 'w' in json_data) and ('l' in json_data)):
                                length = str(json_data['l'])
                                host_client.cmd('iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' -l '+length+' -J>'+str(host_client)+'_'+str(server[0])+'.json')
                                temp = str(host_client)+'_'+str(server[0])
                                ax = str(server)
                                buffer_server.append(temp)
                                buffer_server.append(ax)
                                name_files.append(str(host_client)+'_'+str(server[0]))
                                element_to_validate = []
                                element_to_validate.append(host_client)
                                element_to_validate.append(server[0])
                                element_to_validate.append(server[1])
                                list_validation.append(element_to_validate)
        time.sleep(1);
        contador_end = 0
        contador_receiver = 0
        count = 0;
        list_end = []
        list_receiver = []
        name_files_size = len(name_files)
        temporal_file_list = []
        traffic_incomplete = True
        print(" * Generando Tráfico...")
        while traffic_incomplete:
            for element in list_validation:
                file_name = r''+str(element[0])+'_'+str(element[1])+'.json'
                # Si el archivo existe lo lee y revisa si esta completo
                if os.path.exists(file_name):
                    read_file = open(file_name).read()
                    if read_file == '':
                        pass
                    else:
                        try:
                            json_temporal_file = json.loads(read_file)
                        except:
                            pass
                        if 'end' in json_temporal_file :
                            if element in list_end:
                                pass
                            else:
                                list_end.append(element)
                                contador_end += 1
                        if 'receiver_tcp_congestion' in json_temporal_file['end']:
                            if element in list_receiver:
                                pass
                            else:
                                list_receiver.append(element)
                                contador_receiver += 1
                # Si el archivo no existe que reinicie el trafico, creandolo de nuevo en ese par Cliente-Servidor
                else:
                    reset_traffic(element[0], element[1], element[2])
            print('end: ',contador_end,' rec: ',contador_receiver) 
            if contador_receiver == name_files_size and contador_end == contador_receiver :
                traffic_incomplete = False
                break      
            elif (contador_end  == name_files_size and contador_receiver < contador_end) or (contador_end  == name_files_size and contador_receiver > contador_end) :
                resp = {}
                resp['error']: 'Imposible Crear el Tráfico'
                tend = time.time()
                totaltime = tend - tstart
                print('Tiempo de Ejecucion: ',totaltime)
                print('Proceso Finalizado...')
                return(resp)
                break
        

        #Comprobar que los archivos  generados están completos para seguir con la ejecución 
        print(' * Comprobando Archivos Generados...')
        name_files_server_size = len(name_files_server)
        conta = 0
        temporal_file_list_server= []
        while conta < name_files_server_size:
            for server_file in name_files_server:
                read_file = open(str(server_file)+'.json').read()
                if read_file == '':
                    pass
                else :
                    try:

                        json_temporal_file = json.loads(read_file);
                    except:
                        print(server_file)
                        pass
                    
                    if 'receiver_tcp_congestion' in json_temporal_file['end']:
                        if str(server_file) in temporal_file_list_server:
                            pass
                        else:
                            temporal_file_list_server.append(str(server_file))
                            conta += 1
                    else:
                        pass

        time.sleep(1)

        #Abre el archivo correspondiente al trafico de los clientes y lo pasa a Dict
        print(' * Leyendo Resultados de los Clientes...')
        for name in name_files:
            archive_json = json.loads(open(str(name)+'.json').read())
            dict_data_traffic[str(name)] = archive_json
            os.system('echo %s|sudo -S %s' % ('Okm1234$', 'rm -r '+str(name)+'.json'))

        #Abre el archivo correspondiente al trafico de los servidores y lo pasa a Dict
        print(' * Leyendo Resultados de los Servidores...')
        for name_server in name_files_server:
            print(str(name_server))
            archive_json_server = json.loads(open(str(name_server)+'.json').read())                    
            dict_data_traffic_server[str(name_server)] = archive_json_server
            os.system('echo %s|sudo -S %s' % ('Okm1234$', 'rm -r '+str(name_server)+'.json'))

        #Diccionario que almacena la respueta para Django
        traffic = {}
        #Carga los archivos del cliente a un dict para la respuesta del servidor a Django
        print(' * Generando Salida de los Servidores...')
        for name_server in name_files_server:
            print(str(name_server))
            connected = dict_data_traffic_server[str(name_server)]['start']['connected'][0]

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
            
            intervals = dict_data_traffic_server[str(name_server)]['intervals']
            #print(intervals)
            times = {}
            data_speciffic= {}
            number_of_intervals = len(intervals)

            for t in range(int(number_of_intervals)):
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
        print(' * Generando Salida de los Clientes...')
        for name in name_files:
            print(str(name))
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
            number_of_intervals = len(intervals)
            for t in range(int(number_of_intervals)):
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

    elif('specific' in json_data):
        pass
    elif('xtreme' in json_data):
        pass


#Caca y Popo


if __name__ == '__main__':
    app.run(debug= True, host='10.55.6.188')


