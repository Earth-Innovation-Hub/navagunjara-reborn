#!/usr/bin/env python3
"""
Content detection module for the Image Viewer application.
Uses OpenCV for image processing and content bounding box detection.
"""

import math
import numpy as np
from typing import Tuple, Optional, Dict, List, Any
from PIL import Image

try:
    import cv2
except ImportError:
    cv2 = None
    print("OpenCV not installed. Some detection features may not work.")

# Type alias for bounding box (x_min, y_min, x_max, y_max)
BoundingBox = Tuple[float, float, float, float]

class ContentDetector:
    """Class for detecting content in images"""
    
    def __init__(self):
        """Initialize the detector"""
        # Content detection parameters
        self.min_contour_area_fraction = 0.01  # Min 1% of image area
        
        # Grid detection parameters
        self.canny_threshold1 = 50
        self.canny_threshold2 = 150
        self.hough_threshold = 50
        self.hough_min_line_length = 50
        self.hough_max_line_gap = 10
        self.angle_tolerance = 2  # Degrees
        self.spacing_tolerance = 0.2  # 20% variation allowed
        self.min_lines_for_grid = 4  # Minimum number of lines to consider as a grid
        
        # Standard grid sizes in meters (assuming 1.0m image width)
        self.standard_grid_sizes = [0.01, 0.02, 0.05, 0.1, 0.2, 0.25, 0.5]
        self.preferred_grid_size = 0.1  # Default 10-cell grid (1.0m / 10)
        
        # Scoring weights for different grid aspects
        self.consistency_weight = 0.4
        self.standard_size_weight = 0.4
        self.num_lines_weight = 0.2
    
    def detect_content(self, image: Image.Image) -> Optional[BoundingBox]:
        """Detect the main content in the image
        
        Args:
            image: PIL Image object
            
        Returns:
            Bounding box as (x_min, y_min, x_max, y_max) or None if no content detected
        """
        if cv2 is None:
            # If OpenCV is not available, fall back to the dummy implementation
            width, height = image.size
            margin_x = width * 0.1
            margin_y = height * 0.1
            return (margin_x, margin_y, width - margin_x, height - margin_y)
            
        try:
            # Convert PIL image to OpenCV format
            img_np = np.array(image)
            if len(img_np.shape) == 3 and img_np.shape[2] == 4:  # Has alpha channel
                # Convert RGBA to RGB
                img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGBA2RGB)
            elif len(img_np.shape) == 3:
                img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            else:
                img_cv = img_np  # Grayscale
            
            # Create a grayscale version for processing
            if len(img_cv.shape) == 3:
                gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            else:
                gray = img_cv
            
            # Apply threshold to create binary image
            _, binary = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Find contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return None
                
            # Filter out small contours (noise)
            img_area = gray.shape[0] * gray.shape[1]
            min_contour_area = img_area * self.min_contour_area_fraction
            significant_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_contour_area]
            
            if not significant_contours:
                return None
                
            # Find the bounding box that encompasses all significant content
            x_min, y_min = float('inf'), float('inf')
            x_max, y_max = 0, 0
            
            for contour in significant_contours:
                x, y, w, h = cv2.boundingRect(contour)
                x_min = min(x_min, x)
                y_min = min(y_min, y)
                x_max = max(x_max, x + w)
                y_max = max(y_max, y + h)
            
            return (x_min, y_min, x_max, y_max)
            
        except Exception as e:
            print(f"Error in content detection: {str(e)}")
            return None
    
    def detect_grid(self, image: Image.Image) -> Dict[str, Any]:
        """Detect grid patterns in the image
        
        Args:
            image: PIL Image object
            
        Returns:
            Dictionary with grid information:
            {
                'detected': bool, whether a grid was detected
                'grid_size_px': float, estimated grid size in pixels
                'grid_size_m': float, estimated grid size in meters (based on image being 1.0m wide)
                'confidence': float, confidence level (0-1)
                'vertical_lines': list of detected vertical line positions
                'horizontal_lines': list of detected horizontal line positions
            }
        """
        if cv2 is None:
            return {'detected': False, 'reason': 'OpenCV not available'}
            
        try:
            # Convert PIL image to OpenCV format
            img_np = np.array(image)
            if len(img_np.shape) == 3 and img_np.shape[2] == 4:  # Has alpha channel
                # Convert RGBA to RGB
                img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGBA2RGB)
            elif len(img_np.shape) == 3:
                img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            else:
                img_cv = img_np  # Grayscale
            
            # Create a grayscale version for processing
            if len(img_cv.shape) == 3:
                gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            else:
                gray = img_cv
            
            # Get image dimensions
            height, width = gray.shape
            
            # Apply preprocessing to enhance grid lines
            # 1. Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # 2. Apply adaptive thresholding to enhance grid lines
            binary = cv2.adaptiveThreshold(
                blurred, 
                255, 
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY_INV, 
                11, 
                2
            )
            
            # 3. Apply morphological operations to enhance grid lines
            kernel = np.ones((3, 3), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            # 4. Apply Canny edge detection
            edges = cv2.Canny(binary, self.canny_threshold1, self.canny_threshold2)
            
            # 5. Use probabilistic Hough Line Transform to detect lines
            lines = cv2.HoughLinesP(
                edges, 
                rho=1, 
                theta=np.pi/180,
                threshold=self.hough_threshold,
                minLineLength=self.hough_min_line_length,
                maxLineGap=self.hough_max_line_gap
            )
            
            if lines is None or len(lines) < self.min_lines_for_grid:
                return {'detected': False, 'reason': 'Not enough lines detected'}
            
            # Separate horizontal and vertical lines
            horizontal_lines = []
            vertical_lines = []
            
            for line in lines:
                x1, y1, x2, y2 = line[0]
                
                # Calculate line length
                line_length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                
                # Skip very short lines
                if line_length < self.hough_min_line_length:
                    continue
                
                # Calculate angle
                if x2 - x1 == 0:  # Vertical line
                    angle = 90
                else:
                    angle = abs(math.degrees(math.atan2(y2 - y1, x2 - x1)))
                
                # Classify as vertical or horizontal based on angle
                if angle < self.angle_tolerance or angle > (180 - self.angle_tolerance):
                    # Horizontal line
                    horizontal_lines.append((y1 + y2) / 2)  # Store y-position
                elif abs(angle - 90) < self.angle_tolerance:
                    # Vertical line
                    vertical_lines.append((x1 + x2) / 2)  # Store x-position
            
            # Sort lines by position
            horizontal_lines.sort()
            vertical_lines.sort()
            
            # Filter out duplicate lines (within tolerance)
            filtered_horizontal = self._filter_duplicate_lines(horizontal_lines)
            filtered_vertical = self._filter_duplicate_lines(vertical_lines)
            
            # If we don't have enough lines in both directions, not a grid
            if len(filtered_horizontal) < self.min_lines_for_grid or len(filtered_vertical) < self.min_lines_for_grid:
                return {'detected': False, 'reason': 'Not enough consistent lines for a grid'}
            
            # Calculate spacing between lines
            h_spacings = self._calculate_spacings(filtered_horizontal)
            v_spacings = self._calculate_spacings(filtered_vertical)
            
            # Group similar spacings to find the most common spacing
            h_groups = self._group_similar_values(h_spacings, tolerance=0.2)
            v_groups = self._group_similar_values(v_spacings, tolerance=0.2)
            
            # Find the most common spacing in each direction
            horizontal_spacing = self._most_common_value(h_groups)
            vertical_spacing = self._most_common_value(v_groups)
            
            # Use the minimum spacing as the grid size (since one direction might be subdivided)
            # But ensure we have at least 3 lines with this spacing to consider it valid
            grid_candidates = []
            
            if len(h_groups.get(horizontal_spacing, [])) >= 3:
                grid_candidates.append(horizontal_spacing)
                
            if len(v_groups.get(vertical_spacing, [])) >= 3:
                grid_candidates.append(vertical_spacing)
                
            if not grid_candidates:
                return {'detected': False, 'reason': 'No consistent grid spacing found'}
                
            grid_size_px = min(grid_candidates)
            
            # Calculate physical grid size (assuming image width is 1.0m)
            raw_grid_size_m = grid_size_px / width * 1.0
            
            # Find how many cells would fit across the 1.0m width
            cells_across = width / grid_size_px
            
            # Calculate confidence levels for different aspects
            h_consistency = self._calculate_consistency(filtered_horizontal, horizontal_spacing)
            v_consistency = self._calculate_consistency(filtered_vertical, vertical_spacing)
            
            # Calculate a consistency score (average of horizontal and vertical)
            consistency_score = (h_consistency + v_consistency) / 2
            
            # Calculate a score for standard grid size match
            # Prioritize standard grid sizes, especially the preferred 0.1m size (10 cells)
            standard_size_score = 0.0
            
            # Calculate how close raw_grid_size_m is to each standard grid size
            distance_to_preferred = abs(raw_grid_size_m - self.preferred_grid_size) / self.preferred_grid_size
            
            # High score if very close to preferred 0.1m grid size
            if distance_to_preferred < 0.1:  # Within 10% of preferred grid size
                standard_size_score = 1.0 - distance_to_preferred
            else:
                # Otherwise, find the closest standard grid size
                min_distance = float('inf')
                for std_size in self.standard_grid_sizes:
                    distance = abs(raw_grid_size_m - std_size) / std_size
                    if distance < min_distance:
                        min_distance = distance
                
                # Score based on proximity to any standard grid size
                standard_size_score = max(0, 1.0 - min_distance)
            
            # Calculate a score based on the number of lines detected 
            # More lines generally means more confident detection
            num_lines_score = min(1.0, (len(filtered_horizontal) + len(filtered_vertical)) / 30)
            
            # Calculate a weighted confidence score
            confidence = (
                self.consistency_weight * consistency_score +
                self.standard_size_weight * standard_size_score +
                self.num_lines_weight * num_lines_score
            )
            
            # Determine the final grid size based on constraints and confidence
            grid_size_m = None
            
            # STRONG ENFORCEMENT OF 10-CELL GRID (0.1m) WHEN APPROPRIATE
            # If the detected grid has approximately 10 (+/- 1) cells across, enforce the 0.1m grid size
            if 9 <= cells_across <= 11:
                grid_size_m = 0.1  # Enforce 10 cells per meter
                confidence = max(confidence, 0.9)  # High confidence for 10-cell grid
            # If close to 20 cells (double grid), prefer the 0.05m grid size
            elif 19 <= cells_across <= 21:
                grid_size_m = 0.05  # Enforce 20 cells per meter
                confidence = max(confidence, 0.85)  # Good confidence for 20-cell grid
            # If close to 5 cells, prefer the 0.2m grid size
            elif 4.5 <= cells_across <= 5.5:
                grid_size_m = 0.2  # Enforce 5 cells per meter
                confidence = max(confidence, 0.85)  # Good confidence for 5-cell grid
            else:
                # For other cases, select the closest standard grid size
                # but favor common grid sizes (0.1m, 0.05m, 0.2m) if they're close
                closest_std_size = min(self.standard_grid_sizes, key=lambda x: abs(x - raw_grid_size_m))
                
                # If we're reasonably close to a standard size, use it
                if abs(raw_grid_size_m - closest_std_size) / closest_std_size < 0.15:  # Within 15%
                    grid_size_m = closest_std_size
                else:
                    # If no standard size is a good match, use the raw calculation 
                    # but round to a reasonable precision
                    grid_size_m = round(raw_grid_size_m * 100) / 100  # Round to nearest 0.01m
            
            # Ensure final grid size is within valid range
            grid_size_m = max(0.01, min(0.5, grid_size_m))
            
            return {
                'detected': True,
                'grid_size_px': grid_size_px,
                'grid_size_m': grid_size_m,
                'raw_grid_size_m': raw_grid_size_m,
                'cells_across': cells_across,
                'confidence': confidence,
                'vertical_lines': filtered_vertical,
                'horizontal_lines': filtered_horizontal,
                'vertical_spacing': vertical_spacing,
                'horizontal_spacing': horizontal_spacing,
                'consistency_score': consistency_score,
                'standard_size_score': standard_size_score,
                'num_lines_score': num_lines_score
            }
            
        except Exception as e:
            print(f"Error in grid detection: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'detected': False, 'reason': f'Error: {str(e)}'}
    
    def _filter_duplicate_lines(self, lines, tolerance=10):
        """Filter out duplicate lines that are too close to each other
        
        Args:
            lines: List of line positions
            tolerance: Minimum distance between lines
            
        Returns:
            Filtered list of line positions
        """
        if not lines:
            return []
            
        filtered = [lines[0]]
        
        for line in lines[1:]:
            if line - filtered[-1] >= tolerance:
                filtered.append(line)
                
        return filtered
    
    def _calculate_spacings(self, lines):
        """Calculate spacing between consecutive lines
        
        Args:
            lines: List of line positions
            
        Returns:
            List of spacings between consecutive lines
        """
        return [lines[i+1] - lines[i] for i in range(len(lines)-1)]
    
    def _group_similar_values(self, values, tolerance=0.2):
        """Group similar values together
        
        Args:
            values: List of values to group
            tolerance: Tolerance for considering values similar (as a fraction)
            
        Returns:
            Dictionary mapping representative values to lists of similar values
        """
        if not values:
            return {}
            
        # Sort values
        sorted_values = sorted(values)
        
        # Group similar values
        groups = {}
        
        for value in sorted_values:
            # Find a group with a representative value close to the current value
            found_group = False
            
            for representative in groups:
                # Calculate relative difference
                relative_diff = abs(value - representative) / representative
                
                if relative_diff <= tolerance:
                    groups[representative].append(value)
                    found_group = True
                    break
                    
            # If no suitable group found, create a new one
            if not found_group:
                groups[value] = [value]
                
        return groups
    
    def _most_common_value(self, groups):
        """Find the most common value in the groups
        
        Args:
            groups: Dictionary mapping representative values to lists of similar values
            
        Returns:
            Most common representative value
        """
        if not groups:
            return None
            
        # Find the group with the most values
        most_common = max(groups.keys(), key=lambda k: len(groups[k]))
        
        return most_common
    
    def _calculate_consistency(self, lines, expected_spacing):
        """Calculate consistency of line spacing
        
        Args:
            lines: List of line positions
            expected_spacing: Expected spacing between lines
            
        Returns:
            Consistency score between 0 and 1
        """
        if len(lines) < 2:
            return 0
            
        # Calculate actual spacings
        spacings = [lines[i+1] - lines[i] for i in range(len(lines)-1)]
        
        # Calculate relative errors
        errors = [abs(spacing - expected_spacing) / expected_spacing for spacing in spacings]
        
        # Average error (capped at 1.0)
        avg_error = min(1.0, sum(errors) / len(errors))
        
        # Convert error to consistency score (1.0 - error)
        return 1.0 - avg_error 