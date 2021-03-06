import json
import os
import sched
import socket
import subprocess
import sys
import threading
import time
from threading import Timer

from pprint import pprint

import mininet.link
import mininet.log
import mininet.node
from flask import Flask, request
from flask_cors import CORS
from mininet.cli import CLI
from mininet.net import Mininet
from mininet.node import Node, Host, Switch, Controller
from mininet.node import CPULimitedHost
from mininet.node import OVSSwitch, RemoteController
from mininet.topo import Topo

# Variables app Flask
app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}}) # Acepta dede todas las direcciones con el *

# Create a variable for the elements of topology
# Estas variables tienen los arreglos de cada elemento de red en cada item
host_group = []
switch_group = []
controller_group = []
link_group = []
port_group = []

# Estas variables solo contienen los nombres de los elementos
host_container = []
switch_container = []
controller_container = []
link_container = []

link_array = []
link_dict = {}
port_container = []

tstart = None

# Estas variables contienen los elementos de red de Mininet 
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


def wireshark_launcher():
    run_wireshark = subprocess.call(['wireshark-gtk', '-S'])
        
# Creacion del hilo para lanzar Wireshark
w = threading.Thread(target=wireshark_launcher,)

@app.route('/',methods=['GET'])
def get():
    return 'Este es el Sevidor Mininet'

