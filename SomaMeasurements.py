#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 18 20:50:53 2024

@author: debyelizarraras
"""


import tkinter as tk
from tkinter import filedialog
import os
import cv2
import numpy as np
from skimage.morphology import remove_small_objects, binary_erosion, binary_closing, binary_dilation
from skimage.measure import label, regionprops
import openpyxl



# Define a function to extract the cell soma

def extract_soma_and_measure(cell_image_path, output_soma_path, min_soma_area=50):
    # Open the processed individual cell image
    cell_image = cv2.imread(cell_image_path, cv2.IMREAD_GRAYSCALE)

    # Remove small objects (ramifications)
    cell_binary = remove_small_objects(cell_image.astype(bool), min_size=50).astype(np.uint8) * 255

    # Erosion to extract the soma
    kernel = np.ones((3, 3), np.uint8)
    soma = cv2.erode(cell_binary, kernel, iterations=1)

    # Label connected components in the soma
    labeled_soma = label(soma)

    # Get properties of labeled regions
    props = regionprops(labeled_soma)

    # Check if there are any labeled regions
    if props:
        # Find the index of the largest region
        largest_index = np.argmax([prop.area for prop in props])

        # Create a binary mask keeping only the largest region
        largest_soma = np.zeros_like(soma)
        largest_soma[labeled_soma == largest_index + 1] = 255

        # Save the extracted soma
        cv2.imwrite(output_soma_path, largest_soma)
        
        # Measure area and perimeter
        area = props[largest_index].area
        perimeter = props[largest_index].perimeter

        return os.path.splitext(os.path.basename(cell_image_path))[0], area, perimeter
    
    else:
        # Save the original soma (no extraction performed)
        cv2.imwrite(output_soma_path, soma)
        
        return os.path.splitext(os.path.basename(cell_image_path))[0], 0, 0


# Get the region and group from the user
region = input("Enter the region: ")
group = input("Enter the group: ")
 
# Create a Tkinter window for folder selection
root = tk.Tk()
root.withdraw()  # Hide the root window

  
# Ask the user to select the main folder containing subfolders
main_folder = filedialog.askdirectory(title="Select Main Folder")

if main_folder:
    
    # Create an output parent folder
    output_parent_folder = os.path.join(main_folder, f'Cell Soma {group} {region}')
    os.makedirs(output_parent_folder, exist_ok=True)
    
    # Create an Excel workbook and add a worksheet
    excel_path = os.path.join(main_folder, f'Soma_Measurements_{region}_{group}.xlsx')
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.append(["Cell ID", "Region","Group", "Area", "Perimeter"])
   

    # Iterate through each subfolder in the main folder
    for subfolder_name in os.listdir(main_folder):
        subfolder_path = os.path.join(main_folder, subfolder_name)

        # Check if the path is a directory
        if os.path.isdir(subfolder_path):
            # Create an output folder for each subfolder in the output parent folder
            output_folder_soma = os.path.join(output_parent_folder, f'{subfolder_name}_Soma')
            os.makedirs(output_folder_soma, exist_ok=True)

            # Iterate through each file in the subfolder
            for filename in os.listdir(subfolder_path):
                if filename.endswith('.png'):
                    cell_image_path = os.path.join(subfolder_path, filename)
                    output_soma_path = os.path.join(output_folder_soma, f'Soma_{filename}')

                    # Extract soma, measure area and perimeter
                    cell_id, area, perimeter = extract_soma_and_measure(cell_image_path,output_soma_path)

                # Write the measurements to the Excel worksheet
                    worksheet.append([cell_id, region, group, area, perimeter])
                    
     # Save the Excel workbook
        workbook.save(excel_path)

# Close the workbook to ensure the changes are written
        workbook.close()

        print(f"Soma measurements saved to {excel_path}")