# Image Viewer with Grid Measurement and PDF Export

A lightweight application for browsing through images in a folder with basic navigation, zoom functionality, grid measurement support, and PDF export capabilities.

## Features

- Browse through all images in a folder
- Supports common image formats (PNG, JPG, JPEG, BMP, GIF, TIFF)
- Zoom in/out and pan around images
- Keyboard shortcuts for easy navigation
- Grid overlay for measurements with prominent 10cm scale bar
- High visibility grid with thicker lines and larger, bold labels
- Set image height for accurate scaling (width fixed at 1m)
- Adjustable grid size (default 10cm x 10cm)
- Export to PDF with 42" or 44" paper width
- Simple and clean interface

## How to Use

1. **Installation**:
   ```
   pip install pillow numpy reportlab
   ```

2. **Run the application**:
   ```
   python image_viewer.py
   ```

3. **Open a folder**:
   - Click the "Open Folder" button
   - Select a directory that contains images
   - The application will load all supported image files

4. **Navigation**:
   - Use the "Previous" and "Next" buttons to navigate between images
   - Or use the left and right arrow keys on your keyboard

5. **Zooming and Panning**:
   - Use the mouse wheel to zoom in and out
   - Use the "+" and "-" keys to zoom in and out
   - Click and drag to pan around when zoomed in
   - Press "r" to reset zoom to 100%

6. **Grid Measurement**:
   - Click "Set Height" to specify the real-world height of the image (width is fixed at 1m)
   - Click "Toggle Grid" or press "g" to show/hide the measurement grid
   - Click "Adjust Grid Size" or press "s" to change the grid spacing
   - Default grid size is 10cm x 10cm (0.1m)

7. **PDF Export**:
   - Click "Export 42\" PDF" or press "4" to export with 42-inch paper width
   - Click "Export 44\" PDF" or press "5" to export with 44-inch paper width
   - The PDF will be scaled properly to maintain the 1m width standard
   - Grid lines will be included in the PDF if the grid is enabled

## Keyboard Shortcuts

- **Left Arrow**: Previous image
- **Right Arrow**: Next image
- **+**: Zoom in
- **-**: Zoom out
- **r**: Reset zoom to 100%
- **g**: Toggle grid
- **h**: Set image height
- **s**: Adjust grid size
- **4**: Export to PDF (42" width)
- **5**: Export to PDF (44" width)

## Requirements

- Python 3.6+
- Pillow (PIL Fork)
- NumPy
- ReportLab
- Tkinter (included with standard Python installation)

## License

This project is open source and available under the MIT License. 