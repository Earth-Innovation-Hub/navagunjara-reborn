# Image Viewer with Grid Measurement

A lightweight application for browsing through images in a folder with basic navigation, zoom functionality, and grid measurement support.

## Features

- Browse through all images in a folder
- Supports common image formats (PNG, JPG, JPEG, BMP, GIF, TIFF)
- Zoom in/out and pan around images
- Keyboard shortcuts for easy navigation
- Grid overlay for measurements
- Set image height for accurate scaling (width fixed at 1m)
- Adjustable grid size (default 10cm x 10cm)
- Simple and clean interface

## How to Use

1. **Installation**:
   ```
   pip install pillow numpy
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

## Keyboard Shortcuts

- **Left Arrow**: Previous image
- **Right Arrow**: Next image
- **+**: Zoom in
- **-**: Zoom out
- **r**: Reset zoom to 100%
- **g**: Toggle grid
- **h**: Set image height
- **s**: Adjust grid size

## Requirements

- Python 3.6+
- Pillow (PIL Fork)
- NumPy
- Tkinter (included with standard Python installation)

## License

This project is open source and available under the MIT License. 