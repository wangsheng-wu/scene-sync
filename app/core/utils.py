"""
Utility functions for the photo matching application
"""

import os
import csv
from pathlib import Path
from typing import List, Dict, Tuple
from PIL import Image
import cv2
import numpy as np


# Supported image formats
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}


def get_image_files(directory: str) -> List[str]:
    """
    Get all image files from a directory
    
    Args:
        directory: Path to the directory
        
    Returns:
        List of image file paths
    """
    if not os.path.exists(directory):
        return []
    
    image_files = []
    for file in os.listdir(directory):
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path):
            ext = os.path.splitext(file)[1].lower()
            if ext in SUPPORTED_FORMATS:
                image_files.append(file_path)
    
    return sorted(image_files)


def validate_image_file(file_path: str) -> bool:
    """
    Validate if a file is a readable image
    
    Args:
        file_path: Path to the image file
        
    Returns:
        True if valid image, False otherwise
    """
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except Exception:
        return False


def load_image_for_matching(file_path: str) -> np.ndarray:
    """
    Load image for ORB matching
    
    Args:
        file_path: Path to the image file
        
    Returns:
        Grayscale image as numpy array
    """
    img = cv2.imread(file_path)
    if img is None:
        raise ValueError(f"Could not load image: {file_path}")
    
    # Convert to grayscale for feature detection
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return gray


def get_available_folders(base_directory: str) -> List[str]:
    """
    Get list of available folders in a directory
    
    Args:
        base_directory: Base directory to search
        
    Returns:
        List of folder names
    """
    if not os.path.exists(base_directory):
        return []
    
    folders = []
    for item in os.listdir(base_directory):
        item_path = os.path.join(base_directory, item)
        if os.path.isdir(item_path):
            # Check if folder contains any image files
            if get_image_files(item_path):
                folders.append(item)
    
    return sorted(folders)


def save_matching_results(results: List[Dict], output_file: str):
    """
    Save matching results to CSV file
    
    Args:
        results: List of matching results
        output_file: Path to output CSV file
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['film_photo', 'scene_photo', 'confidence_score']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for result in results:
            writer.writerow(result)


def get_file_name_from_path(file_path: str) -> str:
    """
    Extract file name from full path
    
    Args:
        file_path: Full path to file
        
    Returns:
        Just the file name
    """
    return os.path.basename(file_path)


def calculate_matching_score(matches: List) -> float:
    """
    Calculate confidence score based on number of good matches
    
    Args:
        matches: List of feature matches
        
    Returns:
        Confidence score between 0 and 1
    """
    if not matches:
        return 0.0
    
    # Count good matches (distance < threshold)
    good_matches = [m for m in matches if m.distance < 50]
    
    # Calculate score based on ratio of good matches
    score = len(good_matches) / len(matches)
    
    # Normalize to 0-1 range
    return min(score, 1.0) 