@app.route('/',methods=['POST'])
def executor():
    global serversEnabled, aux_array, name_files, name_files_server, aux, json_data, tstart, linkeados, net, host_added, switch_added,controller_added
    print('\n * Hora ',time.localtime().tm_hour,':',time.localtime().tm_min,':',time.localtime().tm_sec)
    tstart = time.time()
    content = request.json
    contador = 0
    
    json_data = content

    answer_to_client = None 
    charge_array = {}
    traffic_array = {}
    dict_answer = {} #diccionario que se enviar?? como respuesta al Cliente
    name_files = []
    name_files_server = []
    
    # Leemos las opciones de operaci??n 
    if 'action' in json_data:
        print(' * Datos: ',content)
        act = json_data['action']

        if act == "stop":
            print(" * Terminando Emulacion...")
            
            stopEmulation()           
            ans = {}
            ans['emulacion'] = 'terminada'
            f = json.dumps(ans)
            serversEnabled = False
            reset_variables()
            print(' * Emulaci??n Terminada con ??xito')

        return ans
    
    #Tipos de Distribucion del Tr??fico
    # Transmission Control Protocol
    elif 'TCP' in json_data:
        print(' * Datos: ',content)
        try:
            answer = traffic_executor_tcp()
            with open('answer.json', 'w') as outfile:
                json.dump(answer, outfile)
            return(answer)
        except:
            print(' * Error: ', sys.exc_info()[0])
            answer = {}
            answer['Error'] = 'Failed to Send Response'
            tend = time.time()
            totaltime = tend - tstart
            print(' * Tiempo de Ejecucion: ',totaltime)
            print(' * Proceso Finalizado...')
            return(answer)

    # User Datagram Protocol
    elif 'UDP' in json_data:
        print(' * Datos: ',content)
        try:
            answer = traffic_executor_udp()
            with open('answer.json', 'w') as outfile:
                json.dump(answer, outfile)
            return(answer)
        except:
            print(' * Error: ', sys.exc_info()[0])
            answer = {}
            answer['Error'] = 'Failed to Send Response'
            tend = time.time()
            totaltime = tend - tstart
            print(' * Tiempo de Ejecucion: ',totaltime)
            print(' * Proceso Finalizado...')
            return(answer)
    else:
        # Creaci??n y Montaje de la Red en Mininet
        
            print(' * Creando el Arreglo de la Red ...')
            # Contiene el diccionario de la clave Items
            array_data = content['items']
            ipClient = content['IpClient']
            aux = ""
            
            for ip in ipClient:
                ip_sh = ip[0]
                aux = aux+ip
            
            # Si existe Direccion Ip se activa wireshark
            if(aux != ''):
                # Establece en el Bash la direccion del cliente  en el DISPPLAY
                os.environ["DISPLAY"] = aux+':0.0'
                # w.start() 

            print(' * Agregando Elementos de Red...')
            for element in array_data:
                element_configuration = {}
                identifier = element['id'][0]
                # Si el elemento es un Controlador
                if identifier == 'c':
                    identify = element['id']
                    cntlr = net.addController(identify)
                    if 'type' in element:
                        if element['type'] == 'OpenFlow Reference Implementation':
                            cntlr.controller = mininet.node.Controller
                        if element['type'] == 'NOX':
                            cntlr.controller=mininet.node.NOX
                        if element['type'] == 'OVS':
                            cntlr.controller=mininet.node.OVS
                        if element['type'] == 'OpenDayLigth':
                            pass
                    if 'ipController' in element:
                        cntlr.ip = element['ipController']
                    if 'port' in element:
                        cntlr.port = int(element['port'])
                        
                    if 'protocol' in element:
                        cntlr.protocol = element['protocol']
                    controller_added.append(cntlr)
                # Si el elemento es un Switch
                if identifier == 's':
                    identify = element['id']
                    switch = net.addSwitch(identify)
                    if 'ipSwitch' in element:
                        switch.ip = element['ipSwitch']
                    if 'verbose' in element:
                        switch.verbose = element['verbose']
                    if 'batch' in element:
                        switch.batch = True
                    if 'inNameSpace' in element:
                        switch.inNamespace = True
                    if 'inBand' in element:
                        switch.inband = True
                    if 'failMode' in element:
                        switch.failMode = element['failMode']
                    if 'reconnectedSwitch' in element:
                        switch.reconnectms = element['reconnectedSwitch']
                    if 'dataPath' in element:
                        switch.dataPath = element['dataPath']
                    if 'dataPathId' in element:
                        switch.dpid = element['dataPathId']
                    if 'dataPathOpt' in element:
                        switch.dpopts = element['dataPathOpt']
                    if 'protocol' in element:
                        switch.protocol = element['protocol']
                    if 'dpctlPort' in element:
                        switch.listenPort = element['dpctlPort']
                    if 'stp' in element:
                        switch.stp = True
                    if 'stpPriority' in element:
                        switch.prio = element['stpPriority']
                    if 'type' in element:
                        if element['type']  == 'IVS Switch':
                            cls=mininet.node.IVSSwitch
                        if element['type']  == 'Linux Bridge':
                            switch.cls = mininet.node.LinuxBridge
                        if element['type']  == 'OVS Brigde':
                            cls=mininet.node.OVSBridge
                        if element['type']  == 'OVS Switch':
                            cls=mininet.node.OVSSwitch
                        if element['type']  == 'User Switch':
                            cls=mininet.node.UserSwitch

                    switch_added.append(switch)
                # Si el elemento es un Host
                if identifier == 'h':
                    identify = element['id']
                    host = net.addHost(identify)
                    # host.ip = None
                    
                    if 'ipHost' in element:
                        
                        host.defaultRoute = 'via '+str(element['ipHost'])
                    if 'sheduler' in element:
                        pass
                        # host.setCPUFrac(sched=element['sheduler'].lower, f = float(element['cpuLimit']))
                        # host.cpu = element['sheduler']
                        # host.cls = mininet.node.CPULimitedHost
                         #host.CPULimitedHost.setCPUFrac().sched = element['sheduler']
                        # host.CPULimitedHost.setCPUFrac().f = element['cpuLimit']
                    # if 'cpuLimit' in element:
                    #    host.cls = mininet.node.CPULimitedHost
                    #    host.setCPUFrac().f = element['cpuLimit']
                    if 'cpuCore' in element:
                        host.cls = mininet.node.CPULimitedHost
                        host.setCPUs(cores = int(element['cpuCore']))
                    
                    host_added.append(host)
            
            print(' * Agregando Enlaces')
            for element in array_data:
                identifier = element['id'][0]
                # Si el elemento es un Enlace
                if identifier == 'l':
                    cn = element['connection']
                    interface1 = element['intfName1']
                    interface2 = element['intfName2']
                    el_cn = cn.split(',')
                    # Si el enlace inicia en un Switch
                    if el_cn[0][0] == 's':
                        for s in switch_added:
                            if s.name == el_cn[0]:
                                for h in host_added:
                                    if h.name == el_cn[1]:
                                        link = net.addLink(s,h, intfName1 = interface1, intfName2 = interface2)
                                        linkeados.append(link)
                                for sa in switch_added:
                                    if sa.name == el_cn[1]:
                                        link = net.addLink(s,sa,intfName1 = interface1, intfName2 = interface2)
                                        linkeados.append(link)
                    # Si el enlace inicia en un Host
                    elif el_cn[0][0] == 'h':
                        for h in host_added:
                            if h.name == el_cn[0]:
                                for s in switch_added:
                                    if s.name == el_cn[1]:
                                        link = net.addLink(s,h, intfName1 = interface1, intfName2 = interface2)
                                        linkeados.append(link)

            print(' * Configurando Interfaces...')
            for element in array_data:
                identifier = element['id'][0]
                # Si el elemento es una Intefaz
                if identifier == 'e':
                    if 'ipPort' in element:
                        pt = element['intf']
                        element_network = pt.split('-')[0]
                        name_interface = pt.split('-')[1]
                        if str(element_network[0]) == 'h':
                            for h in host_added:
                                if element_network == h.name:
                                    interface = str(element['intf'])
                                    h.setIP(str(element['ipPort']), intf= interface, prefixLen= 8)
                        elif str(element_network[0]) == 's':
                            for s in switch_added:
                                if element_network == s.name:
                                    interface = str(element['intf'])
                                    s.setIP(str(element['ipPort']), intf= interface, prefixLen= 8)
                    
            print(' * Construyendo la Red...')
            net.build()

            print(' * Iniciando Controladores...')
            for c in controller_added:
                c.start()
            
            print(' * Iniciando Switchs...')
            for element in array_data:
                for s in switch_added:
                    if element['id'] == s.name: 
                        for c in controller_added:
                            if element['controller'] == c.name:
                                s.start([c])
            
            

            print(' * Red Emulada con ??xito')
            pprint(vars(host_added[0]))
            host_added[0].params['ip'] = '10.0.5.5/8'
            print(' * Red Emulada con ??xito000000000000000')
            pprint(vars(host_added[0]))
            print(' * ', host_added[0].IP())
            print('IP sw: ', host_added[0].cmd('ifconfig -a'))
            at = {}
            at['red'] = 'creada'
            return at


