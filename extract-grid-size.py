import cv2
import numpy as np
import os
import glob
import matplotlib
import datetime
# Use a non-interactive backend to avoid any display issues
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

def analyze_grid(image_path, paper_width_inches):
    """Process grid image and create PDF with exact 1m drawing width
    
    Args:
        image_path: Path to the input PNG image
        paper_width_inches: Width of the paper roll in inches (42 or 44)
    """
    print(f"\nAnalyzing {os.path.basename(image_path)} for {paper_width_inches}-inch paper...")
    
    # Convert paper width to cm
    paper_width_cm = paper_width_inches * 2.54
    
    # Load the image
    image = cv2.imread(image_path)
    
    if image is None:
        print(f"Error: Could not load image {image_path}")
        return None
    
    # Get a grayscale version for processing
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply threshold to binarize the image
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

    # Use morphology to close small gaps in lines
    kernel = np.ones((5,5), np.uint8)
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    # Detect edges
    edges = cv2.Canny(closed, 50, 150, apertureSize=3)

    # Use Hough Line Transform to detect lines
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=100, maxLineGap=10)

    horizontal_lines = []
    vertical_lines = []

    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if abs(y2 - y1) < 10:  # Horizontal line
                horizontal_lines.append((y1, y2))
            elif abs(x2 - x1) < 10:  # Vertical line
                vertical_lines.append((x1, x2))

    # Extract unique horizontal and vertical positions
    horizontal_positions = sorted(set([y for y1, y2 in horizontal_lines for y in (y1, y2)]))
    vertical_positions = sorted(set([x for x1, x2 in vertical_lines for x in (x1, x2)]))

    # Count rows and columns
    num_rows = len(horizontal_positions) - 1 if len(horizontal_positions) > 1 else 0
    num_cols = len(vertical_positions) - 1 if len(vertical_positions) > 1 else 0
    
    # Calculate width and length in meters (assuming each cell is 10cm x 10cm)
    width_meters = num_cols * 0.1
    length_meters = num_rows * 0.1
    
    # Set fixed drawing area to exactly 1m width
    drawing_width_m = 1.0  # Exactly 1.0 meter
    drawing_width_cm = drawing_width_m * 100  # 100 cm
    
    # Center the drawing
    left_margin = (paper_width_cm - drawing_width_cm) / 2  # Center the drawing
    right_margin = left_margin
    top_margin = 1.5  # Reduced from 2.5cm
    bottom_margin = 4.5  # Reduced from 7.5cm
    
    # Determine if rotation is needed (if width > height, rotate for best fit)
    need_rotation = width_meters > length_meters
    
    if need_rotation:
        # Swap dimensions after rotation
        orientation = "rotated"
        grid_dims = f"{num_rows}x{num_cols}_r"
        
        # Calculate dimensions after rotation (width becomes height and vice versa)
        pdf_width = drawing_width_m  # Fixed at 1m
        pdf_length = drawing_width_m * (width_meters / length_meters)  # Height based on aspect ratio
        scale_factor = drawing_width_m / width_meters
    else:
        # No rotation needed
        orientation = "normal"
        grid_dims = f"{num_rows}x{num_cols}"
        
        # Scale drawing to 1m width
        pdf_width = drawing_width_m  # Exactly 1m
        pdf_length = length_meters * (drawing_width_m / width_meters)
        scale_factor = drawing_width_m / width_meters
    
    # Calculate scale ratio for display
    scale_ratio = f"1:{int(1/scale_factor)}" if scale_factor < 1 else f"{int(scale_factor)}:1"
    if 0.95 < scale_factor < 1.05:
        scale_ratio = "1:1"
    
    # Format dimensions for filename
    width_str = f"{pdf_width:.1f}m"
    length_str = f"{pdf_length:.1f}m"
    
    # Generate PDF filename
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    pdf_filename = f"{base_name}_{paper_width_inches}in_w{width_str}xl{length_str}_{grid_dims}.pdf"
    pdf_path = os.path.join("PDFs", pdf_filename)

    # Print information
    print(f"Image: {os.path.basename(image_path)}")
    print(f"Grid Size: {num_rows} rows × {num_cols} columns")
    print(f"Original Dimensions: {width_meters:.1f}m × {length_meters:.1f}m")
    print(f"Drawing Width: Exactly 1.0m (centered on {paper_width_inches}\" paper)")
    print(f"Drawing Length: {pdf_length:.1f}m (scaled)")
    print(f"Scale Factor: {scale_factor:.3f} ({scale_ratio})")
    print(f"Rotation: {need_rotation}")
    print(f"Generating: {pdf_filename}")
    
    # Convert BGR to RGB
    img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # If rotation is needed for the printer, rotate the image
    if need_rotation:
        img_rgb = cv2.rotate(img_rgb, cv2.ROTATE_90_CLOCKWISE)
    
    # Calculate exact figure size
    total_width_cm = paper_width_cm
    total_length_cm = pdf_length * 100 + top_margin + bottom_margin
    
    # Convert to inches for matplotlib
    fig_width_inches = total_width_cm / 2.54
    fig_length_inches = total_length_cm / 2.54
    
    # Create figure with exact size (no auto-adjustments)
    fig = plt.figure(figsize=(fig_width_inches, fig_length_inches), constrained_layout=False)
    fig.patch.set_facecolor('white')
    
    # Calculate image position (centered)
    left_margin_norm = left_margin / total_width_cm
    bottom_margin_norm = bottom_margin / total_length_cm
    width_norm = drawing_width_cm / total_width_cm
    height_norm = (pdf_length * 100) / total_length_cm
    
    # Place image
    img_ax = fig.add_axes([left_margin_norm, bottom_margin_norm, width_norm, height_norm])
    img_ax.imshow(img_rgb)
    img_ax.set_xticks([])
    img_ax.set_yticks([])
    
    # Add border
    img_ax.spines['top'].set_linewidth(1.5)
    img_ax.spines['right'].set_linewidth(1.5)
    img_ax.spines['bottom'].set_linewidth(1.5)
    img_ax.spines['left'].set_linewidth(1.5)
    
    # More robust grid estimator with statistical validation to enforce metric correctness
    # First, calculate all grid line spacings to find the most consistent spacing
    horizontal_spacings = []
    for i in range(1, len(horizontal_positions)):
        spacing = horizontal_positions[i] - horizontal_positions[i-1]
        if spacing > 10:  # Filter out noise/too close lines
            horizontal_spacings.append(spacing)
    
    vertical_spacings = []
    for i in range(1, len(vertical_positions)):
        spacing = vertical_positions[i] - vertical_positions[i-1]
        if spacing > 10:  # Filter out noise/too close lines
            vertical_spacings.append(spacing)
    
    # Calculate median spacing to get the most reliable grid cell size
    if len(horizontal_spacings) > 0 and len(vertical_spacings) > 0:
        # Use median for robustness against outliers
        median_h_spacing = sorted(horizontal_spacings)[len(horizontal_spacings)//2]
        median_v_spacing = sorted(vertical_spacings)[len(vertical_spacings)//2]
        
        # Validate grid spacing consistency - print warnings if inconsistent
        h_std = np.std(horizontal_spacings)
        v_std = np.std(vertical_spacings)
        h_mean = np.mean(horizontal_spacings)
        v_mean = np.mean(vertical_spacings)
        
        h_cv = h_std / h_mean if h_mean > 0 else 0
        v_cv = v_std / v_mean if v_mean > 0 else 0
        
        if h_cv > 0.2 or v_cv > 0.2:  # Coefficient of variation > 20% indicates inconsistency
            print(f"WARNING: Grid spacing is inconsistent. CV: h={h_cv:.2f}, v={v_cv:.2f}")
            print(f"Horizontal spacings: min={min(horizontal_spacings):.1f}, max={max(horizontal_spacings):.1f}, median={median_h_spacing:.1f}")
            print(f"Vertical spacings: min={min(vertical_spacings):.1f}, max={max(vertical_spacings):.1f}, median={median_v_spacing:.1f}")
    else:
        # Fallback if spacing calculation fails
        print("WARNING: Could not calculate reliable grid spacing")
        median_h_spacing = img_rgb.shape[0] / max(1, num_rows)
        median_v_spacing = img_rgb.shape[1] / max(1, num_cols)
    
    # Find center region of grid for most reliable grid corner
    if need_rotation:
        # If image is rotated, adjust indices accordingly
        h_center_idx = len(horizontal_positions) // 3
        v_center_idx = len(vertical_positions) // 3
    else:
        # Use points closer to center for better reliability
        h_center_idx = len(horizontal_positions) // 3
        v_center_idx = len(vertical_positions) // 3
    
    # Ensure valid indices with sufficient margin from edges
    h_center_idx = max(1, min(h_center_idx, len(horizontal_positions) - 2))
    v_center_idx = max(1, min(v_center_idx, len(vertical_positions) - 2))
    
    # Get corner coordinates from the more reliable region
    if need_rotation:
        corner_y = horizontal_positions[h_center_idx]
        corner_x = vertical_positions[v_center_idx]
        
        # Use statistically validated spacing for scale bars
        scale_bar_pixel_width = median_v_spacing
        scale_bar_pixel_height = median_h_spacing
    else:
        corner_y = horizontal_positions[h_center_idx]
        corner_x = vertical_positions[v_center_idx]
        
        # Use statistically validated spacing for scale bars
        scale_bar_pixel_width = median_v_spacing
        scale_bar_pixel_height = median_h_spacing
    
    # Make scale bars more prominent
    bar_thickness = min(scale_bar_pixel_width, scale_bar_pixel_height) * 0.08
    
    # Draw more prominent L-shaped scale bar (horizontal part)
    horizontal_bar = Rectangle((corner_x, corner_y - bar_thickness/2), 
                              scale_bar_pixel_width, bar_thickness,
                              linewidth=2, edgecolor='black', facecolor='white', alpha=1.0)
    img_ax.add_patch(horizontal_bar)
    
    # Draw more prominent L-shaped scale bar (vertical part)
    vertical_bar = Rectangle((corner_x - bar_thickness/2, corner_y - scale_bar_pixel_height), 
                            bar_thickness, scale_bar_pixel_height,
                            linewidth=2, edgecolor='black', facecolor='white', alpha=1.0)
    img_ax.add_patch(vertical_bar)
    
    # Add scale bar labels with larger font size
    img_ax.text(corner_x + scale_bar_pixel_width/2, 
               corner_y + bar_thickness*3, 
               "10 cm", color='black', fontsize=12, fontweight='bold',
               ha='center', va='bottom', bbox=dict(facecolor='white', alpha=1.0, pad=3))
    
    img_ax.text(corner_x - bar_thickness*3, 
               corner_y - scale_bar_pixel_height/2, 
               "10 cm", color='black', fontsize=12, fontweight='bold',
               ha='right', va='center', rotation=90,
               bbox=dict(facecolor='white', alpha=1.0, pad=3))
    
    # Add indicator point at grid corner
    img_ax.plot(corner_x, corner_y, 'o', color='red', markersize=7, zorder=10)
    
    # Get current date
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Create more compact legend box in top-left corner
    legend_width = drawing_width_cm * 0.22  # Reduced from 0.3 (30%) to 0.22 (22%)
    legend_height = legend_width * 0.55  # Reduced proportionally
    legend_left = left_margin
    legend_top = total_length_cm - top_margin - legend_height
    
    # Convert to normalized coordinates
    legend_left_norm = legend_left / total_width_cm
    legend_top_norm = legend_top / total_length_cm
    legend_width_norm = legend_width / total_width_cm
    legend_height_norm = legend_height / total_length_cm
    
    # Add legend
    legend_ax = fig.add_axes([legend_left_norm, legend_top_norm, legend_width_norm, legend_height_norm])
    legend_ax.set_xticks([])
    legend_ax.set_yticks([])
    legend_ax.set_facecolor('white')
    legend_ax.patch.set_alpha(0.8)
    
    # Draw border
    for spine in legend_ax.spines.values():
        spine.set_linewidth(1.5)
        spine.set_edgecolor('black')
    
    # Add dividing lines
    num_sections = 7
    for i in range(1, num_sections):
        y_pos = i / num_sections
        legend_ax.axhline(y=y_pos, color='black', linewidth=0.75)
    
    # Add title and metadata with larger font size
    legend_ax.text(0.5, 0.93, "GRID LAYOUT METADATA", fontsize=11, weight='bold', ha='center', va='center')
    
    metadata = [
        ("File", os.path.basename(image_path)),
        ("Grid Size", f"{num_rows} × {num_cols} cells"),
        ("Cell Size", "10cm × 10cm"),
        ("Scale", scale_ratio),
        ("Drawing Width", "EXACTLY 1.0 meter"),
        (f"Paper Width", f"{paper_width_inches}-inch ({paper_width_cm:.1f}cm)"),
        ("Date", current_date)
    ]
    
    # Add metadata entries with larger font
    for i, (label, value) in enumerate(metadata):
        y_pos = 0.93 - ((i + 1) * (0.93 / num_sections))
        legend_ax.text(0.05, y_pos, f"{label}:", fontsize=9, weight='bold', ha='left', va='center')
        legend_ax.text(0.5, y_pos, f"{value}", fontsize=9, ha='left', va='center')
    
    # Create more compact title block in bottom right corner
    title_block_width = drawing_width_cm * 0.2  # Reduced from 0.25 to 0.2
    title_block_height = bottom_margin * 0.85  # Slightly reduced to save space
    title_left = total_width_cm - right_margin - title_block_width
    title_bottom = 0.1 * bottom_margin
    
    # Convert to normalized coordinates
    title_left_norm = title_left / total_width_cm
    title_bottom_norm = title_bottom / total_length_cm
    title_width_norm = title_block_width / total_width_cm
    title_height_norm = title_block_height / total_length_cm
    
    # Add title block
    title_ax = fig.add_axes([title_left_norm, title_bottom_norm, title_width_norm, title_height_norm])
    title_ax.set_xticks([])
    title_ax.set_yticks([])
    
    # Draw borders and dividing lines
    title_ax.spines['top'].set_linewidth(1.5)
    title_ax.spines['right'].set_linewidth(1.5)
    title_ax.spines['bottom'].set_linewidth(1.5)
    title_ax.spines['left'].set_linewidth(1.5)
    title_ax.axhline(y=0.7, color='black', linewidth=1.5)
    title_ax.axhline(y=0.4, color='black', linewidth=1.5)
    title_ax.axvline(x=0.5, color='black', linewidth=1.5)
    
    # Add text with larger font size
    title_ax.text(0.5, 0.85, "GRID LAYOUT", fontsize=12, weight='bold', ha='center', va='center')
    title_ax.text(0.25, 0.55, "Scale:", fontsize=10, ha='center', va='center')
    title_ax.text(0.75, 0.55, scale_ratio, fontsize=10, ha='center', va='center')
    title_ax.text(0.25, 0.25, "Date:", fontsize=10, ha='center', va='center')
    title_ax.text(0.75, 0.25, f"{current_date}", fontsize=10, ha='center', va='center')
    
    # Add scale bar (integrated with title block to save space)
    scale_bar_height = 0.01  # Slightly increased for visibility
    scale_bar_y = title_bottom_norm - scale_bar_height * 1.8  # Positioned closer to title block
    scale_bar_ax = fig.add_axes([left_margin_norm, scale_bar_y, width_norm, scale_bar_height])
    scale_bar_ax.set_xlim(0, 1)
    scale_bar_ax.set_ylim(0, 1)
    scale_bar_ax.axhline(y=0.5, xmin=0, xmax=1, color='black', linewidth=2)
    scale_bar_ax.axvline(x=0, ymin=0.25, ymax=0.75, color='black', linewidth=2)
    scale_bar_ax.axvline(x=1, ymin=0.25, ymax=0.75, color='black', linewidth=2)
    scale_bar_ax.text(0.5, 0, f"1 meter (EXACT SCALE) - {scale_ratio}", fontsize=10, ha='center', va='bottom')
    scale_bar_ax.set_xticks([])
    scale_bar_ax.set_yticks([])
    scale_bar_ax.spines['top'].set_visible(False)
    scale_bar_ax.spines['right'].set_visible(False)
    scale_bar_ax.spines['bottom'].set_visible(False)
    scale_bar_ax.spines['left'].set_visible(False)
    
    # PDF metadata
    pdf_metadata = {
        'Title': f"Grid {num_rows}x{num_cols} - {paper_width_inches}\" Paper - Exact 1m Width",
        'Subject': f"Architectural Grid | {paper_width_inches}\" Paper | Scale {scale_ratio}",
        'Keywords': f"grid,{orientation},{num_rows},{num_cols},{paper_width_inches}-inch,exact_1m_width",
        'Creator': "Grid Layout Generator",
        'Producer': "PDF Generator for Architectural Grid Layouts"
    }
    
    # Save PDF with exact dimensions
    plt.savefig(pdf_path, format='pdf', dpi=300, metadata=pdf_metadata)
    plt.close()
    
    print(f"PDF saved to: {pdf_path}")
    print(f"Drawing width is EXACTLY 1.0 meter when printed at 100% scale")
    
    return pdf_filename

def main():
    # Create output directory
    os.makedirs("PDFs", exist_ok=True)
    
    # Find PNG files
    png_files = glob.glob("*.png")

    if not png_files:
        print("No PNG files found in the current directory.")
        return
    
    print(f"Found {len(png_files)} PNG files. Processing...")
    
    # Paper sizes to generate (42-inch and 44-inch)
    paper_sizes = [42, 44]
    
    # Process all files for both paper sizes
    all_pdf_filenames = []
    
    for paper_size in paper_sizes:
        print(f"\nGenerating PDFs for {paper_size}-inch paper...")
        
        pdf_filenames = []
        for png_file in png_files:
            pdf_name = analyze_grid(png_file, paper_size)
            if pdf_name:
                pdf_filenames.append(pdf_name)
                all_pdf_filenames.append(pdf_name)
    
    # Print results
    print("\nGenerated PDF files (in 'PDFs' folder):")
    for filename in all_pdf_filenames:
        print(filename)
    
    print("\nProcessing complete!")
    print("\nIMPORTANT: When printing, ensure 'Scale' is set to exactly 100% for the 1-meter width to be accurate.")

if __name__ == "__main__":
    main()
