# Blender Collection Visualization Tools

A set of Blender Python scripts for visualizing and organizing collections in Blender scenes.

## Scripts Included

### 1. list_collections.py
Basic script that lists all collections in the current Blender scene and creates bounding boxes around each collection.

### 2. list_collections_detailed.py
Advanced script that:
- Lists all collections with detailed information
- Creates bounding boxes around each collection
- Adds orthographic cameras for X, Y, and Z axis views of each collection
- Organizes everything in a structured collection hierarchy

### 3. bbox_face_camera_generator.py
Script that creates orthographic cameras for each face of bounding boxes:
- Generates cameras perpendicular to each face of bounding boxes
- Creates a dedicated collection for the cameras
- Maintains proper camera framing for each bounding box face

### 4. add_orthographic_cameras.py
Creates standardized orthographic cameras for front, top, and side views:
- Sets up front (Y+), side (X+), and top (Z+) orthographic cameras for each bounding box
- Organizes cameras in a structured collection hierarchy
- Automatically adjusts orthographic scale based on bounding box dimensions

### 5. camera_animation.py
Creates an animated camera that moves between all cameras in the BBoxCameras collection:
- Creates a single animated camera that visits each bounding box camera position
- Sets up keyframes for smooth transitions between views
- Configures appropriate animation length based on the number of cameras

### 6. render_visualization_cameras.py
Comprehensive script for creating and rendering from visualization cameras:
- Combines functionality of list_collections_detailed.py
- Creates orthographic cameras for all collections (except those with 'base' in their name)
- Renders images from all cameras to a specified output directory
- Includes cleanup functionality to remove existing visualization objects

## Features

- **Collection Hierarchy Visualization**: Displays the parent-child relationships between collections
- **Bounding Box Generation**: Creates wireframe boxes around each collection's objects
- **Orthographic Camera Setup**: Generates properly positioned and scaled cameras for standard views
- **Organized Output**: Places all generated objects in a clean collection hierarchy
- **Color Coding**: Assigns unique colors to each collection's bounding box
- **Camera Animation**: Creates animated cameras for visualization and presentation
- **Automated Rendering**: Renders images from all visualization cameras
- **Flexible Customization**: Scripts can be used individually or combined based on specific needs

## Usage

1. Open Blender and your desired .blend file
2. Open the Script Editor workspace
3. Load one of the scripts
4. Run the script (Alt+P or press the "Run Script" button)

### list_collections.py
This script will:
- Print a hierarchical list of all collections in the scene
- Create red wireframe bounding boxes around each collection

### list_collections_detailed.py
This script will:
- Print detailed information about each collection
- Create color-coded bounding boxes around each collection
- Generate orthographic cameras for X, Y, and Z views
- Organize everything in a "Collection_Visualization" collection

### bbox_face_camera_generator.py
This script will:
- Create a camera for each face of every bounding box in the BoundingBoxes collection
- Store cameras in a "BBoxCameras" collection
- Position cameras perpendicular to each face with appropriate framing

### add_orthographic_cameras.py
This script will:
- Create standard orthographic cameras (front, top, side) for each bounding box
- Organize cameras in collections named after their bounding boxes
- Add all camera collections to an "OrthographicCameras" master collection

### camera_animation.py
This script will:
- Create an animated camera that moves between all cameras in the BBoxCameras collection
- Set up keyframes for smooth transitions between camera positions
- Configure the scene's end frame based on the number of cameras

### render_visualization_cameras.py
This script will:
- Create color-coded bounding boxes around each collection (except those with 'base' in name)
- Generate orthographic cameras for standard views of each collection
- Render images from all cameras to the specified output directory
- Optionally clean up existing visualization objects before processing

## Usage Example for render_visualization_cameras.py
```python
import bpy
import sys
import os

# Add the directory containing the script to the Python path
script_dir = "/path/to/blender_tools"
if script_dir not in sys.path:
    sys.path.append(script_dir)

# Import the module
from render_visualization_cameras import render_visualization_cameras

# Specify output directory (relative to .blend file or absolute path)
output_dir = "//renders/visualization_cameras/"  # relative path starts with //

# Run the function (True to clear existing visualization objects)
render_visualization_cameras(output_dir, clear_existing=True)
```

## Requirements
- Blender 2.80 or newer 