# Comprueba el limite de memoria en la maquina huesped
def machine_condition_checker():
    tot_memory, used_memory, free_memory = map(int, os.popen('free -t -m').readlines()[-1].split()[1:])
    
    if int(free_memory) <= 2048:
        return True
    else:
        return False

#  Devuelve las variables a su estado inicial
def reset_variables():
    global host_group, switch_group,controller_group,link_group,port_group,host_container,switch_container,controller_container,link_container,link_array,link_dict,port_container,linkeados,host_added,switch_added,controller_added,aux_array, aux, serversEnabled,name_files,name_files_server,hots_receiver,host_sender, net

    host_group = []
    switch_group = []
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

def stopEmulation():
    global net,host_added,switch_added,controller_added,linkeados,tstart

    if(len(linkeados) > 0):
        print(" * Borrando Enlaces...")
        for lk in linkeados:
            try:
                net.delLink(lk)
            except:
                print(' * Error: ', sys.exc_info()[0])
                answer = {}
                answer['Error'] = 'Failed to Delete Links'
                print(' * Proceso Finalizado...')
                return(answer)
    if(len(host_added) > 0):
        print(' * Borrando Hosts...')
        for h in host_added:
            try:
                h.stop(deleteIntfs=True)
                net.delHost(h)
            except:
                print(' * Error: ', sys.exc_info()[0])
                answer = {}
                answer['Error'] = 'Failed to Delete Hosts'
                print(' * Proceso Finalizado...')
                return(answer)

    if(len(switch_added) > 0):
        print(' * Borrando Switchs...')
        for s in switch_added:
            try:
                s.stop(deleteIntfs=True)
                net.delSwitch(s)
            except:
                print(' * Error: ', sys.exc_info()[0])
                answer = {}
                answer['Error'] = 'Failed to Delete Switchs'
                print(' * Proceso Finalizado...')
                return(answer)
            
    if(len(controller_added) > 0):
        print(' * Borrando Controladores...')
        for c in controller_added:
            try:
                net.delController(c)
            except:
                print(' * Error: ', sys.exc_info()[0])
                answer = {}
                answer['Error'] = 'Failed to Delete Controllers'
                print(' * Proceso Finalizado...')
                return(answer)

    print(' * Iniciando Secuencia de Parada de la Red en Mininet...')
    try:
        net.stop()
    except:
        print(' * Error: ', sys.exc_info()[0])
        answer = {}
        answer['Error'] = 'Failed to Stop Mininet'
        tend = time.time()
        totaltime = tend - tstart
        print('Tiempo de Ejecucion: ',totaltime)
        print(' * Proceso Finalizado...')
        return(answer)

    # Eliminacion "Manual" de la Red de Mininet
    #os.system('echo %s|sudo -S %s' % ('Okm1234$','mn -c'))
    #os.system('echo %s|sudo -S %s' % ('Okm1234$', 'pkill -9 -f  "sudo mnexec"'))
    #os.system('echo %s|sudo -S %s' % ('Okm1234$', 'pkill -9 -f mininet'))
    #os.system('echo %s|sudo -S %s' % ('Okm1234$', 'pkill -9 -f Tunel=Ethernet'))
    #os.system('echo %s|sudo -S %s' % ('Okm1234$', 'pkill -9 -f .ssh/mn'))
    #os.system('echo %s|sudo -S %s' % ('Okm1234$', 'rm -f ~/.ssh/mn/*'))
    os.system('echo %s|sudo -S %s' % ('123','mn -c'))
    os.system('echo %s|sudo -S %s' % ('123', 'pkill -9 -f  "sudo mnexec"'))
    os.system('echo %s|sudo -S %s' % ('123', 'pkill -9 -f mininet'))
    os.system('echo %s|sudo -S %s' % ('123', 'pkill -9 -f Tunel=Ethernet'))
    os.system('echo %s|sudo -S %s' % ('123', 'pkill -9 -f .ssh/mn'))
    os.system('echo %s|sudo -S %s' % ('123', 'rm -f ~/.ssh/mn/*'))
    reset_variables()
    return(True)

