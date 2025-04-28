#!/usr/bin/env python3
"""
Test script for validating the grid detection algorithm.
"""

import os
import sys
from PIL import Image
import json

from imageviewer.core.content_detection import ContentDetector
from imageviewer.core.grid_service import GridService
from imageviewer.core.image_handler import ImageHandler

def test_grid_detection(image_path):
    """Test grid detection on a given image
    
    Args:
        image_path: Path to the image file
    """
    print(f"Testing grid detection on: {os.path.basename(image_path)}")
    
    # Load the image
    try:
        image = Image.open(image_path)
        print(f"Image size: {image.size[0]}x{image.size[1]}")
    except Exception as e:
        print(f"Error loading image: {e}")
        return
    
    # Create detector and service instances
    detector = ContentDetector()
    grid_service = GridService()
    image_handler = ImageHandler()
    
    # Detect grid
    print("Running grid detection...")
    result = detector.detect_grid(image)
    
    # Print results
    if result['detected']:
        print("\nGRID DETECTED:")
        print(f"Raw grid size: {result['raw_grid_size_m']:.4f}m")
        print(f"Adjusted grid size: {result['grid_size_m']:.4f}m")
        print(f"Cells across 1.0m width: {result['cells_across']:.2f}")
        print(f"Confidence: {result['confidence']:.2%}")
        print(f"Vertical lines: {len(result['vertical_lines'])}")
        print(f"Horizontal lines: {len(result['horizontal_lines'])}")
        
        # Additional scores
        print("\nSCORE BREAKDOWN:")
        print(f"Consistency score: {result['consistency_score']:.2f}")
        print(f"Standard size score: {result['standard_size_score']:.2f}")
        print(f"Number of lines score: {result['num_lines_score']:.2f}")
        
        # Test how the GridService handles the detected size
        print("\nGRID SERVICE TEST:")
        original_size = result['grid_size_m']
        adjusted_size = grid_service.set_grid_size(original_size)
        print(f"Original detected size: {original_size:.4f}m")
        print(f"Grid service adjusted size: {adjusted_size:.4f}m")
        
        # Test if it's a standard grid size
        is_standard = grid_service.is_standard_grid_size(adjusted_size)
        print(f"Is standard grid size: {is_standard}")
        print(f"Cells per meter: {grid_service.get_cells_per_meter()}")
        
        # Test preferences for 10-cell grid
        if 9 <= result['cells_across'] <= 11:
            print("\nNOTE: Grid layout matches preferred 10-cell pattern (0.1m)!")
    else:
        print("\nNO GRID DETECTED")
        print(f"Reason: {result.get('reason', 'Unknown')}")
    
    print("\n" + "-" * 50 + "\n")
    
def batch_test_grid_detection(directory):
    """Test grid detection on all images in a directory
    
    Args:
        directory: Directory containing images
    """
    # Find all image files in the directory
    image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff')
    image_files = [
        os.path.join(directory, f) for f in os.listdir(directory)
        if f.lower().endswith(image_extensions) and os.path.isfile(os.path.join(directory, f))
    ]
    
    if not image_files:
        print(f"No image files found in {directory}")
        return
    
    print(f"Found {len(image_files)} image files for testing\n")
    
    # Test each image
    for image_path in image_files:
        test_grid_detection(image_path)
    
    print(f"Completed testing {len(image_files)} images")

if __name__ == "__main__":
    # Check for command line argument
    if len(sys.argv) > 1:
        path = sys.argv[1]
        if os.path.isfile(path):
            test_grid_detection(path)
        elif os.path.isdir(path):
            batch_test_grid_detection(path)
        else:
            print(f"Invalid path: {path}")
    else:
        print("Usage: python test_grid_detection.py <image_path_or_directory>")
        print("Example: python test_grid_detection.py test_images/")
        print("Example: python test_grid_detection.py test_images/grid_sample.png") 