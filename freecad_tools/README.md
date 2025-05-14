# FreeCAD Architectural Truss Tools

This directory contains FreeCAD macros for generating various types of architectural trusses with FEM (Finite Element Method) analysis setup.

![image](https://github.com/user-attachments/assets/6c324304-ba5d-4fbe-8f60-14fab6d1b8c0)

## Macros Included

### 1. Pyramidal Truss (`pyramidal-truss.FCMacro`)
Creates a 3-sided pyramidal truss with:
- Triangular base with configurable side length
- Apex point with configurable height
- Two horizontal reinforcement levels at 1/3 and 2/3 of the height
- Diagonal bracing between reinforcement levels
- Circular beam cross-sections with configurable radius
- Complete FEM analysis setup with:
  - Steel material properties
  - Fixed constraints at the base
  - Downward force at the apex
  - Gmsh mesh generation

### 2. Rectangular Truss (`nava-freecad.FCMacro`)
Similar to the pyramidal truss but with different dimensions:
- Larger base side length (4.0 units instead of 1.0)
- Different height (3.0 units)
- Uses CalculiXCcxTools solver
- Uses Netgen meshing instead of Gmsh
- Includes instructions for running analysis automatically

### 3. Three Column Truss (`three_column_truss.FCMacro`)
A more complex three-column architectural truss design:
- Three parallel columns with configurable length, width, and height
- Segmented structure with configurable number of segments
- Comprehensive bracing:
  - Horizontal chord members on top and bottom
  - Vertical members
  - Diagonal web members
  - Cross-bracing between columns
- FEM analysis with:
  - Fixed constraints at six corner points
  - Different force loads on each column (middle column has higher load)
  - CalculiXCcxTools solver
  - Netgen meshing

## Usage

1. Open FreeCAD (version 1.0.0 or later)
2. Open the Macro menu (Macro → Macros...)
3. Click "Add" and browse to the .FCMacro file you want to use
4. Select the macro and click "Execute"

The macro will automatically:
- Create a new document
- Generate the truss structure
- Set up the FEM analysis
- Configure materials, constraints, and mesh
- Save the file (to /tmp by default)

## Compatibility Notes

- The macros include error handling for different FreeCAD versions
- If using Gmsh, ensure it's installed on your system
- Some FEM features may require manual configuration depending on your FreeCAD version
- Solver properties and mesh creation methods adapt to the available features

## Parameters

Each macro has configurable parameters at the top of the file:
- Dimensions (side length, height, width)
- Beam radius (thickness)
- For the three-column truss: number of segments, spacing, etc.

Modify these values to customize the truss to your specific requirements.

## Advanced Usage

The macros include commented code sections that can:
- Run the analysis automatically (uncomment the relevant sections)
- Generate and display results
- Create additional visualization objects

## Requirements

- FreeCAD 1.0.0+
- FEM workbench
- CalculiX (included with FreeCAD)
- Gmsh (for pyramidal truss) or Netgen (for rectangular and three-column trusses)
