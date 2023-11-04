# leer PLACAS y crear una base de datos
# usando el servidor :http://docs.platerecognizer.com/
# Api : https://api.platerecognizer.com/v1/plate-reader

########### Dependencies ##############
from re import X
import PySimpleGUI as sg
import cv2
import numpy as np
import sys
from sys import exit as exit
from datetime import datetime
import requests
import pandas as pd
from tkinter import messagebox
import csv
import paho.mqtt.client as mqtt
import json

client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    print('Connected with result code '+str(rc))
    client.subscribe('testtopic/#')

client.on_connect = on_connect

client.connect("localhost", 1883, 60)

# Parametros
max_num_plate=10 # maximo numero de placas a almacenar en el fichero .csv

img = ('C:/Users/Blue/Documents/RoaPlacasVehiculares/temp.jpg')

#funcion para leer la placa
def leer_placa(img):
    regions = ['gb', 'it'] # estos parametros depende del tipo de placa a leer segun el pais
    # Se abre el archivo de datos .csv
    with open(img, 'rb') as fp:
        #se pide la consulta al servidor
        response = requests.post(
            'https://api.platerecognizer.com/v1/plate-reader/',
            data=dict(regions=regions),  # Opcional
            # se sube la foto al servidor
            # Se le envia el token a la APi de la web http://docs.platerecognizer.com/
            # Aqui tienes que colocar tu propio Token suscribiendote a la pagina
            files=dict(upload=fp),
            headers={'Authorization': 'Token ec0e382b2c69372354d6732eab5739356657ae69 '})
    return response.json() #retorna el json con los datos procesados

# funcion para validar y guardar la placa leida
def validar_placa(data, lista_placas,file,writer,max_num_plates, fechas):
    if data['results'] !=[]: #siempre que la imagen sea una placa
        #validar que no haya placas repetidas
        for result in data['results']:
            license_plate=result['plate']
        if len(lista_placas)>1: #para comenzar a verificar a partir de 1 placa
            if result['plate'] in lista_placas:
                validar=1 #filtra placas repetidas
            else:
                lista_placas.append(license_plate)
                validar=0 #asigna cero si no esta repetida
        else: # se agrega la primera placa
            lista_placas.append(license_plate)
            validar=0
        #verificar que haya menos de maximo numero de carros
        if len(lista_placas)>max_num_plates:
            validar=2
            lista_placas.pop() #elimina la ultima placa de la lista
        # se verifica si hay espacio en el parking o si esta repetida la placa antes de guardar
        guardar_placa(data, file, writer,validar)
        # Mensaje para saber que se leyo correctamente la placa
        messagebox.showinfo(message='PLACA leída "CORRECTAMENTE"')
        # Se lee la fecha y la hora
        date_=datetime.today().strftime('%x %X') #leer le fecha y hora
        fechas.append(date_.split(' '))
        #date,time_=date_[0], date_[1]

    else: # cuando la imagen no tenga una placa
        messagebox.showerror("ERROR", 'La imagen NO FUE RECONOCIDA')


#funcion para ir guardando en el archivo cada placa leida
def guardar_placa(data, file, writer,validar):
        for result in data['results']:
            if validar==0:
                writer.writerow(dict(date=datetime.today().strftime('%x %X'),
                         license_plate=result['plate'],
                         score=result['score'],
                         dscore=result['dscore'],
                         ))
                X = {"license_plate": result['plate'], "score": result['score'], "dscore": result['dscore']}
                payload=json.dumps(X)
                client.publish('placa', payload ,qos=0)
            if validar==1:
                messagebox.showerror("ERROR", 'PLACA REPETIDA')
            if validar==2:
                messagebox.showerror("ERROR", 'MAS de ' + str(max_num_plate)+ ' AUTOS')



def tablero(frame, lista_placas,fechas):
    pizarra = np.zeros((frame.shape[0],300,3),dtype=np.uint8)
    # titulo
    cv2.putText(pizarra, "PLACAS LEIDAS :", (10, 20), cv2.FONT_HERSHEY_COMPLEX, .6, (255,0,255), 1, cv2.LINE_AA)
    #imprimir placas en el tablero
    y=25
    for placa,fecha in zip(lista_placas,fechas):
        y+=16
        cv2.putText(pizarra, placa, (10, y), cv2.FONT_HERSHEY_COMPLEX, .5, (255,254,255), 1, cv2.LINE_AA)
        cv2.putText(pizarra, fecha[0], (90, y), cv2.FONT_HERSHEY_COMPLEX, .5, (255,254,255), 1, cv2.LINE_AA)
        cv2.putText(pizarra, fecha[1], (190, y), cv2.FONT_HERSHEY_COMPLEX, .5, (255,254,255), 1, cv2.LINE_AA)
    #unir pizarra con imagen
    combinado= np.hstack([frame,pizarra])
    return combinado

"""
software para lectura de placas
"""

sg.ChangeLookAndFeel('Black')
# define the window layout
layout = [[sg.Text('PLACA VEHICULAR', size=(40, 1), justification='center', font='Helvetica 20')],
          [sg.Image(filename='', key='image')],
          [sg.Button('LEER PLACA', size=(10, 1), font='Helvetica 14'),
          sg.Button('SALIR', size=(10, 1), font='Helvetica 14'),]]
# create the window and show it without the plot
window = sg.Window('SOFTWARE DE LECTURA DE PLACAS', layout,
                   location=(800,400))
######## ciclo para que la ventana se ejecute constantemente #######
file='save.csv' # nombre del archivo de datos previamente creado
# se bare el archivo para escritura
lista_placas=[]; fechas=[]
with open(file, 'w') as output:
    # se definen los campos del fichero
    fields = ['date', 'license_plate', 'score', 'dscore']
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    # se hace un ciclo para que la ventana se mantenga constantemente
    # ---===--- Event LOOP Read and display frames, operate the GUI --- #
    cap = cv2.VideoCapture(0)
    def rescale_frame(frame, percent=50):
        #649*480
        scale_percent = 50
        width = int(frame.shape[1] * scale_percent / 100)
        height = int(frame.shape[0] * scale_percent / 100)
        dim = (width, height)
        return cv2.resize(frame, dim, interpolation=cv2.INTER_AREA)

    recording = True
    while True:
        event, values = window.Read(timeout=20)
        if event == 'SALIR' or event is None:
            break
        elif event == 'LEER PLACA':
            foto="temp.jpg" # nombre de la imagen temporal a guardar
            # se guarda la imagen capturada por el video
            cv2.imwrite(foto,frame)
            # se llama a la funcion leer placa
            data=leer_placa(foto)
            validar_placa(data,lista_placas,file,writer,max_num_plate, fechas) #recibe la fecha y hora
            
        if recording:
            ret, frame = cap.read()
            cap.set(3, 100)
            cap.set(4, 50)
            frame = rescale_frame(frame, percent=10) 
            #Crear tablero de resultados
            frame_tablero=tablero(frame, lista_placas,fechas)
            imgbytes=cv2.imencode('.png', frame_tablero)[1].tobytes() #ditto
            window.FindElement('image').Update(data=imgbytes)
    window.close() #cerrar todo


exit()


