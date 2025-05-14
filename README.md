# Architectural Grid & Drawing Tools

This repository contains specialized tools for architectural drawing preparation, focusing on grid pattern analysis and PDF generation for large-format printing.

## Tools Included

### 1. Grid Vision: Architectural Grid Analysis

An image processing tool that automatically detects grid patterns in architectural renderings and generates precisely scaled PDFs with a fixed 1-meter width.

### 2. PDF Metadata Generator

A user-friendly GUI application that creates properly scaled and formatted PDFs for wide-format printing, with consistent 1-meter width and embedded metadata blocks.

### 3. FreeCAD Architectural Truss Tools

A collection of Python scripts for generating parametric 3D architectural trusses in FreeCAD with built-in FEM (Finite Element Method) analysis capabilities.

## Features

### Grid Vision Tool
- Automatic detection of grid cells using computer vision techniques
- Precise scaling to exactly 1-meter width for accurate printing
- Support for both 42-inch and 44-inch paper rolls
- Automatic PDF generation with proper scaling
- Statistical validation of measurements for accuracy

### PDF Metadata Generator
- User-friendly graphical interface for easy interaction
- Fixed 1.0m width for consistent scaling
- Automatic generation of PDFs for both 42-inch and 44-inch paper sizes
- Creation of metadata blocks in the top-left corner of PDFs
- Organization of output files in separate folders by paper size
- Image preview with zoom capabilities
- Batch processing support for multiple images

### FreeCAD Truss Tools
- Generation of various truss designs (pyramidal, rectangular, three-column, artistic)
- Parametric dimensions for easy customization
- Automatic FEM analysis setup for structural testing
- Compatible with FreeCAD 1.0.0 and later
- Built-in materials and constraints for engineering analysis
- Detailed documentation and examples

## How It Works

### Grid Vision: Computer Vision Pipeline

This tool implements a complete computer vision pipeline to analyze grid images:

1. **Image Acquisition & Preprocessing**
   - Loading images with `cv2.imread()`
   - Color space conversion with `cv2.cvtColor()`
   - Image binarization with `cv2.threshold()`
   - Noise reduction with morphological operations like `cv2.morphologyEx()`

2. **Feature Detection**
   - Edge detection using the Canny algorithm `cv2.Canny()`
   - Line detection with Hough Transform `cv2.HoughLinesP()`
   - Statistical validation to ensure measurement accuracy

3. **Geometric Analysis**
   - Identification of horizontal and vertical line segments
   - Classification and grouping of detected lines
   - Grid cell size calculation and validation
   - Statistical analysis of spacing consistency

4. **Metric Conversion & Scaling**
   - Conversion between pixel coordinates and physical dimensions
   - Precise scaling calculations to ensure 1:1 physical accuracy
   - Aspect ratio preservation and orientation optimization

### PDF Metadata Generator: Workflow

The PDF Metadata Generator provides a more interactive approach:

1. **Image Loading & Visualization**
   - Select individual images or entire directories
   - Preview with zoom and navigation controls
   - Automatic extraction of image dimensions

2. **Dimension & Metadata Specification**
   - Fixed 1.0m width for standard measurement
   - Input height in meters
   - Name specification for the object being rendered

3. **PDF Generation**
   - Automatic creation of PDFs for both 42-inch and 44-inch paper
   - Proper scaling to maintain aspect ratio
   - Centered positioning on the paper
   - Addition of metadata block in the top-left corner of the PDF

4. **Output Organization**
   - Separate directories for 42-inch and 44-inch paper sizes
   - Consistent naming conventions for easy reference
   - Generation of metadata text files with comprehensive information

## Requirements

- Python 3.6+
- OpenCV (`opencv-python`)
- NumPy
- Matplotlib
- Pillow (PIL)
- ReportLab (for PDF generation)
- Tkinter (for GUI application)

Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Grid Vision Tool

1. Place your grid PNG images in the same directory as the script
2. Run the script:
```bash
python extract-grid-size.py
```
3. PDFs will be generated in a subfolder named "PDFs"

### PDF Metadata Generator

1. Launch the GUI application:
```bash
python pdf_metadata_gui.py
```

2. Use the application:
   - Open an image or directory of images using the File menu
   - Navigate between images using Previous/Next buttons or arrow keys
   - Enter the height in meters (width is fixed at 1.0m)
   - Enter a name for the object (optional)
   - Click "Generate PDFs for both paper sizes"
   - Generated PDFs will be saved in "PDFs/42inch_prints" and "PDFs/44inch_prints"

### FreeCAD Truss Tools

1. Open FreeCAD (version 1.0.0 or later)
2. Navigate to the freecad_tools directory
3. Load one of the Python scripts using the macro functionality:
```bash
# Example for loading the pyramidal truss
python3 pyramidal-truss.py
```
4. The script will automatically generate the truss structure with proper analysis setup
5. See individual script comments for customization options

## Workflow Integration

These tools can be used separately or together in a workflow:

1. For images with clear grid patterns, use the **Grid Vision** tool for automatic analysis and PDF generation
2. For other orthographic renderings without grids, use the **PDF Metadata Generator** to manually specify dimensions and create properly scaled PDFs
3. Both tools ensure outputs are properly scaled with a consistent 1-meter width for professional printing

## Learning Extensions

### Educational Project Ideas
1. **Line Detection Visualization**: Modify the code to display intermediate steps of line detection
2. **Error Analysis**: Add code to visualize and analyze the accuracy of detected grid lines
3. **Algorithm Comparison**: Compare the results of different edge/line detection algorithms
4. **Performance Optimization**: Profile and optimize the image processing pipeline
5. **Feature Extension**: Add automatic detection of drawing elements within grid cells

