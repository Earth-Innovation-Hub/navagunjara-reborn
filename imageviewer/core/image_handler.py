#!/usr/bin/env python3
"""
Image handler module for the Image Viewer application.
Manages loading, processing, and navigation of images.
"""

import os
from typing import List, Optional
from PIL import Image, ImageTk

class ImageHandler:
    """Class for handling image loading and processing"""
    
    def __init__(self):
        """Initialize the image handler"""
        self.current_image_path = None
        self.current_pil_image = None
        self.current_display_image = None
        self.image_list = []
        self.current_index = -1
        
        # Image properties - FIXED WIDTH CONSTRAINT
        self.image_width_m = 1.0  # Fixed width in meters (IMMUTABLE)
        self.image_height_m = 1.0  # Default height in meters (will be calculated based on aspect ratio)
        
        # Zoom properties
        self.zoom_factor = 1.0
    
    def load_folder(self, directory: str) -> bool:
        """Load all images from a directory
        
        Args:
            directory: Path to directory containing images
            
        Returns:
            True if successful, False otherwise
        """
        if not os.path.isdir(directory):
            return False
            
        # Find all image files in the directory
        image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff')
        all_files = os.listdir(directory)
        self.image_list = [
            os.path.join(directory, f) for f in all_files 
            if f.lower().endswith(image_extensions) and os.path.isfile(os.path.join(directory, f))
        ]
        
        # Sort files alphabetically
        self.image_list.sort()
        
        # Reset current index
        if self.image_list:
            self.current_index = 0
            return self.load_current_image()
        else:
            self.current_index = -1
            return False
    
    def load_current_image(self) -> bool:
        """Load the current image
        
        Returns:
            True if successful, False otherwise
        """
        if not self.image_list or not (0 <= self.current_index < len(self.image_list)):
            return False
            
        self.current_image_path = self.image_list[self.current_index]
        
        try:
            # Load the image
            self.current_pil_image = Image.open(self.current_image_path)
            
            # Calculate image height based on aspect ratio (width is FIXED at 1.0m)
            self._calculate_image_height()
            
            # Reset zoom when loading a new image
            self.zoom_factor = 1.0
            
            return True
        except Exception as e:
            print(f"Error loading image: {str(e)}")
            return False
    
    def _calculate_image_height(self) -> None:
        """Calculate image height in meters based on aspect ratio with fixed 1.0m width"""
        if self.current_pil_image:
            width, height = self.current_pil_image.size
            aspect_ratio = height / width
            
            # Calculate height using the fixed 1.0m width and image aspect ratio
            raw_height_m = self.image_width_m * aspect_ratio
            
            # Round to the nearest 0.1m increment for better grid alignment
            self.image_height_m = round(raw_height_m * 10) / 10
            
            # Ensure minimum height for very thin images
            self.image_height_m = max(0.1, self.image_height_m)
    
    def set_image_height(self, height_m: float) -> None:
        """Set the physical height of the image in meters
        
        This is a manual override for the calculated height.
        The width remains fixed at 1.0m regardless of this setting.
        
        Args:
            height_m: Height in meters
        """
        # Validate minimum height
        height_m = max(0.1, height_m)
        
        # Round to the nearest 0.1m increment for better grid alignment
        self.image_height_m = round(height_m * 10) / 10
    
    def get_physical_size(self) -> tuple:
        """Get the physical size of the image in meters
        
        Returns:
            Tuple of (width_m, height_m)
        """
        return (self.image_width_m, self.image_height_m)
    
    def get_physical_aspect_ratio(self) -> float:
        """Get the physical aspect ratio (height/width) of the image
        
        Returns:
            Aspect ratio as height/width
        """
        if self.image_width_m == 0:
            return 1.0
        return self.image_height_m / self.image_width_m 