#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 13 15:43:51 2024

@author: debyelizarraras
"""

import tkinter as tk
from tkinter import filedialog
import numpy as np
from skimage.morphology import skeletonize
import matplotlib.pyplot as plt
from PIL import Image
import os
import cv2
import openpyxl

def analyze_skeleton(cell_image_path, output_skeleton_path, output_segmented_path):
    # Open the image
    image = Image.open(cell_image_path)

    # Convert image to grayscale
    image_gray = image.convert('L')
    
    # Convert image to numpy array
    image_array = np.array(image_gray)
    
    # Threshold image to obtain binary image
    binary_image = image_array > 0
    
    # Skeletonize the binary image
    skeleton = skeletonize(binary_image)
    
    # Save the skeletonized image
    cv2.imwrite(output_skeleton_path, skeleton.astype(np.uint8) * 255)
    
    # Identify end points, junctions, and slabs
    end_points, junctions, slabs = identify_points(skeleton)
    
    # Perform segmentation
    segmented_image = segment_image(image_array, skeleton, end_points, junctions, slabs)
    
    # Save the segmented image
    cv2.imwrite(output_segmented_path, segmented_image.astype(np.uint8) * 255)

    # Count ramifications
    num_ramifications = count_ramifications(skeleton, end_points, junctions, slabs)

    return os.path.splitext(os.path.basename(cell_image_path))[0], skeleton, segmented_image, end_points, junctions, slabs, num_ramifications

def identify_points(skeleton):
    # Get coordinates of skeleton points
    skeleton_coords = np.transpose(np.nonzero(skeleton))
    
    # Create lists to store end points, junctions, and slabs
    end_points = []
    junctions = []
    slabs = []
    
    # Iterate through skeleton points
    for coord in skeleton_coords:
        # Get neighboring pixels
        neighbors = get_neighbors(coord, skeleton)
        
        # Count the number of neighbors
        num_neighbors = len(neighbors)
        
        # Classify the pixel based on the number of neighbors
        if num_neighbors == 1:
            end_points.append(coord)
        elif num_neighbors > 2:
            junctions.append(coord)
        else:
            slabs.append(coord)
    
    return end_points, junctions, slabs

def get_neighbors(coord, skeleton):
    # Define offsets for neighboring pixels
    offsets = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    
    # Get shape of the image
    height, width = skeleton.shape
    
    # List to store neighboring pixels
    neighbors = []
    
    # Iterate over offsets
    for dx, dy in offsets:
        x, y = coord[0] + dx, coord[1] + dy
        # Check if the neighbor is within the image bounds and is a skeleton pixel
        if 0 <= x < height and 0 <= y < width and skeleton[x, y]:
            neighbors.append((x, y))
    
    return neighbors

def count_ramifications(skeleton, end_points, junctions, slabs):
    # Initialize the count of ramifications
    num_ramifications = 0
    
    # Create a set of end points and junctions for efficient lookup
    end_points_set = set(map(tuple, end_points))
    junctions_set = set(map(tuple, junctions))
    
    # Iterate over end points and trace connections to junctions
    for end_point in end_points:
        visited = set()
        stack = [end_point]
        while stack:
            current = stack.pop()
            if tuple(current) in junctions_set:
                num_ramifications += 1
                break
            if tuple(current) in visited:
                continue
            visited.add(tuple(current))
            for neighbor in get_neighbors(current, skeleton):
                stack.append(neighbor)
                
    return num_ramifications

def has_path(skeleton, start, end):
    # Perform a simple depth-first search to check for a path between start and end points
    visited = set()
    stack = [start]
    
    while stack:
        current = stack.pop()
        if tuple(current) == tuple(end):  # Convert arrays to tuples before comparison
            return True
        if tuple(current) in visited:  # Convert arrays to tuples before comparison
            continue
        visited.add(tuple(current))  # Convert arrays to tuples before adding to set
        for neighbor in get_neighbors(current, skeleton):
            stack.append(neighbor)
    
    return False

def segment_image(image_array, skeleton, end_points, junctions, slabs):
    # Perform segmentation based on the skeleton and detected points
    segmented_image = np.zeros_like(image_array)
    
    # Mark skeleton points
    segmented_image[skeleton] = 255
    
    # Mark end points
    for point in end_points:
        segmented_image[point[0], point[1]] = 150  # Adjust intensity as needed
    
    # Mark junctions
    for point in junctions:
        segmented_image[point[0], point[1]] = 100  # Adjust intensity as needed
    
    # Mark slabs
    for point in slabs:
        segmented_image[point[0], point[1]] = 50  # Adjust intensity as needed
    
    return segmented_image

def save_visualization(cell_image_path, segmented_image, end_points, junctions, slabs, output_folder):
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Plot and save the visualization figure
    file_name = os.path.splitext(os.path.basename(cell_image_path))[0]
    plt.figure(figsize=(8, 8))
    plt.imshow(segmented_image, cmap='gray')
    plt.scatter([point[1] for point in end_points], [point[0] for point in end_points], c='b', label='End Points', s=10)
    plt.scatter([point[1] for point in junctions], [point[0] for point in junctions], c='purple', label='Junctions', s=10)
    plt.scatter([point[1] for point in slabs], [point[0] for point in slabs], c='orange', label='Slabs', s=10)
    plt.title('Skeleton Analysis')
    plt.legend()
    plt.savefig(os.path.join(output_folder, f'Visualization_{file_name}.png'))
    plt.close()

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
    output_parent_folder = os.path.join(main_folder, f'Analyze Skeleton {group} {region}')
    os.makedirs(output_parent_folder, exist_ok=True)
    
    # Create an Excel workbook and add a worksheet
    excel_path = os.path.join(main_folder, f'Analyze_Skeleton_{region}_{group}.xlsx')
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.append(["Cell ID", "Region", "Group", "# Branches", "# End Point Voxels", "# Junction Voxels", "# Slab Voxels"])
    
    # Iterate through each subfolder in the main folder
    for subfolder_name in os.listdir(main_folder):
        subfolder_path = os.path.join(main_folder, subfolder_name)

        # Check if the path is a directory
        if os.path.isdir(subfolder_path):
            # Create an output folder for each subfolder in the output parent folder
            output_folder_skeletonize = os.path.join(output_parent_folder, f'{subfolder_name}_Skeletonize')
            os.makedirs(output_folder_skeletonize, exist_ok=True)

            # Iterate through each file in the subfolder
            for filename in os.listdir(subfolder_path):
                if filename.endswith('.png'):
                    cell_image_path = os.path.join(subfolder_path, filename)
                    file_name = os.path.splitext(filename)[0]
                    output_skeleton_path = os.path.join(output_folder_skeletonize, f'Skeletonize_{file_name}.png')
                    output_segmented_path = os.path.join(output_folder_skeletonize, f'Segmented_{file_name}.png')

                    # Extract num_ramifications, end points, junctions, slab
                    cell_id, skeleton, segmented_image, end_points, junctions, slabs, num_ramifications = analyze_skeleton(cell_image_path, output_skeleton_path, output_segmented_path)

                    # Save the visualization figure
                    save_visualization(cell_image_path, segmented_image, end_points, junctions, slabs, output_folder_skeletonize)

                    # Write the measurements to the Excel worksheet
                    worksheet.append([cell_id, region, group, num_ramifications, len(end_points), len(junctions), len(slabs)])
                    
    # Save the Excel workbook
    workbook.save(excel_path)

    # Close the workbook to ensure the changes are written
    workbook.close()

    print(f"Skeleton Analysis saved to {excel_path}")
