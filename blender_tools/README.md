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

## Features

- **Collection Hierarchy Visualization**: Displays the parent-child relationships between collections
- **Bounding Box Generation**: Creates wireframe boxes around each collection's objects
- **Orthographic Camera Setup**: Generates properly positioned and scaled cameras for standard views
- **Organized Output**: Places all generated objects in a clean collection hierarchy
- **Color Coding**: Assigns unique colors to each collection's bounding box

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

## Requirements
- Blender 2.80 or newer 