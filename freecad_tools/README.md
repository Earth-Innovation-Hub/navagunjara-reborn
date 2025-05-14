# FreeCAD Architectural Truss Tools

This directory contains Python scripts for generating various types of architectural trusses in FreeCAD with FEM (Finite Element Method) analysis setup.

## Scripts Included

### 1. Pyramidal Truss (`pyramidal-truss.py`)
Creates a 3-sided pyramidal truss with:
- Triangular base
- Apex point
- Horizontal reinforcement levels
- Diagonal bracing
- FEM analysis setup for structural testing

### 2. Rectangular Truss (`nava-freecad.py`)
Generates a rectangular truss structure with:
- Parallel trusses
- Cross-bracing
- FEM analysis setup

### 3. Three Column Truss (`three_column_truss.py`)
A three-column architectural truss design.

### 4. Artistic Truss (`artistic_truss.py`)
A more decorative truss design for artistic applications.

## Usage

1. Open FreeCAD (version 1.0.0 or later)
2. Load the script using the macro functionality
3. The script will automatically generate the truss structure with proper analysis setup

The generated structures can be exported in various formats (STEP, IGES, etc.) for use in other software, or directly used for FEM analysis within FreeCAD.

## Requirements

- FreeCAD 1.0.0+
- FEM workbench

## Parameters

Each script has configurable parameters at the top of the file:
- Dimensions (size, height, width)
- Material properties
- Beam thickness
- Analysis parameters

Modify these values to customize the truss to your needs. 