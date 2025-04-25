#!/usr/bin/python3

#This file is used as command line to generate Rectangle or Cover photos list.

import sys
import os
import time

from files import get_images_folder
from batch import rectangle_batch, cover_batch

def main():
    # Check if the correct number of arguments are passed
    if len(sys.argv) != 4:
        print("Usage: vb <folder_source> <folder_output> <type: cov or rec> ")
        sys.exit(1)
    stime=time.time()
    print("Process beings...")
    # Get the folder paths from the arguments
    folder_source = sys.argv[1]
    folder_output = sys.argv[2]

    # Check if the folder_source exists
    if not os.path.exists(folder_source):
        print(f"Error: The source folder '{folder_source}' does not exist.")
        sys.exit(1)

    # Check if the folder_output exists, if not create it
    if not os.path.exists(folder_output):
        os.makedirs(folder_output)
        print(f"Output folder '{folder_output}' created.")
    print("Getting images from source path...")
    img=get_images_folder(folder_source)
    print("Exporting new photos as Rectangle with arrow and logo to output path...")
    if sys.argv[3]=="rec":
        rectangle_batch(img, 'Le360', folder_output)
    elif sys.argv[3]=="cov":
        cover_batch(img,'Le360',folder_output)
    else:
        print("Wrong type, choose cov or rec")
        sys.exit(1)
    print("Operation done.")
    etime=time.time()
    elapsed_time=etime-stime
    print(f"took {elapsed_time:.6f} seconds to execute.")
    
if __name__ == "__main__":
    main()