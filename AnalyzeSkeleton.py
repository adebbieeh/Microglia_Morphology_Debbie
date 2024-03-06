#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 13 12:52:38 2024

@author: debyelizarraras
"""

import numpy as np
from skimage.morphology import skeletonize
import matplotlib.pyplot as plt
from PIL import Image


def analyze_skeleton(image):
    # Convert image to grayscale
    image_gray = image.convert('L')
    
    # Convert image to numpy array
    image_array = np.array(image_gray)
    
    # Threshold image to obtain binary image
    binary_image = image_array > 0
    
    # Skeletonize the binary image
    skeleton = skeletonize(binary_image)
    
    # Identify end points, junctions, and slabs
    end_points, junctions, slabs = identify_points(skeleton)

    # Count ramifications
    num_ramifications = count_ramifications(skeleton, end_points, junctions, slabs)

    return skeleton, end_points, junctions, slabs, num_ramifications

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

# Example usage:
# Assuming `cell_image` is your binary image of the cell

cell_image_path = '/Users/debyelizarraras/Desktop/Results Paper/CORTEZA/MOR/Individual processed cells MOR CI/Individual_Processed_Cells_MAX_R4_MOR_INS_CX_40X_B_1.czi - C=0.tif/MAX_R4_MOR_INS_CX_40X_B_1.czi - C=0.tif_cell_3_processed.png'
cell_image = Image.open(cell_image_path)
skeleton, end_points, junctions, slabs, num_ramifications = analyze_skeleton(cell_image)

print("Number of End Points:", len(end_points))
print("Number of Junctions:", len(junctions))
print("Number of Slabs:", len(slabs))
print("Number of Ramifications:", num_ramifications)

# Visualize the skeleton
plt.figure(figsize=(8, 8))
plt.imshow(skeleton, cmap='gray')
plt.scatter([point[1] for point in end_points], [point[0] for point in end_points], c='b', label='End Points', s=10)
plt.scatter([point[1] for point in junctions], [point[0] for point in junctions], c='purple', label='Junctions', s=10)
plt.scatter([point[1] for point in slabs], [point[0] for point in slabs], c='orange', label='Slabs', s=10)
plt.title('Skeleton Analysis')
plt.legend()
plt.show()
