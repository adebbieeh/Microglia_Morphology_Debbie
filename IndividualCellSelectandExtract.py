#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 20 18:33:34 2023

@author: debyelizarraras
"""

import tkinter as tk
from tkinter import filedialog
import os
import cv2
from PIL import Image
import numpy as np
from skimage import measure
from skimage.morphology import remove_small_objects, binary_erosion, binary_dilation


# Create a Tkinter window
root = tk.Tk()
root.withdraw()  # Hide the root window

region = input('Enter region:')
group = input('Enter the experimental group:')

# Ask user to select the input folder
input_folder = filedialog.askdirectory(title="Select Input Folder")

if input_folder:
    
    # Create folders for saving results
    output_folder_selected_cells = f'Selected cells {group} {region}'
    output_folder_selected_cells_rectangles_numbers = f'Selected cells rectangles numbers {group} {region}'
    output_folder_individual_cells = f'Individual cells {group} {region}'
    output_folder_individual_cells_processed = f'Individual processed cells {group} {region}'
    
 
    os.makedirs(output_folder_selected_cells, exist_ok=True)
    os.makedirs(output_folder_selected_cells_rectangles_numbers, exist_ok=True)
    os.makedirs(output_folder_individual_cells, exist_ok=True)
    os.makedirs(output_folder_individual_cells_processed, exist_ok=True)

    
    # Loop through each file in the folder
    for filename in os.listdir(input_folder):
        if filename.endswith('.tif') or filename.endswith('.tiff'):
            image_path = os.path.join(input_folder, filename)

            # Open an image file
            image = Image.open(image_path)

            # Convert PIL Image to a NumPy array
            image_array = np.array(image)

            # Label connected regions in the thresholded image
            labels = measure.label(image_array)

            # Get properties of labeled regions
            props = measure.regionprops(labels)

            # Define a minimum area threshold for cells
            min_cell_area = 300  # Adjust this based on your image

            # Filter regions based on area
            filtered_regions = [region for region in props if region.area >= min_cell_area]

            # Save selected cells image
            selected_cells_path = os.path.join(output_folder_selected_cells, f'Selected_cells_{filename}')
            selected_cells = Image.new('L', image.size, 0)
            for region in filtered_regions:
                for coord in region.coords:
                    selected_cells.putpixel((coord[1], coord[0]), 255)
            selected_cells.save(selected_cells_path)

            # Draw rectangles and numbers on cells
            image_cv2 = cv2.imread(image_path)
            for idx, region in enumerate(filtered_regions):
                min_row, min_col, max_row, max_col = region.bbox
                cv2.rectangle(image_cv2, (min_col, min_row), (max_col, max_row), (0, 255, 0), 2)
                cv2.putText(image_cv2, str(idx + 1), (min_col, min_row), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            # Save image with rectangles and cell numbers
            output_image_path = os.path.join(output_folder_selected_cells_rectangles_numbers,
                                             f'Selected_cells_rectangles_numbers_{filename}')
            cv2.imwrite(output_image_path, image_cv2)

            # Save individual cell images
            output_directory = os.path.join(output_folder_individual_cells, f'Individual_Cells_{filename}')
            os.makedirs(output_directory, exist_ok=True)
            
            # Save individual processed cell images
            output_directory_processed_cells = os.path.join(output_folder_individual_cells_processed, f'Individual_Processed_Cells_{filename}') 
            os.makedirs(output_directory_processed_cells, exist_ok=True)
            
            for idx, region in enumerate(filtered_regions):
                cell_coords = region.coords
                min_row, min_col = np.min(cell_coords, axis=0)
                max_row, max_col = np.max(cell_coords, axis=0)
                cell_image = image.crop((min_col, min_row, max_col, max_row))
                cell_image.save(os.path.join(output_directory, f'{filename}_cell_{idx + 1}.png'))
                
              # Convert PIL Image to a NumPy array
                cell_array = np.array(cell_image)

              # Thresholding
                threshold_value = 100  # Adjust this threshold based on your image
                cell_binary = cv2.threshold(cell_array, threshold_value, 255, cv2.THRESH_BINARY)[1]

              # Remove small objects (noise)
                cell_binary = remove_small_objects(cell_binary.astype(bool), min_size=100).astype(np.uint8) * 255

              # Save processed individual cell image
                cell_image_processed = Image.fromarray(cell_binary)
                cell_image_processed.save(os.path.join(output_directory_processed_cells, f'{filename}_cell_{idx + 1}_processed.png'))
                

            
    