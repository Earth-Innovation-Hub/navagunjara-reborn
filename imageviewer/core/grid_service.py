#!/usr/bin/env python3
"""
Grid service module for the Image Viewer application.
Handles grid calculations and rendering.
"""

class GridService:
    """Class for handling grid calculations and rendering"""
    
    def __init__(self):
        """Initialize the grid service"""
        # Default grid size in meters (1m width / 10 cells)
        self.grid_size = 0.1
        self.show_grid = False
        
        # Standard grid divisions (in meters)
        self.standard_grid_sizes = [0.01, 0.02, 0.05, 0.1, 0.2, 0.25, 0.5]
        # Preferred size for common use case (10 cells across 1m width)
        self.preferred_grid_size = 0.1
    
    def toggle_grid(self) -> bool:
        """Toggle grid visibility
        
        Returns:
            New grid visibility state
        """
        self.show_grid = not self.show_grid
        return self.show_grid
    
    def set_grid_size(self, size_m: float) -> float:
        """Set grid size in meters
        
        Args:
            size_m: Grid size in meters
            
        Returns:
            New grid size in meters (adjusted to standard sizes)
        """
        # If the provided size is very close to our preferred size (10-cell grid),
        # enforce exact compliance with the standard
        if 0.095 <= size_m <= 0.105:
            self.grid_size = self.preferred_grid_size
            return self.grid_size
            
        # For other cases, find the closest standard grid size
        # Calculate relative distance to each standard size
        relative_distances = [(abs(size_m - std_size) / std_size, std_size) 
                             for std_size in self.standard_grid_sizes]
        
        # Sort by relative distance (closest first)
        relative_distances.sort()
        
        # If closest standard size is within 15% of requested size, use it
        closest_distance, closest_size = relative_distances[0]
        if closest_distance <= 0.15:
            size_m = closest_size
        else:
            # Otherwise round to reasonable precision (0.01m)
            size_m = round(size_m * 100) / 100
        
        # Validate grid size (between 0.01m and 0.5m)
        self.grid_size = max(0.01, min(0.5, size_m))
        return self.grid_size
    
    def reset_to_standard_grid(self) -> float:
        """Reset to the standard 10-cell grid (0.1m)
        
        Returns:
            Standard grid size (0.1m)
        """
        self.grid_size = self.preferred_grid_size
        return self.grid_size
    
    def get_cells_per_meter(self) -> int:
        """Get the number of cells per meter with current grid size
        
        Returns:
            Number of cells per meter
        """
        return int(round(1.0 / self.grid_size))
    
    def is_standard_grid_size(self, size_m: float) -> bool:
        """Check if a grid size matches one of the standard sizes
        
        Args:
            size_m: Grid size to check in meters
            
        Returns:
            True if it's a standard grid size, False otherwise
        """
        # Check with a small tolerance (1%)
        for std_size in self.standard_grid_sizes:
            if abs(size_m - std_size) / std_size < 0.01:
                return True
        return False 