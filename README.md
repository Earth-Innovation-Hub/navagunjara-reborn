# Grid Vision: Architectural Grid Analysis & PDF Generator


This project demonstrates practical applications of computer vision in architectural and design workflows. It uses OpenCV and image processing techniques to analyze grid patterns in images and generate precise, scaled PDF outputs for professional printing.

## Learning Objectives

- Understand fundamental computer vision techniques for feature detection
- Learn how to extract geometric information from images
- Apply image processing techniques to real-world design problems
- Understand scale conversion between digital and physical dimensions
- Explore automation of technical drawing preparation

## How It Works: The Computer Vision Pipeline

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

5. **Visualization & Output Generation**
   - Creation of precisely scaled PDFs using Matplotlib
   - Addition of measurement references and scale bars
   - Metadata integration for documentation purposes

## Technical Concepts Explained

### Hough Line Transform
The code implements the probabilistic Hough Transform to detect lines in the binarized image. This algorithm works by:
1. Transforming points in image space to lines in Hough space
2. Finding peaks in the accumulator matrix to identify the most likely line parameters
3. Converting back to get line endpoints in the original image

### Morphological Operations
The script uses morphological closing to improve line detection:
```python
kernel = np.ones((5,5), np.uint8)
closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
```
This helps connect small gaps in the detected grid lines before applying edge detection.

### Statistical Validation
To ensure measurement accuracy, the code implements statistical validation:
```python
h_std = np.std(horizontal_spacings)
v_std = np.std(vertical_spacings)
h_mean = np.mean(horizontal_spacings)
v_mean = np.mean(vertical_spacings)
h_cv = h_std / h_mean if h_mean > 0 else 0
v_cv = v_std / v_mean if v_mean > 0 else 0
```
This identifies inconsistencies in grid spacing that could affect measurement precision.

## Usage

### Requirements
- Python 3.6+
- OpenCV (`opencv-python`)
- NumPy
- Matplotlib

Install dependencies:
```bash
pip install opencv-python numpy matplotlib
```

### Running the Tool
1. Place your grid PNG images in the same directory as the script
2. Run the script:
```bash
python extract-grid-size.py
```
3. PDFs will be generated in a subfolder named "PDFs"

### Expected Outputs
- Precisely scaled PDFs with 1-meter drawing width
- Versions for both 42-inch and 44-inch paper widths
- Scale bars and measurement references
- Metadata legend with file information and scale details

## Learning Extensions

### Educational Project Ideas
1. **Line Detection Visualization**: Modify the code to display intermediate steps of line detection
2. **Error Analysis**: Add code to visualize and analyze the accuracy of detected grid lines
3. **Algorithm Comparison**: Compare the results of different edge/line detection algorithms
4. **Performance Optimization**: Profile and optimize the image processing pipeline
5. **Feature Extension**: Add automatic detection of drawing elements within grid cells