# Reinicia el Tr??fico en un host cliente y un host servidor en particular
def reset_traffic(host_client, host_server, port):
    global json_data
    print(' * Reiniciando Tr??fico en: '+str(host_client)+'-'+str(host_server))
    host_server.cmd('fuser -k -n tcp '+str(port))
    host_server.cmd('iperf3 -s -p '+str(port)+' -J>'+str(host_server)+'_'+str(port)+'.json'+' &')
    time.sleep(1)
     # Variable que contiene las ejecuciones quedebe tomar Iperf3
    trafico = json_data['TCP'][0] # Un dicconario con las posibles opciones Iperf3
    # Se crea la orden estableciendo el host como Cliente enviando trafico al host Servidor en el puerto indicado
    orden = 'iperf3 -c '+str(host_server.IP())+' -p '+str(host_server[1])+' '
    # Se genera la orden con la lectura del diccionario del trafico
    for t in trafico:
        orden = orden+'-'+str(t)+' '+str(trafico[t])+' '
    # Crea la orden Completa dependiendo de que modo tenga One for All o ALl for All
    if 'all_for_all' in json_data:
        #  Agregamos la condicion de que la respuesta la entregue en un archivo Json y que se ejecute en segundo Plano con el '&'
        orden = orden+'-J>'+str(host_client)+'_'+str(host_server[0])+'.json'+' &'
    elif 'one_for_all' in json_data:
        #  Agregamos la condicion de que la respuesta la entregue en un archivo Json y que espera a terminar el proceso ya q no se envia a segundo plano
        orden = orden+'-J>'+str(host_client)+'_'+str(host_server[0])+'.json'
    #  Se Carga la orden al host Cliente
    host_client.cmd(orden)

