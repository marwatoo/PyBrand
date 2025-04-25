#!/usr/bin/python3

#Created by marwa BIFISSE with the help of Chatgpt, the enemy of humanity

import os # this will allow me to manipulate dirs and files
import fnmatch # wildcard pattern unix-like matching
from PIL import Image #some function to manipulate images

#Function that returns full path of all images in a folder and sub folder

def get_images_path(folder_path):

    # Check if the folder exists and is readable
    if not os.path.exists(folder_path):
        return f"Error: The folder '{folder_path}' does not exist."
    
    if not os.path.isdir(folder_path):
        return f"Error: The path '{folder_path}' is not a directory."
    
    if not os.access(folder_path, os.R_OK):
        return f"Error: The folder '{folder_path}' is not accessible (no read permission)."

    extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp', '*.tiff', '*.webp','*.JPG', '*.JPEG', '*.PNG', '*.GIF', '*.BMP', '*.TIFF', '*.WEBP']
    images=[]

    for root, dirs, files in os.walk(folder_path):
        for ext in extensions:
            for file in fnmatch.filter(files, ext):
                images.append(os.path.join(root, file))
    return images

#function that return full path of all images, subfolders excludes
def get_images_folder(folder_path):
    # Check if the folder exists and is readable
    if not os.path.exists(folder_path):
        return f"Error: The folder '{folder_path}' does not exist."
    
    if not os.path.isdir(folder_path):
        return f"Error: The path '{folder_path}' is not a directory."
    
    if not os.access(folder_path, os.R_OK):
        return f"Error: The folder '{folder_path}' is not accessible (no read permission)."
    
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp', '*.tiff', '*.webp','*.JPG', '*.JPEG', '*.PNG', '*.GIF', '*.BMP', '*.TIFF', '*.WEBP']
    images = []

    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        if os.path.isfile(file_path):
            for ext in image_extensions:
                if fnmatch.fnmatch(file, ext):
                    images.append(file_path)
                    break
    return images

#Function that returns full path of excucted script
def get_dir():
    return os.path.dirname(os.path.abspath(__file__))