#!/usr/bin/python3

#Created by marwa BIFISSE with the help of Chatgpt, the enemy of humanity

from photos import batch_process_images
import os
from files import get_dir

#Function for 1080x1080
def square_batch(images, logo, output_folder, city, text, lang):

    logop=''
    if logo=="Le360":
        logop=os.path.join(get_dir(),'logo360/Le360.png')
    elif logo=='Sport':
        logop=os.path.join(get_dir(),'logo360/Le360Sport.png')
    elif logo=='Afrique':
        logop=os.path.join(get_dir(),'logo360/Le360Afrique.png')

    arrow=os.path.join(get_dir(),'logo360/arrow.png')

    batch_process_images(images, logop,output_folder,'bottom-left',1080,1080,'center',30,60,arrow,'bottom-right',None,'on',city,text, lang)

#Function for 1080x1350
def rectangle_batch(images, logo, output_folder):

    logop=''
    if logo=="Le360":
        logop=os.path.join(get_dir(),'logo360/Le360.png')
    elif logo=='Sport':
        logop=os.path.join(get_dir(),'logo360/Le360Sport.png')
    elif logo=='Afrique':
        logop=os.path.join(get_dir(),'logo360/Le360Afrique.png')

    arrow=os.path.join(get_dir(),'logo360/arrow.png')

    batch_process_images(images,logop,output_folder,'bottom-center',1080,1350,'center',30,60,arrow,'bottom-right')

#Function for 1920x1080
def cover_batch(images, logo, output_folder):
    logop=''
    if logo=="Le360":
        logop=os.path.join(get_dir(),'logo360/Le360.png')
    elif logo=='Sport':
        logop=os.path.join(get_dir(),'logo360/Le360Sport.png')
    elif logo=='Afrique':
        logop=os.path.join(get_dir(),'logo360/Le360Afrique.png')

    batch_process_images(images,logop,output_folder,'bottom-center',1920,1080,'center',30,40)