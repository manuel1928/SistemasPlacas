# leer PLACAS y crear una base de datos
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

# Parametros
max_num_plate=10 # maximo numero de placas a almacenar en el fichero .csv

sg.ChangeLookAndFeel('Black')

# define the window layout
layout = [[sg.Text('placas veiculares', size=(40, 1), justification='center', font='Helvetica 20')],
          [sg.Image(filename='', key='image')],
          [sg.Button('Read plate', size=(10, 1), font='Helvetica 14'),
           sg.Button('Map', size=(10, 1), font='Any 14'),
          sg.Button('Exit', size=(10, 1), font='Helvetica 14'),]]
# create the window and show it without the plot
window = sg.Window('Demo Application - Read Plate v1.1', layout,
                   location=(800,400))
######## ciclo para que la ventana se ejecute constantemente #######

    
cap = cv2.VideoCapture('rtsp://192.168.230.9:8554/profile0')

def rescale_frame(frame, percent=50):
    scale_percent = 50
    width = int(frame.shape[1] * scale_percent / 100)
    height = int(frame.shape[0] * scale_percent / 100)
    dim = (width, height)
    return cv2.resize(frame, dim, interpolation=cv2.INTER_AREA)

recording = True
while True:
    event, values = window.Read(timeout=20)
    if event == 'Exit' or event is None:
        break
    elif event == 'Read plate':
        ret, frame = cap.read()
        cv2.imwrite('C:/Users/obed hipolito/Documents/RoaPlacasVehiculares/imagen.jpg', frame)
        break
    elif event == 'Map':
        break
    if recording:
        ret, frame = cap.read()  
        frame = rescale_frame(frame, percent=10)          
        imgbytes=cv2.imencode('.png', frame)[1].tobytes() #ditto
        window.FindElement('image').Update(data=imgbytes)
window.close() #cerrar todo


exit()