# Ejecuta el Trafico TCP en Iperf3 
def traffic_executor_tcp():
    
    global serversEnabled,name_files,name_files_server,json_data, tstart    
    host_size= (len(host_added))-1
    port_list =[]
    initial_port = 5000
    # Tiempo : t , Intervalo : i, Numero Bytes: n, Ancho de Banda: b,   Ventana: w, Tama??o bloque: l
    traffic_mode = ''
    wait_time = 1
    dict_data_traffic = {}
    dict_data_traffic_server = {}
    file_traffic= []
    data_traffic={}
    procces_data={}
    data_gen= {}
    list_validation = []
    
    if('global' in json_data):
        print(' * TCP - Global Mode')
        if 'all_for_all' in json_data:
            print(' * All for All Mode')
        elif 'one_for_all' in json_data:
            print(' * One for All Mode')
        #Lista de Puertos
        for pt in range(host_size):
            initial_port = initial_port + 1
            port_list.append(str(initial_port))

        #Se colocan los host como servidor en el puerto indicado
        if(serversEnabled == True):
            try:
                print(' * Reiniciando el Servicio iperf3...')
                #os.system('echo %s|sudo -S %s' % ('Okm1234$', 'pkill -9 iperf3'))
                os.system('echo %s|sudo -S %s' % ('123', 'pkill -9 iperf3'))

                if machine_condition_checker() == True:
                    print(' * Error: L??mite de Memoria Alcanzado')
                    answer = {}
                    answer['Error'] = 'Memory Limit Reached'
                    tend = time.time()
                    totaltime = tend - tstart
                    print(' * Tiempo de Ejecuci??n: ',totaltime)
                    print(' * Proceso Finalizado...')
                    return answer    
            except:
                print(' * Error: ', sys.exc_info()[0])
                answer = {}
                answer['Error'] = 'Failed to Reload Iperf3'
                tend = time.time()
                totaltime = tend - tstart
                print(' * Tiempo de Ejecuci??n: ',totaltime)
                print(' * Proceso Finalizado...')
                return answer
            

        print(' * Estableciendo Servidores...')
        for host_server in host_added:
            for port in port_list:
                try:
                    host_server.cmd('iperf3 -s -p '+str(port)+' -J>'+str(host_server)+'_'+str(port)+'.json'+' &')
                    time.sleep(0.5)
                    name_files_server.append(str(host_server)+'_'+str(port))
                    aux = [host_server, port]
                    aux_array.append(aux)
                    if machine_condition_checker() == True:
                        print(' * Error: L??mite de Memoria Alcanzado')
                        answer = {}
                        answer['Error'] = 'Memory Limit Reached'
                        tend = time.time()
                        totaltime = tend - tstart
                        print(' * Tiempo de Ejecuci??n: ',totaltime)
                        print(' * Proceso Finalizado...')
                        return answer    
                except:
                    print(' * Error: ', sys.exc_info()[0])
                    answer = {}
                    answer['Error'] = 'Failed to Create Servers'
                    tend = time.time()
                    totaltime = tend - tstart
                    print(' * Tiempo de Ejecuci??n: ',totaltime)
                    print(' * Proceso Finalizado...')
                    #os.system('echo %s|sudo -S %s' % ('Okm1234$', 'rm -f *.json'))
                    os.system('echo %s|sudo -S %s' % ('123', 'rm -f *.json'))
                    return answer

        serversEnabled = True
        time.sleep(1)
        buffer_server = []

        print(' * Escablaciendo Clientes...')
        size_host_added = len(host_added)
        size_server = len(aux_array)
        size_port = len(port_list)
        try:
            for server in aux_array:
                    for host_client in host_added:
                        if not (str(host_client)+'_'+str(server[0])) in buffer_server:
                            if not str(server) in buffer_server:
                                if str(server[0]) == str(host_client):
                                    pass
                                else:
                                    # Variable que contiene las ejecuciones quedebe tomar Iperf3
                                    trafico = json_data['TCP'][0] # Un dicconario con las posibles opciones Iperf3
                                    # Se crea la orden estableciendo el host como Cliente enviando trafico al host Servidor en el puerto indicado
                                    orden = 'iperf3 -c '+str(server[0].IP())+' -p '+str(server[1])+' '
                                    # Se genera la orden con la lectura del diccionario del trafico
                                    for t in trafico:
                                        orden = orden+'-'+str(t)+' '+str(trafico[t])+' '

                                    # Crea la orden Completa dependiendo de que modo tenga One for All o ALl for All
                                    if 'all_for_all' in json_data:
                                        #  Agregamos la condicion de que la respuesta la entregue en un archivo Json y que se ejecute en segundo Plano con el '&'
                                        orden = orden+'-J>'+str(host_client)+'_'+str(server[0])+'.json'+' &'
                                    elif 'one_for_all' in json_data:
                                        #  Agregamos la condicion de que la respuesta la entregue en un archivo Json y que espera a terminar el proceso ya q no se envia a segundo plano
                                        orden = orden+'-J>'+str(host_client)+'_'+str(server[0])+'.json'
                                    #  Se Carga la orden al host Cliente
                                    host_client.cmd(orden)
                                    # Creacion de Validadores Futuros
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
                                    # Si alcanza el Limite de Memoria sugerido Crash
                                    if machine_condition_checker() == True:
                                        print(' * Error: L??mite de Memoria Alcanzado')
                                        answer = {}
                                        answer['Error'] = 'Memory Limit Reached'
                                        tend = time.time()
                                        totaltime = tend - tstart
                                        print(' * Tiempo de Ejecucion: ',totaltime)
                                        print(' * Proceso Finalizado...')
                                        return answer
        except:
            print(' * Error: ', sys.exc_info()[0])
            answer={}                   
            answer['Error'] = 'Failed to Create Clients'
            tend = time.time()
            totaltime = tend - tstart
            print(' * Tiempo de Ejecuci??n: ',totaltime)
            print(' * Proceso Finalizado...')
            #os.system('echo %s|sudo -S %s' % ('Okm1234$', 'rm -f *.json'))
            os.system('echo %s|sudo -S %s' % ('123', 'rm -f *.json'))
            return answer
    elif('specific' in json_data):
        print(' * TCP - Specific Mode')
        #Se colocan los host como servidor en el puerto indicado
        if(serversEnabled == True):
            try:
                print(' * Reiniciando el Servicio iperf3...')
                #os.system('echo %s|sudo -S %s' % ('Okm1234$', 'pkill -9 iperf3'))
                os.system('echo %s|sudo -S %s' % ('123', 'pkill -9 iperf3'))


                if machine_condition_checker() == True:
                    print(' * Error: L??mite de Memoria Alcanzado')
                    answer = {}
                    answer['Error'] = 'Memory Limit Reached'
                    tend = time.time()
                    totaltime = tend - tstart
                    print(' * Tiempo de Ejecuci??n: ',totaltime)
                    print(' * Proceso Finalizado...')
                    return answer    
            except:
                print(' * Error: ', sys.exc_info()[0])
                answer = {}
                answer['Error'] = 'Failed to Reload Iperf3'
                tend = time.time()
                totaltime = tend - tstart
                print(' * Tiempo de Ejecuci??n: ',totaltime)
                print(' * Proceso Finalizado...')
                return answer
        # Reconocimiento de los host a quienes se le generar?? tr??fico
        host_as_server = json_data['specific'][0]['host_server']
        host_as_client = json_data['specific'][0]['host_client']

        print(' * Estableciendo el Servidor...')
        for host_server in host_added:
            port = initial_port
            if (str(host_server) == str(host_as_server)):
                host_server.cmd('iperf3 -s -p '+str(port)+' -J>'+str(host_as_server)+'_'+str(port)+'.json'+' &')
                time.sleep(0.5)
                name_files_server.append(str(host_as_server)+'_'+str(port))    
                aux = [host_server, port]
                aux_array.append(aux)
                host_as_server = host_server
        serversEnabled = True 
        print(' * Estableciendo el Cliente...')
        for host_client in host_added:
            port = initial_port
            if (str(host_client) == str(host_as_client)):
                # Variable que contiene las ejecuciones quedebe tomar Iperf3
                trafico = json_data['TCP'][0] # Un dicconario con las posibles opciones Iperf3
                # Se crea la orden estableciendo el host como Cliente enviando trafico al host Servidor en el puerto indicado
                orden = 'iperf3 -c '+str(host_as_server.IP())+' -p '+str(port)+' '
                # Se genera la orden con la lectura del diccionario del trafico
                for t in trafico:
                    orden = orden+'-'+str(t)+' '+str(trafico[t])+' '
                #  Agregamos la condicion de que la respuesta la entregue en un archivo Json y que espera a terminar el proceso ya q no se envia a segundo plano
                orden = orden+'-J>'+str(host_as_client)+'_'+str(host_as_server)+'.json'
                #  Se Carga la orden al host Cliente
                print(' * Cargando Orden en el Cliente ...')
                host_client.cmd(orden)
                # Creacion de Validadores Futuros
                name_files.append(str(host_client)+'_'+str(host_as_server))
                element_to_validate = []
                element_to_validate.append(host_as_client)
                element_to_validate.append(host_as_server)
                element_to_validate.append(port)
                list_validation.append(element_to_validate)
    elif('xtreme' in json_data):
        print(' * TCP - Xtreme Mode')
        if(serversEnabled == True):
            try:
                print(' * Reiniciando el Servicio iperf3...')
                #os.system('echo %s|sudo -S %s' % ('Okm1234$', 'pkill -9 iperf3'))
                os.system('echo %s|sudo -S %s' % ('123', 'pkill -9 iperf3'))
                if machine_condition_checker() == True:
                    print(' * Error: L??mite de Memoria Alcanzado')
                    answer = {}
                    answer['Error'] = 'Memory Limit Reached'
                    tend = time.time()
                    totaltime = tend - tstart
                    print(' * Tiempo de Ejecuci??n: ',totaltime)
                    print(' * Proceso Finalizado...')
                    return answer    
            except:
                print(' * Error: ', sys.exc_info()[0])
                answer = {}
                answer['Error'] = 'Failed to Reload Iperf3'
                tend = time.time()
                totaltime = tend - tstart
                print(' * Tiempo de Ejecuci??n: ',totaltime)
                print(' * Proceso Finalizado...')
                
        try:
            print(' * Estableciendo el Servidor...')
            port = initial_port
            host_as_client = host_added[0];
            host_as_server = host_added[len(host_added)-1]
            port = initial_port
            host_as_server.cmd('iperf3 -s -p '+str(port)+' -J>'+str(host_as_server)+'_'+str(port)+'.json'+' &')
            time.sleep(0.5)
        except:
            print(' * Error: ', sys.exc_info()[0])
            answer = {}
            answer['Error'] = 'Failed to Create Server'
            tend = time.time()
            totaltime = tend - tstart
            print(' * Tiempo de Ejecuci??n: ',totaltime)
            print(' * Proceso Finalizado...')
            return answer

        name_files_server.append(str(host_as_server)+'_'+str(port))    
        aux = [host_as_server, port]
        aux_array.append(aux)
        # Variable que contiene las ejecuciones quedebe tomar Iperf3
        trafico = json_data['TCP'][0] # Un dicconario con las posibles opciones Iperf3
        # Se crea la orden estableciendo el host como Cliente enviando trafico al host Servidor en el puerto indicado
        orden = 'iperf3 -c '+str(host_as_server.IP())+' -p '+str(port)+' '
        # Se genera la orden con la lectura del diccionario del trafico
        for t in trafico:
            orden = orden+'-'+str(t)+' '+str(trafico[t])+' '
        #  Agregamos la condicion de que la respuesta la entregue en un archivo Json y que espera a terminar el proceso ya q no se envia a segundo plano
        orden = orden+'-J>'+str(host_as_client)+'_'+str(host_as_server)+'.json'
        #  Se Carga la orden al host Cliente
        print(' * Cargando Orden en el Cliente ...')
        host_as_client.cmd(orden)
        # Creaci??n de Validadores Futuros
        temp = str(host_as_client)+'_'+str(host_as_server)
        name_files.append(str(host_as_client)+'_'+str(host_as_server))
        element_to_validate = []
        element_to_validate.append(host_as_client)
        element_to_validate.append(host_as_server)
        element_to_validate.append(port)
        list_validation.append(element_to_validate)

    # -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-
    #  Esta secci??n  comprueba y carga la respuesta de Iperf3                                                                              *-
    # -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-

    time.sleep(1);
    contador_end = 0
    contador_receiver = 0
    count = 0;
    list_end = []
    list_receiver = []
    name_files_size = len(name_files)
    name_files_server_size = len(name_files_server)
    temporal_file_list = []
    traffic_incomplete = True

    print(' * Clientes: ',name_files_size,' Servidores: ',name_files_server_size)

    # Si la ejecucion no es correcta suele arrojar ningun archivo en respuesta, tanto en server como en client
    if (name_files_size != name_files_server_size) or (name_files_size == 0  and  name_files_server_size == 0) :
        print(' * Error: Ejecuci??n no Lograda')
        answer = {}
        answer['Error'] = 'Bad Execution'
        tend = time.time()
        totaltime = tend - tstart
        print(' * Tiempo de Ejecuci??n: ',totaltime)
        print(' * Proceso Finalizado...')
        return answer 
    
    # Comprueba los archivos del cliente en la salida hasta que se completen mientras se ejecuta el trafico
    print(" * Generando Tr??fico...")
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
                    except:
                        pass
            # Si el archivo no existe que reinicie el trafico, creandolo de nuevo en ese par Cliente-Servidor
            else:
                reset_traffic(element[0], element[1], element[2])

            if machine_condition_checker() == True:
                print(' * Error: L??mite de Memoria Alcanzado')
                answer = {}
                answer['Error'] = 'Memory Limit Reached'
                tend = time.time()
                totaltime = tend - tstart
                print(' * Tiempo de Ejecuci??n: ',totaltime)
                print(' * Proceso Finalizado...')
                return answer   
        
        
        # Si el numero de end es igual an de la clave de end['receiver_tcp_congestion'] el trafico fue exitoso
        if contador_receiver == name_files_size and contador_end == contador_receiver :
            print(' * End: ',contador_end,' Rec: ',contador_receiver) 
            traffic_incomplete = False
            break      
        elif (contador_end  == name_files_size and contador_receiver < contador_end) or (contador_end  == name_files_size and contador_receiver > contador_end) :
            print(' * Error: ', 'Imposible Crear el Tr??fico')
            print(' * End: ',contador_end,' Rec: ',contador_receiver)
            answer = {}
            answer['Error'] = 'Failed to Create Traffic'
            tend = time.time()
            totaltime = tend - tstart
            print(' * Tiempo de Ejecuci??n: ',totaltime)
            print(' * Proceso Finalizado...')
            #os.system('echo %s|sudo -S %s' % ('Okm1234$', 'rm -f *.json'))
            os.system('echo %s|sudo -S %s' % ('123', 'rm -f *.json'))
            return(answer)
            break
    
    #Comprobar que los archivos  generados en el servidor est??n completos para seguir con la ejecuci??n 
    print(' * Comprobando Archivos Generados...')
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
                    print(' * Non-Existent File: ',server_file)
                    pass
                
                if 'receiver_tcp_congestion' in json_temporal_file['end']:
                    if str(server_file) in temporal_file_list_server:
                        pass
                    else:
                        temporal_file_list_server.append(str(server_file))
                        conta += 1
                else:
                    pass
            if machine_condition_checker() == True:
                print(' * Error: L??mite de Memoria Alcanzado')
                answer = {}
                answer['Error'] = 'Memory Limit Reached'
                tend = time.time()
                totaltime = tend - tstart
                print(' * Tiempo de Ejecucion: ',totaltime)
                print(' * Proceso Finalizado...')
                return answer
    
    #Abre el archivo correspondiente al trafico de los clientes y lo pasa a Dict
    print(' * Leyendo Resultados de los Clientes...')
    for name in name_files:
        try: 
            archive_json = json.loads(open(str(name)+'.json').read())
            dict_data_traffic[str(name)] = archive_json
            #os.system('echo %s|sudo -S %s' % ('Okm1234$', 'rm -r '+str(name)+'.json'))
            os.system('echo %s|sudo -S %s' % ('123', 'rm -r '+str(name)+'.json'))
            if machine_condition_checker() == True:
                print(' * Error: L??mite de Memoria Alcanzado')
                answer = {}
                answer['Error'] = 'Memory Limit Reached'
                tend = time.time()
                totaltime = tend - tstart
                print(' * Tiempo de Ejecucion: ',totaltime)
                print(' * Proceso Finalizado...')
                return answer 
        except:
            print(' * File Error: ', str(name))
            answer = {}
            answer['Error'] = 'Failed to Read Client Traffic'
            tend = time.time()
            totaltime = tend - tstart
            print(' * Tiempo de Ejecucion: ',totaltime)
            print(' * Proceso Finalizado...')
            return(answer)
    
    #Abre el archivo correspondiente al trafico de los servidores y lo pasa a Dict
    print(' * Leyendo Resultados de los Servidores...')
    for name_server in name_files_server:
        try:
            archive_json_server = json.loads(open(str(name_server)+'.json').read())                    
            dict_data_traffic_server[str(name_server)] = archive_json_server
            #os.system('echo %s|sudo -S %s' % ('Okm1234$', 'rm -r '+str(name_server)+'.json'))
            os.system('echo %s|sudo -S %s' % ('123', 'rm -r '+str(name_server)+'.json'))
            if machine_condition_checker() == True:
                print(' * Error: L??mite de Memoria Alcanzado')
                answer = {}
                answer['Error'] = 'Memory Limit Reached'
                tend = time.time()
                totaltime = tend - tstart
                print(' * Tiempo de Ejecucion: ',totaltime)
                print(' * Proceso Finalizado...')
                return answer 
        except:
            print(' * File Error: ', str(name_server))
            answer = {}
            answer['Error'] = 'Failed to Read Server Traffic'
            tend = time.time()
            totaltime = tend - tstart
            print(' * Tiempo de Ejecucion: ',totaltime)
            print(' * Proceso Finalizado...')
            return(answer)

    #Diccionario que almacena la respueta para Django
    traffic = {}
    #Carga los archivos del cliente a un dict para la respuesta del servidor 
    print(' * Generando Salida de los Servidores...')
    try:
        for name_server in name_files_server:
            connected = dict_data_traffic_server[str(name_server)]['start']['connected'][0]

            #datos del host que actua como transmisor
            local_host = connected['local_host']
            local_port = connected['local_port']

            #datos del host que actua como servidor
            #remote_host = dict_data_traffic_server[str(name_server)]['start']['connecting_to']['host']
            #remote_port = dict_data_traffic_server[str(name_server)]['start']['connecting_to']['port']

            #datos de los par??metros del tr??fico en la red
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
            if machine_condition_checker() == True:
                print(' * Error: L??mite de Memoria Alcanzado')
                answer = {}
                answer['Error'] = 'Memory Limit Reached'
                tend = time.time()
                totaltime = tend - tstart
                print(' * Tiempo de Ejecucion: ',totaltime)
                print(' * Proceso Finalizado...')
                return answer 

        name_files_server = []
    except:
        print(' * Error: ',name_server,' - ', sys.exc_info()[0])
        answer = {}
        answer['Error'] = 'Failed to Generate Output Server Traffic'
        tend = time.time()
        totaltime = tend - tstart
        print(' * Tiempo de Ejecucion: ',totaltime)
        print(' * Proceso Finalizado...')
        return(answer)
    #Carga los archivos a un diccionario para la respuesta del servidor 
    print(' * Generando Salida de los Clientes...')
    try:
        for name in name_files:
            
            connected = dict_data_traffic[str(name)]['start']['connected'][0]
            #print('tipo: ', type(connected))

            #datos del host que actua como transmisor
            local_host = connected['local_host']
            local_port = connected['local_port']

            #datos del host que actua como servidor
            remote_host = dict_data_traffic[str(name)]['start']['connecting_to']['host']
            remote_port = dict_data_traffic[str(name)]['start']['connecting_to']['port']

            #datos de los par??metros del tr??fico en la red
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
                
            #Resultados del Tr??fico generado
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

            if machine_condition_checker() == True:
                print(' * Error: L??mite de Memoria Alcanzado')
                answer = {}
                answer['Error'] = 'Memory Limit Reached'
                tend = time.time()
                totaltime = tend - tstart
                print(' * Tiempo de Ejecucion: ',totaltime)
                print(' * Proceso Finalizado...')
                return answer 
    except:
        print(' * Error: ',name,' - ', sys.exc_info()[0])
        answer = {}
        answer['Error'] = 'Failed to Generate Output Client Traffic'
        tend = time.time()
        totaltime = tend - tstart
        print(' * Tiempo de Ejecucion: ',totaltime)
        print(' * Proceso Finalizado...')
        return(answer)
    
    name_files = []
    tend = time.time()
    totaltime = tend - tstart
    print(' * Tiempo de Ejecuci??n: ',totaltime)
    print(' * Proceso Finalizado...')
    return traffic

# Ejecuta el Trafico UDP en Iperf3 
def traffic_executor_udp():
    return 0

if __name__ == '__main__':
    #app.run(debug= False, host='10.55.6.188')
    app.run(debug= False, host='192.168.56.103')