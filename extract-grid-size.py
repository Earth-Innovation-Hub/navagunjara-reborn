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
    top_margin = 0.8  # Reduced even further from 1.5cm
    bottom_margin = 2.5  # Reduced from 4.5cm for more paper conservation
    
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
    
    # Store actual drawing coordinates for reference by other elements
    drawing_left = left_margin_norm
    drawing_right = left_margin_norm + width_norm
    drawing_bottom = bottom_margin_norm
    drawing_top = bottom_margin_norm + height_norm
    
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
    
    # Ensure we're using the actual grid cells for alignment, not arbitrary positions
    grid_unit_width_pixels = median_v_spacing  # Width of a 10cm grid cell in pixels
    grid_unit_height_pixels = median_h_spacing  # Height of a 10cm grid cell in pixels
    
    # Find the pixel coordinates of the grid corners for precise alignment
    grid_top_left_x = vertical_positions[0] if len(vertical_positions) > 0 else 0
    grid_top_left_y = horizontal_positions[0] if len(horizontal_positions) > 0 else 0
    grid_bottom_right_x = vertical_positions[-1] if len(vertical_positions) > 0 else img_rgb.shape[1]
    grid_bottom_right_y = horizontal_positions[-1] if len(horizontal_positions) > 0 else img_rgb.shape[0]
    
    # Draw checkered scale bars perfectly aligned with the grid itself, not arbitrary margins
    bar_thickness = min(grid_unit_width_pixels, grid_unit_height_pixels) * 0.15  # Slightly thicker
    
    # Place horizontal scale bar precisely at the top edge of the grid
    h_scale_bar_x = grid_top_left_x
    h_scale_bar_y = grid_top_left_y - bar_thickness * 1.5  # Position just above the grid
    
    # Place vertical scale bar precisely at the left edge of the grid
    v_scale_bar_x = grid_top_left_x - bar_thickness * 1.5  # Position just left of the grid
    v_scale_bar_y = grid_top_left_y
    
    # Draw checkered 1cm segments for horizontal scale bar (10 segments of 1cm each)
    segment_width = grid_unit_width_pixels / 10  # Each segment is 1cm
    
    for i in range(10):
        # Alternate colors for checkered pattern
        color = 'black' if i % 2 == 0 else 'white'
        edge_color = 'white' if i % 2 == 0 else 'black'
        
        # Create one segment at a time, aligned precisely with the grid top edge
        h_segment = Rectangle((h_scale_bar_x + i * segment_width, h_scale_bar_y), 
                             segment_width, bar_thickness,
                             linewidth=2, edgecolor=edge_color, facecolor=color, alpha=1.0)
        img_ax.add_patch(h_segment)
    
    # Draw checkered 1cm segments for vertical scale bar (10 segments of 1cm each)
    segment_height = grid_unit_height_pixels / 10  # Each segment is 1cm
    
    for i in range(10):
        # Alternate colors for checkered pattern
        color = 'black' if i % 2 == 0 else 'white'
        edge_color = 'white' if i % 2 == 0 else 'black'
        
        # Create one segment at a time, aligned precisely with the grid left edge
        v_segment = Rectangle((v_scale_bar_x, v_scale_bar_y + i * segment_height), 
                             bar_thickness, segment_height,
                             linewidth=2, edgecolor=edge_color, facecolor=color, alpha=1.0)
        img_ax.add_patch(v_segment)
    
    # Add scale bar labels with larger font size (doubled)
    img_ax.text(h_scale_bar_x + segment_width/2, 
               h_scale_bar_y + bar_thickness*3, 
               "10 cm", color='black', fontsize=24, fontweight='bold',
               ha='center', va='bottom', bbox=dict(facecolor='white', alpha=1.0, pad=4))
    
    img_ax.text(v_scale_bar_x - bar_thickness*3, 
               v_scale_bar_y - segment_height/2, 
               "10 cm", color='black', fontsize=24, fontweight='bold',
               ha='right', va='center', rotation=90,
               bbox=dict(facecolor='white', alpha=1.0, pad=4))
    
    # Add 1cm labels at the midpoint of the scale bars
    img_ax.text(h_scale_bar_x + segment_width/2, 
               h_scale_bar_y - bar_thickness*2, 
               "1 cm", color='black', fontsize=16, fontweight='bold',
               ha='center', va='top', bbox=dict(facecolor='white', alpha=1.0, pad=2))
    
    img_ax.text(v_scale_bar_x - bar_thickness*2, 
               v_scale_bar_y - segment_height/2, 
               "1 cm", color='black', fontsize=16, fontweight='bold',
               ha='right', va='center', rotation=90,
               bbox=dict(facecolor='white', alpha=1.0, pad=2))
    
    # Add indicator point at the actual grid corner
    img_ax.plot(grid_top_left_x, grid_top_left_y, 'o', color='red', markersize=12, zorder=10)
    
    # Get current date
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Move legend inside the grid drawing to conserve paper
    # Position in top-left corner of the grid drawing
    legend_width = drawing_width_cm * 0.25  # Slightly smaller to fit better
    legend_height = legend_width * 0.5
    
    # Convert grid corner pixel coordinates to normalized figure coordinates
    # We need to transform from pixel coordinates to axis coordinates to figure coordinates
    grid_corner_axis_x = grid_top_left_x / img_rgb.shape[1]
    grid_corner_axis_y = grid_top_left_y / img_rgb.shape[0]
    
    # Now convert from axis to figure coordinates
    grid_corner_fig_x = left_margin_norm + (grid_corner_axis_x * width_norm)
    grid_corner_fig_y = bottom_margin_norm + (grid_corner_axis_y * height_norm)
    
    # Position the legend exactly at the grid corner inside the drawing
    legend_left_norm = grid_corner_fig_x + 0.01  # Slight offset from corner for visibility
    legend_top_norm = grid_corner_fig_y - 0.01   # Slight offset from corner for visibility
    legend_width_norm = legend_width / total_width_cm
    legend_height_norm = legend_height / total_length_cm
    
    # Add improved legend - positioned inside the grid drawing
    legend_ax = fig.add_axes([legend_left_norm, legend_top_norm - legend_height_norm, legend_width_norm, legend_height_norm])
    legend_ax.set_xticks([])
    legend_ax.set_yticks([])
    legend_ax.set_facecolor('white')
    legend_ax.patch.set_alpha(0.85)  # Slightly more transparent so grid lines can be seen through it
    
    # Draw stronger border
    for spine in legend_ax.spines.values():
        spine.set_linewidth(1.5)  # Slightly thinner border
        spine.set_edgecolor('black')
    
    # Improved visual organization with better spacing
    num_sections = 7
    
    # Add header section with different background
    header_height = 1.0 / num_sections
    header_rect = Rectangle((0, 1.0 - header_height), 1, header_height,
                          facecolor='#f0f0f0', edgecolor='black', 
                          linewidth=1.0, alpha=1.0, zorder=0)
    legend_ax.add_patch(header_rect)
    
    # Add dividing lines with improved styling
    for i in range(1, num_sections):
        y_pos = 1.0 - (i / num_sections)
        legend_ax.axhline(y=y_pos, color='black', linewidth=0.8, alpha=0.7)
    
    # Add vertical dividing line to separate labels from values
    legend_ax.axvline(x=0.4, color='black', linewidth=0.8, alpha=0.5)
    
    # Add title with improved styling - smaller font to fit inside grid
    legend_ax.text(0.5, 0.93, "GRID LAYOUT METADATA", fontsize=16, weight='bold', 
                 ha='center', va='center', color='#000000')
    
    metadata = [
        ("File", os.path.basename(image_path)),
        ("Grid Size", f"{num_rows} × {num_cols} cells"),
        ("Cell Size", "10cm × 10cm"),
        ("Scale", scale_ratio),
        ("Drawing Width", "EXACTLY 1.0 meter"),
        (f"Paper Width", f"{paper_width_inches}-inch ({paper_width_cm:.1f}cm)"),
        ("Date", current_date)
    ]
    
    # Add metadata entries with improved styling and positioning - smaller fonts
    for i, (label, value) in enumerate(metadata):
        # Calculate position with better spacing
        y_pos = 0.93 - ((i + 1) * (0.93 / num_sections))
        
        # More contrast between label and value but smaller font
        legend_ax.text(0.03, y_pos, f"{label}:", fontsize=12, weight='bold', 
                     ha='left', va='center', color='#000000')
        
        legend_ax.text(0.43, y_pos, f"{value}", fontsize=12, 
                     ha='left', va='center', color='#000000')
    
    # Add small grid example in the bottom right corner of legend (optional in this compact version)
    grid_example_size = 0.08
    grid_example_x = 0.88
    grid_example_y = 0.07
    
    # Add a small visual grid example
    for i in range(3):
        # Horizontal lines
        legend_ax.axhline(y=grid_example_y + i*grid_example_size/2, 
                        xmin=1.0 - grid_example_size - 0.02, 
                        xmax=1.0 - 0.02, 
                        color='black', linewidth=0.8)
        # Vertical lines
        legend_ax.axvline(x=grid_example_x + i*grid_example_size/2, 
                        ymin=0.02, 
                        ymax=0.02 + grid_example_size, 
                        color='black', linewidth=0.8)
    
    # Move title block inside the grid at the bottom-right corner of the drawing
    title_block_width = drawing_width_cm * 0.15  # Smaller to fit inside grid
    title_block_height = title_block_width * 0.4
    
    # Find a position inside the grid, near bottom right
    # Calculate normalized coordinates for the position:
    # Find the bottom-right pixel coordinate of the grid
    grid_bottom_right_axis_x = grid_bottom_right_x / img_rgb.shape[1]
    grid_bottom_right_axis_y = grid_bottom_right_y / img_rgb.shape[0]
    
    # Convert to figure coordinates
    grid_bottom_right_fig_x = left_margin_norm + (grid_bottom_right_axis_x * width_norm)
    grid_bottom_right_fig_y = bottom_margin_norm + (grid_bottom_right_axis_y * height_norm)
    
    # Position inside the grid
    title_left_norm = grid_bottom_right_fig_x - (title_block_width / total_width_cm) - 0.01  # Offset from edge
    title_bottom_norm = grid_bottom_right_fig_y + 0.01  # Slight offset from bottom
    title_width_norm = title_block_width / total_width_cm
    title_height_norm = title_block_height / total_length_cm
    
    # Add title block inside the grid
    title_ax = fig.add_axes([title_left_norm, title_bottom_norm, title_width_norm, title_height_norm])
    title_ax.set_xticks([])
    title_ax.set_yticks([])
    title_ax.set_facecolor('white')
    title_ax.patch.set_alpha(0.85)  # Slightly transparent
    
    # Draw border
    for spine in title_ax.spines.values():
        spine.set_linewidth(1.5)
        spine.set_edgecolor('black')
    
    # Simplified, more readable layout
    title_ax.axhline(y=0.5, color='black', linewidth=1.0)
    title_ax.axvline(x=0.5, color='black', linewidth=1.0)
    
    # Add text with clearer organization - smaller font
    title_ax.text(0.5, 0.75, "GRID LAYOUT", fontsize=14, weight='bold', ha='center', va='center')
    title_ax.text(0.25, 0.25, "Scale:", fontsize=12, weight='bold', ha='center', va='center')
    title_ax.text(0.75, 0.25, scale_ratio, fontsize=12, ha='center', va='center')
    
    # Add scale bar - keep this outside the grid for better visibility and exact measurement
    scale_bar_height = 0.012  # Smaller height
    scale_bar_width = drawing_width_cm  # Exactly match drawing width
    
    # Position directly below the drawing, aligned with grid boundaries, much closer to conserve paper
    scale_bar_left_norm = drawing_left  # Align with left edge of grid
    scale_bar_bottom_norm = drawing_bottom - (scale_bar_height * 1.2 / total_length_cm)  # Position very close to grid
    scale_bar_width_norm = width_norm  # Match exactly with grid width
    scale_bar_height_norm = scale_bar_height / total_length_cm
    
    # Create scale bar axis aligned with drawing
    scale_bar_ax = fig.add_axes([scale_bar_left_norm, scale_bar_bottom_norm, scale_bar_width_norm, scale_bar_height_norm])
    scale_bar_ax.set_xlim(0, 1)
    scale_bar_ax.set_ylim(0, 1)
    
    # Create 10 segments for checkered scale bar
    for i in range(10):
        color = 'black' if i % 2 == 0 else 'white'
        segment_width = 0.1
        scale_bar_ax.axhline(y=0.5, xmin=i*segment_width, xmax=(i+1)*segment_width, 
                           color=color, linewidth=6)  # Thinner line
    
    # Add end caps
    scale_bar_ax.axvline(x=0, ymin=0.2, ymax=0.8, color='black', linewidth=1.5)  # Thinner line
    scale_bar_ax.axvline(x=1, ymin=0.2, ymax=0.8, color='black', linewidth=1.5)  # Thinner line
    
    # Add text closer to the scale bar for better integration - smaller font
    scale_bar_ax.text(0.5, 0.1, f"1 meter (EXACT SCALE) - {scale_ratio}", 
                    fontsize=14, fontweight='bold', ha='center', va='top')  # Smaller font
    
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
