# BUSCAR PERSONAS POR PLACA
# AUTOR : Luis Alejandro Sanchez
# usando el servidor :http://docs.platerecognizer.com/
# Api : https://api.platerecognizer.com/v1/plate-reader

########### Dependencies ##############
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
import folium
from folium import plugins
import webbrowser

# Parametros
max_num_plate=10 # maximo numero de placas a almacenar en el fichero .csv

# funcion para mapear las camaras donde fue visto el automovil
def map(id_placa, file_cam, lista_placas):
    #leer fichero de datos
    bd_cam=pd.read_excel(file_cam)
    # filtrar las camaras donde se vio esa placa
    datos_plate=bd_cam[bd_cam['id']==int(id_placa)]
    #hacer una lista con coordenadas donde se vio lña placa
    coordenadas=[]
    #extraer coordenadas
    for x,y in zip(datos_plate['lat'],datos_plate['lon']):
        coordenadas.append([x,y])
    #Crear el mapa
    m = folium.Map(location=[datos_plate['lat'].mean(),datos_plate['lon'].mean()],
                    zoom_start=12, tiles ='Stamen Terrain')
    #Graficar sitios de camaras
    for c in coordenadas:
            folium.Marker(
                location=c,popup=lista_placas[-1],
                icon=folium.Icon(icon_color='white', icon='cam')
            ).add_to(m)
    #grabar en disco
    m.save('map_cam.html')
    webbrowser.open('map_cam.html')


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
            headers={'Authorization': 'Token 0d1c42c242234ca890fd1133106df25952fe1e28 '})
    return response.json() #retorna el json con los datos procesados


# funcion para validar y guardar la placa leida
def validar_placa(data, lista_placas,max_num_plates, fechas):
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
        #
        # Mensaje para saber que se leyo correctamente la placa
        messagebox.showinfo(message='PLACA leída "CORRECTAMENTE"')
        # Se lee la fecha y la hora
        date_=datetime.today().strftime('%x %X') #leer le fecha y hora
        fechas.append(date_.split(' '))
        #date,time_=date_[0], date_[1]

    else: # cuando la imagen no tenga una placa
        messagebox.showerror("ERROR", 'La imagen NO FUE RECONOCIDA')


def tablero(dic_plate, frame, lista_placas,fechas):
    pizarra = np.zeros((frame.shape[0],400,3),dtype=np.uint8)
    # titulo
    cv2.putText(pizarra, "DRIVER INFORMATION :", (30, 20), cv2.FONT_HERSHEY_COMPLEX, .7, (255,0,255), 1, cv2.LINE_AA)
    #imprimir placas en el tablero
    if len(lista_placas)>0:
        #incluir caras en la pantalla de salida
        pizarra, id_placa=face(dic_plate, pizarra,lista_placas,fechas)
    else:
        id_placa=0
    #unir pizarra con imagen
    combinado= np.hstack([frame,pizarra])
    return combinado, id_placa

# funcion para leer los rostros de la base de datos de imagenes
def face(dic_plate, pizarra,lista_placas,fechas):
    #buscar la placa en las imagenes con cada id que es el nombre del archivo jpg
    encontrada=0
    # ciclo para buscar la placa en la BD o diccionario
    for clave,valor in dic_plate.items():
        if valor[0]==lista_placas[-1]:
            id_placa=clave; encontrada=1
            break

    #leer el rostro
    face=cv2.imread(id_placa+'.jpg' if encontrada==1 else 'none'  +'.jpg' )
    face_resize=cv2.resize(face, (210,190))
    y_offset,x_offset=(50,30)
    #insertar la imagen en el tablero
    pizarra[y_offset:y_offset+face_resize.shape[0], x_offset:x_offset+face_resize.shape[1]] = face_resize
    # poneer textos
    if len(lista_placas)>0 and encontrada==1:
        x=255
        cv2.putText(pizarra, 'name: '+ dic_plate[id_placa][1], (x, 50), cv2.FONT_HERSHEY_COMPLEX, .5, (255,254,255), 1, cv2.LINE_AA)
        cv2.putText(pizarra, 'aged: '+ dic_plate[id_placa][2], (x, 75), cv2.FONT_HERSHEY_COMPLEX, .5, (255,254,255), 1, cv2.LINE_AA)
        cv2.putText(pizarra, 'plate: '+ lista_placas[-1], (x, 100), cv2.FONT_HERSHEY_COMPLEX, .5, (255,254,255), 1, cv2.LINE_AA)
    else:
        id_placa=0
    return pizarra, id_placa






"""
PROGRAMA para localizar automoviles por conductor y placa
"""
#nombre del archivo donde estan las placas y sus coordenadas (donde fueron vistas
file_cam='BD_face.xlsx'

sg.ChangeLookAndFeel('Black')
# define the window layout
layout = [[sg.Text('PLATE by Luis Sanchez', size=(40, 1), justification='center', font='Helvetica 20')],
          [sg.Image(filename='', key='image')],
          [sg.Button('Read plate', size=(10, 1), font='Helvetica 14'),
           sg.Button('Map', size=(10, 1), font='Any 14'),
          sg.Button('Exit', size=(10, 1), font='Helvetica 14'),]]
# create the window and show it without the plot
window = sg.Window('Demo Application - Read Plate v1.1', layout,
                   location=(800,400))


######## ciclo para que la ventana se ejecute constantemente #######
lista_placas=[]; fechas=[]
# aqui se asigna de manera aleatoria la placa con id entre 1-6, name, aged, porque solo tenemos 6 imagenes
dic_plate= {
     "1":['aaa123','Tom','32'],
     "2":['bp7f444','Clark','23'],
     "3":["rap44w",'Linda', '21'],
     "4":["cvy000",'Jess','31'],
     "5":["ak59104",'Mely','18'],
     "6":["6aon467",'Pen','25']}

cap = cv2.VideoCapture(0) #si la camara no te abre coloca 1 en lugar de 0
recording = True

while True:

    event, values = window.Read(timeout=20)

    if event == 'Exit' or event is None:
        break

    elif event == 'Read plate':
        foto="temp.jpg" # nombre de la imagen temporal a guardar
        # se guarda la imagen capturada por el video
        cv2.imwrite(foto,frame)
        # se llama a la funcion leer placa
        data=leer_placa(foto)
        validar_placa(data,lista_placas,max_num_plate, fechas) #recibe la fecha y hora

    elif event == 'Map':
        if id_placa!=0:
            map(id_placa, file_cam,lista_placas)
        else:
            messagebox.showerror("ERROR", 'No hay DATOS que MOSTRAR')


    if recording:
        ret, frame = cap.read()
        #Crear tablero de resultados y ubicar el rostro
        frame_tablero, id_placa=tablero(dic_plate, frame, lista_placas,fechas)
        imgbytes=cv2.imencode('.png', frame_tablero)[1].tobytes() #ditto
        window.FindElement('image').Update(data=imgbytes)

window.close() #cerrar todo


exit()


