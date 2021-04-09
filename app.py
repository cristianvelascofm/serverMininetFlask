from flask import Flask
from flask_cors import CORS
from flask import request



import socket
import sys
import os
import json
import subprocess
import time
import threading
from threading import Timer

from mininet.topo import Topo
from mininet.cli import CLI
from mininet.net import Mininet
from mininet.node import OVSSwitch, RemoteController
import mininet.link
import mininet.log
import mininet.node


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


host_added = []
switch_added = []
controller_added = []

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
def show():
    content = request.json
    print(content);
    print('Creando el Arreglo de la Red ...')
    # Contiene el diccionario de la clave Items
    array_data = json_data['items']

    ipClient = json_data['IpClient']
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
                        net.addLink(
                            m, j, intfName1=n['intfName1'], intfName2=n['intfName2'])

    print('Links Creados ...')
    net.start()
    print('RED INICIADA!! ...')

    at = {}
    at['red:'] = 'creada'
    return at
    



if __name__ == '__main__':
    app.run(debug= True, host='192.168.56.1')


