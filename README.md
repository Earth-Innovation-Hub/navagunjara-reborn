# Navagunjara Reborn - Grid Layout Generator

Part of the [Earth Innovation Hub's Navagunjara Reborn project](https://earthinnovationhub.org/navagunjara_reborn).

## Overview

This tool processes grid images and creates standardized PDF layouts with exact 1-meter drawing width for architectural planning. It's specifically designed to support the Navagunjara Reborn sculpture installation.

## Features

- **Metric Precision**: Ensures all grid measurements maintain exact 1-meter width when printed
- **Statistical Validation**: Uses robust estimators to ensure consistent grid measurements
- **Visual Scale Indicators**: Clear L-shaped scale bars showing 10cm×10cm dimensions
- **Paper Conservation**: Optimized margins and layout to minimize paper usage
- **Visual Clarity**: High-contrast, readable fonts and measurements for field use

## Usage

1. Place PNG grid images in the same directory as the script
2. Run `python extract-grid-size.py`
3. PDF files will be generated in a 'PDFs' folder
4. Print at exactly 100% scale for accurate 1-meter grid width

## Technical Details

The script uses computer vision techniques to analyze grid patterns in images, calculating exact dimensions and scaling factors to maintain precise 1-meter width when printed on standard architectural paper rolls (42" or 44").

## License

[Apache 2.0 License](LICENSE)
