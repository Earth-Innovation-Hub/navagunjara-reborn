#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import numpy as np
import os
import re
from datetime import datetime
import reportlab
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch, cm
from reportlab.lib.pagesizes import landscape

# Common image file extensions
IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif']

class PDFMetadataApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Metadata Generator for Wide Format Paper")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Set application icon if available
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass
        
        # State variables
        self.current_image_path = None
        self.image_files = []
        self.current_index = -1
        self.base_output_dir = "PDFs"
        self.cv2_image = None
        self.display_image = None
        self.original_pil_image = None
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        
        # Fixed width in meters (1.0m)
        self.width_m = 1.0
        
        # Paper sizes
        self.paper_sizes = {
            "42-inch": {
                "width_inches": 42,
                "folder": "42inch_prints"
            },
            "44-inch": {
                "width_inches": 44,
                "folder": "44inch_prints"
            }
        }
        
        # Create output directories if they don't exist
        self.create_output_directories()
        
        # Create UI elements
        self.create_menu()
        self.create_layout()
        
        # Bind keyboard shortcuts
        self.root.bind('<Left>', lambda e: self.previous_image())
        self.root.bind('<Right>', lambda e: self.next_image())
        self.root.bind('<plus>', lambda e: self.zoom_in())
        self.root.bind('<equal>', lambda e: self.zoom_in())  # For keyboards where + is shift+= 
        self.root.bind('<minus>', lambda e: self.zoom_out())
        self.root.bind('<0>', lambda e: self.reset_zoom())
    
    def get_output_dir_for_paper_size(self, paper_size_key):
        """Get the output directory for a specific paper size"""
        return os.path.join(self.base_output_dir, self.paper_sizes[paper_size_key]["folder"])
    
    def create_output_directories(self):
        """Create all necessary output directories"""
        if not os.path.exists(self.base_output_dir):
            os.makedirs(self.base_output_dir)
            
        for size_info in self.paper_sizes.values():
            folder_path = os.path.join(self.base_output_dir, size_info["folder"])
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
        
    def create_menu(self):
        # Create menu bar
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open Image", command=self.open_image, accelerator="Ctrl+O")
        file_menu.add_command(label="Open Directory", command=self.open_directory, accelerator="Ctrl+D")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit, accelerator="Alt+F4")
        menubar.add_cascade(label="File", menu=file_menu)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Zoom In", command=self.zoom_in, accelerator="+")
        view_menu.add_command(label="Zoom Out", command=self.zoom_out, accelerator="-")
        view_menu.add_command(label="Reset Zoom", command=self.reset_zoom, accelerator="0")
        menubar.add_cascade(label="View", menu=view_menu)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Process Current Image", command=self.process_current_image, accelerator="Ctrl+P")
        tools_menu.add_command(label="Set Base Output Directory", command=self.set_output_directory)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Instructions", command=self.show_instructions)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        # Attach menu to the window
        self.root.config(menu=menubar)
        
        # Add keyboard bindings for menu items
        self.root.bind('<Control-o>', lambda e: self.open_image())
        self.root.bind('<Control-d>', lambda e: self.open_directory())
        self.root.bind('<Control-p>', lambda e: self.process_current_image())
    
    def create_layout(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top section - Image display and navigation
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Image frame with border
        self.image_frame = ttk.LabelFrame(top_frame, text="Image Preview")
        self.image_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Canvas for image display with dark background for better contrast
        self.canvas = tk.Canvas(self.image_frame, bg="#333333")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Add mouse wheel binding for zoom
        self.canvas.bind("<MouseWheel>", self.mouse_wheel)  # Windows
        self.canvas.bind("<Button-4>", self.mouse_wheel)    # Linux scroll up
        self.canvas.bind("<Button-5>", self.mouse_wheel)    # Linux scroll down
        
        # Navigation and zoom control frame
        nav_frame = ttk.Frame(main_frame)
        nav_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Navigation buttons
        self.prev_btn = ttk.Button(nav_frame, text="Previous", command=self.previous_image)
        self.prev_btn.pack(side=tk.LEFT, padx=5)
        
        self.image_counter = ttk.Label(nav_frame, text="No images loaded")
        self.image_counter.pack(side=tk.LEFT, padx=20)
        
        self.next_btn = ttk.Button(nav_frame, text="Next", command=self.next_image)
        self.next_btn.pack(side=tk.LEFT, padx=5)
        
        # Zoom controls
        zoom_frame = ttk.Frame(nav_frame)
        zoom_frame.pack(side=tk.RIGHT, padx=5)
        
        zoom_out_btn = ttk.Button(zoom_frame, text="-", width=2, command=self.zoom_out)
        zoom_out_btn.pack(side=tk.LEFT, padx=2)
        
        self.zoom_label = ttk.Label(zoom_frame, text="100%", width=6)
        self.zoom_label.pack(side=tk.LEFT, padx=2)
        
        zoom_in_btn = ttk.Button(zoom_frame, text="+", width=2, command=self.zoom_in)
        zoom_in_btn.pack(side=tk.LEFT, padx=2)
        
        reset_zoom_btn = ttk.Button(zoom_frame, text="Reset", command=self.reset_zoom)
        reset_zoom_btn.pack(side=tk.LEFT, padx=5)
        
        # Bottom section - Input fields and metadata preview
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.BOTH, padx=5, pady=5)
        
        # Left side - Input fields
        input_frame = ttk.LabelFrame(bottom_frame, text="Measurement Input")
        input_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Fixed width indicator
        width_frame = ttk.Frame(input_frame)
        width_frame.pack(fill=tk.X, padx=10, pady=5)
        
        width_label = ttk.Label(width_frame, text="Width (fixed):")
        width_label.pack(side=tk.LEFT, padx=5)
        
        width_value_label = ttk.Label(width_frame, text=f"{self.width_m:.2f} meters (1.0m)")
        width_value_label.pack(side=tk.LEFT, padx=5)
        
        # Height input
        height_frame = ttk.Frame(input_frame)
        height_frame.pack(fill=tk.X, padx=10, pady=5)
        
        height_label = ttk.Label(height_frame, text="Height (meters):")
        height_label.pack(side=tk.LEFT, padx=5)
        
        self.height_var = tk.StringVar()
        self.height_entry = ttk.Entry(height_frame, textvariable=self.height_var, width=10)
        self.height_entry.pack(side=tk.LEFT, padx=5)
        
        # Name input
        name_frame = ttk.Frame(input_frame)
        name_frame.pack(fill=tk.X, padx=10, pady=5)
        
        name_label = ttk.Label(name_frame, text="Object Name:")
        name_label.pack(side=tk.LEFT, padx=5)
        
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(name_frame, textvariable=self.name_var, width=30)
        self.name_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Process button
        process_frame = ttk.Frame(input_frame)
        process_frame.pack(fill=tk.X, padx=10, pady=15)
        
        self.process_btn = ttk.Button(process_frame, text="Generate PDFs for both paper sizes", command=self.process_current_image)
        self.process_btn.pack(fill=tk.X, padx=20)
        
        # Right side - Metadata preview
        metadata_frame = ttk.LabelFrame(bottom_frame, text="Metadata Preview")
        metadata_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Metadata display
        self.metadata_text = tk.Text(metadata_frame, wrap=tk.WORD, height=12, width=40)
        self.metadata_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.metadata_text.config(state=tk.DISABLED)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready. Open an image to begin. Use mouse wheel or +/- keys to zoom.")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, padx=5, pady=2)
        
        # Update UI state
        self.update_ui_state()
    
    def open_image(self):
        # Open file dialog
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff *.tif"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            # Reset image list to just this file
            self.image_files = [file_path]
            self.current_index = 0
            self.load_current_image()
    
    def open_directory(self):
        # Open directory dialog
        directory = filedialog.askdirectory(title="Select Directory with Images")
        
        if directory:
            # Find all image files in the directory
            all_files = os.listdir(directory)
            self.image_files = [
                os.path.join(directory, f) for f in all_files 
                if self.is_image_file(f) and os.path.isfile(os.path.join(directory, f))
            ]
            
            # Sort files alphabetically
            self.image_files.sort()
            
            if self.image_files:
                self.current_index = 0
                self.load_current_image()
                self.status_var.set(f"Loaded {len(self.image_files)} images from directory")
            else:
                messagebox.showinfo("No Images", "No image files found in the selected directory")
                self.status_var.set("No images found in directory")
    
    def is_image_file(self, filename):
        """Check if a file is an image based on its extension"""
        ext = os.path.splitext(filename)[1].lower()
        return ext in IMAGE_EXTENSIONS
    
    def load_current_image(self):
        if 0 <= self.current_index < len(self.image_files):
            self.current_image_path = self.image_files[self.current_index]
            
            # Load image using OpenCV
            self.cv2_image = cv2.imread(self.current_image_path)
            
            if self.cv2_image is None:
                messagebox.showerror("Error", f"Failed to load image: {self.current_image_path}")
                return
            
            # Get base filename to suggest as object name
            base_name = os.path.splitext(os.path.basename(self.current_image_path))[0]
            self.name_var.set(base_name)
            
            # Convert to PIL format for Tkinter
            cv2_rgb = cv2.cvtColor(self.cv2_image, cv2.COLOR_BGR2RGB)
            self.original_pil_image = Image.fromarray(cv2_rgb)
            
            # Reset zoom when loading a new image
            self.zoom_factor = 1.0
            self.update_zoom_label()
            
            # Display the image
            self.update_display_image()
            
            # Update counter
            self.image_counter.config(text=f"Image {self.current_index + 1} of {len(self.image_files)}")
            
            # Update status
            self.status_var.set(f"Loaded: {os.path.basename(self.current_image_path)}")
            
            # Update UI state
            self.update_ui_state()
    
    def update_display_image(self):
        """Update the displayed image with current zoom settings"""
        if self.original_pil_image:
            # Get canvas dimensions
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            # Use minimum dimensions if canvas is not yet fully created
            if canvas_width < 100:
                canvas_width = 800
            if canvas_height < 100:
                canvas_height = 400
            
            # Get original image dimensions
            img_width, img_height = self.original_pil_image.size
            
            # Calculate base scaling factor to fit in canvas
            width_ratio = canvas_width / img_width
            height_ratio = canvas_height / img_height
            base_scale = min(width_ratio, height_ratio)
            
            # Apply minimum scale to ensure small images are visible
            # This ensures that images smaller than 300px in either dimension
            # will be scaled up for better visibility
            min_target_size = 300  # Minimum target size in pixels
            if img_width < min_target_size or img_height < min_target_size:
                width_min_scale = min_target_size / img_width if img_width < min_target_size else 0
                height_min_scale = min_target_size / img_height if img_height < min_target_size else 0
                min_scale = max(width_min_scale, height_min_scale)
                base_scale = max(base_scale, min_scale)
            
            # Apply zoom factor to base scale
            final_scale = base_scale * self.zoom_factor
            
            # Calculate new dimensions
            new_width = int(img_width * final_scale)
            new_height = int(img_height * final_scale)
            
            # Resize image
            resized_img = self.original_pil_image.resize((new_width, new_height), Image.LANCZOS)
            
            # Add a subtle border to make the image more visible
            # Create a slightly larger image with a visible border
            border_width = 2
            bordered_img = Image.new('RGB', (new_width + 2*border_width, new_height + 2*border_width), 'white')
            bordered_img.paste(resized_img, (border_width, border_width))
            
            # Convert to PhotoImage for display
            self.display_image = ImageTk.PhotoImage(bordered_img)
            
            # Display the image
            self.show_image()
    
    def show_image(self):
        """Display the current image on the canvas"""
        # Clear previous image
        self.canvas.delete("all")
        
        if self.display_image:
            # Center image on canvas
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            x_position = max(0, (canvas_width - self.display_image.width()) // 2)
            y_position = max(0, (canvas_height - self.display_image.height()) // 2)
            
            # Show image
            self.canvas.create_image(x_position, y_position, anchor=tk.NW, image=self.display_image)
            
            # Get pixel dimensions
            img_height, img_width = self.cv2_image.shape[:2]
            
            # Display dimensions in bottom-right corner with more visible text
            self.canvas.create_text(
                canvas_width - 10, canvas_height - 10,
                text=f"Dimensions: {img_width} × {img_height} px",
                anchor=tk.SE,
                fill="yellow",
                font=('Arial', 10, 'bold')
            )
    
    def zoom_in(self):
        """Increase zoom level"""
        if self.original_pil_image:
            self.zoom_factor = min(self.max_zoom, self.zoom_factor * 1.2)
            self.update_zoom_label()
            self.update_display_image()
    
    def zoom_out(self):
        """Decrease zoom level"""
        if self.original_pil_image:
            self.zoom_factor = max(self.min_zoom, self.zoom_factor / 1.2)
            self.update_zoom_label()
            self.update_display_image()
    
    def reset_zoom(self):
        """Reset zoom to 100%"""
        if self.original_pil_image:
            self.zoom_factor = 1.0
            self.update_zoom_label()
            self.update_display_image()
    
    def update_zoom_label(self):
        """Update the zoom percentage label"""
        zoom_percent = int(self.zoom_factor * 100)
        self.zoom_label.config(text=f"{zoom_percent}%")
    
    def mouse_wheel(self, event):
        """Handle mouse wheel events for zooming"""
        if self.original_pil_image:
            # Determine scroll direction based on platform
            if event.num == 5 or event.delta < 0:  # Scroll down
                self.zoom_out()
            elif event.num == 4 or event.delta > 0:  # Scroll up
                self.zoom_in()
    
    def previous_image(self):
        if self.image_files and self.current_index > 0:
            self.current_index -= 1
            self.load_current_image()
    
    def next_image(self):
        if self.image_files and self.current_index < len(self.image_files) - 1:
            self.current_index += 1
            self.load_current_image()
    
    def update_ui_state(self):
        # Enable/disable navigation buttons
        has_images = len(self.image_files) > 0
        has_prev = self.current_index > 0
        has_next = self.current_index < len(self.image_files) - 1
        
        self.prev_btn.config(state=tk.NORMAL if has_prev else tk.DISABLED)
        self.next_btn.config(state=tk.NORMAL if has_next else tk.DISABLED)
        self.process_btn.config(state=tk.NORMAL if has_images else tk.DISABLED)
    
    def create_pdf_with_metadata(self, pdf_path, paper_width_inches, metadata):
        """Create a PDF with the image and metadata block in the top-left corner"""
        # Get image dimensions
        img = self.cv2_image
        img_height, img_width = img.shape[:2]
        
        # Calculate physical dimensions in inches
        # Convert from meters to inches
        width_inches = metadata["width_m"] * 39.37
        height_inches = metadata["height_m"] * 39.37
        
        # Determine if scaling is needed
        scale_factor = metadata["scale_factor"]
        
        # Calculate adjusted dimensions
        adjusted_width_inches = width_inches * scale_factor
        adjusted_height_inches = height_inches * scale_factor
        
        # Create PDF canvas
        c = canvas.Canvas(pdf_path, pagesize=(paper_width_inches * inch, adjusted_height_inches * inch))
        
        # Calculate left margin to center the image
        left_margin_inches = (paper_width_inches - adjusted_width_inches) / 2
        
        # Add metadata block in top-left corner
        self.add_metadata_block(c, metadata, paper_width_inches)
        
        # Save the original image to a temporary file (reportlab requires a file path)
        temp_dir = os.path.dirname(pdf_path)
        temp_image_path = os.path.join(temp_dir, "temp_image.png")
        cv2.imwrite(temp_image_path, self.cv2_image)
        
        # Draw the image, centered horizontally
        c.drawImage(
            temp_image_path, 
            left_margin_inches * inch,
            0,  # Bottom edge of the page
            width=adjusted_width_inches * inch,
            height=adjusted_height_inches * inch,
            preserveAspectRatio=True
        )
        
        # Finalize the PDF
        c.save()
        
        # Remove the temporary image
        try:
            os.remove(temp_image_path)
        except:
            pass
            
        return True
    
    def add_metadata_block(self, pdf_canvas, metadata, paper_width_inches):
        """Add a metadata block to the top-left corner of the PDF"""
        # Set position for metadata block (in points, 1/72 inch)
        x = 20  # 20 points from left edge
        y = pdf_canvas._pagesize[1] - 100  # 100 points from top edge
        
        # Set font and color
        pdf_canvas.setFont("Helvetica-Bold", 12)
        pdf_canvas.setFillColorRGB(0, 0, 0)  # Black text
        
        # Draw white rectangle with black border for metadata block
        block_width = 300
        block_height = 90
        pdf_canvas.setFillColorRGB(1, 1, 1)  # White fill
        pdf_canvas.setStrokeColorRGB(0, 0, 0)  # Black border
        pdf_canvas.rect(x - 5, y - block_height + 5, block_width, block_height, fill=1)
        
        # Reset fill color for text
        pdf_canvas.setFillColorRGB(0, 0, 0)  # Black text
        
        # Add metadata text
        pdf_canvas.setFont("Helvetica-Bold", 10)
        pdf_canvas.drawString(x, y, f"Object: {metadata['object_name']}")
        y -= 15
        
        pdf_canvas.setFont("Helvetica", 9)
        pdf_canvas.drawString(x, y, f"Size: {metadata['width_m']:.2f}m × {metadata['height_m']:.2f}m")
        y -= 12
        
        pdf_canvas.drawString(x, y, f"Scale: {metadata['scale_text']}")
        y -= 12
        
        pdf_canvas.drawString(x, y, f"Paper: {paper_width_inches}\" wide roll")
        y -= 12
        
        pdf_canvas.drawString(x, y, f"Date: {metadata['date']}")
        y -= 12
        
        pdf_canvas.drawString(x, y, f"File: {os.path.basename(metadata['source_image'])}")
    
    def process_current_image(self):
        if not self.current_image_path or self.cv2_image is None:
            messagebox.showinfo("No Image", "Please load an image first")
            return
        
        # Validate inputs
        try:
            width_m = self.width_m  # Fixed at 1.0m
            height_m = float(self.height_var.get())
            
            if height_m <= 0:
                messagebox.showerror("Invalid Input", "Height must be a positive value")
                return
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid numeric height")
            return
        
        # Get object name
        object_name = self.name_var.get().strip()
        if not object_name:
            object_name = os.path.splitext(os.path.basename(self.current_image_path))[0]
        
        # Sanitize name for filename
        safe_name = re.sub(r'[\\/*?:"<>|]', "_", object_name)
        
        # Format metadata
        timestamp = datetime.now().strftime("%Y-%m-%d")
        
        # PDF generation results
        results = []
        metadata_content = ""
        
        # Process for each paper size
        for paper_size_key, paper_info in self.paper_sizes.items():
            paper_width_inches = paper_info["width_inches"]
            paper_width_m = (paper_width_inches * 2.54) / 100  # Convert to meters
            output_dir = self.get_output_dir_for_paper_size(paper_size_key)
            
            # Determine if scaling is needed
            scale_factor = 1.0
            if width_m > paper_width_m:
                scale_factor = paper_width_m / width_m
            
            # Calculate adjusted dimensions
            adjusted_width_m = width_m * scale_factor
            adjusted_height_m = height_m * scale_factor
            
            # Calculate margins
            horizontal_margin_m = (paper_width_m - adjusted_width_m) / 2
            
            # Generate scale text
            if scale_factor < 0.99:
                scale_text = f"1:{int(1/scale_factor)}"
            else:
                scale_text = "1:1"
            
            # Collect metadata for PDF generation
            metadata = {
                "object_name": object_name,
                "width_m": width_m,
                "height_m": height_m,
                "paper_width_inches": paper_width_inches,
                "adjusted_width_m": adjusted_width_m,
                "adjusted_height_m": adjusted_height_m,
                "scale_factor": scale_factor,
                "scale_text": scale_text,
                "horizontal_margin_m": horizontal_margin_m,
                "date": timestamp,
                "source_image": self.current_image_path
            }
            
            # Create PDF file
            pdf_filename = f"{safe_name}_{width_m:.2f}mx{height_m:.2f}m_{scale_text}_{paper_width_inches}in.pdf"
            pdf_path = os.path.join(output_dir, pdf_filename)
            
            try:
                # Generate the PDF with metadata block
                self.create_pdf_with_metadata(pdf_path, paper_width_inches, metadata)
                
                # Generate metadata text file (for reference)
                metadata_filename = f"{safe_name}_{width_m:.2f}mx{height_m:.2f}m_{scale_text}_{paper_width_inches}in_metadata.txt"
                metadata_path = os.path.join(output_dir, metadata_filename)
                
                metadata_text = f"PDF PRINTING METADATA ({paper_width_inches}\" paper)\n{'-'*50}\n"
                metadata_text += f"Object name: {object_name}\n"
                metadata_text += f"Original dimensions: {width_m:.2f}m × {height_m:.2f}m\n"
                metadata_text += f"Paper: {paper_width_inches}\" wide roll\n"
                metadata_text += f"Print dimensions: {adjusted_width_m:.2f}m × {adjusted_height_m:.2f}m\n"
                metadata_text += f"Scale: {scale_text}\n"
                metadata_text += f"Horizontal margins: {horizontal_margin_m:.2f}m on each side\n"
                metadata_text += f"Date: {timestamp}\n"
                metadata_text += f"Source image: {self.current_image_path}\n"
                metadata_text += f"PDF filename: {pdf_filename}\n"
                
                # Save metadata file
                with open(metadata_path, 'w') as f:
                    f.write(metadata_text)
                
                # Add to the combined metadata content
                if metadata_content:
                    metadata_content += "\n\n" + "="*50 + "\n\n"
                metadata_content += metadata_text
                
                # Add to results
                results.append((paper_size_key, pdf_path))
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create PDF for {paper_size_key}: {str(e)}")
        
        if results:
            # Update metadata preview with combined information
            self.metadata_text.config(state=tk.NORMAL)
            self.metadata_text.delete(1.0, tk.END)
            self.metadata_text.insert(tk.END, metadata_content)
            self.metadata_text.config(state=tk.DISABLED)
            
            # Update status
            self.status_var.set(f"PDFs generated for both 42\" and 44\" paper sizes")
            
            # Show success message
            message = "PDFs created successfully:\n"
            for paper_size, path in results:
                message += f"• {paper_size}: {os.path.basename(path)}\n"
            messagebox.showinfo("Success", message)
    
    def set_output_directory(self):
        directory = filedialog.askdirectory(title="Select Base Output Directory")
        if directory:
            self.base_output_dir = directory
            
            # Create output directories
            self.create_output_directories()
            
            self.status_var.set(f"Base output directory set to: {self.base_output_dir}")
    
    def show_instructions(self):
        instructions = (
            "PDF Metadata Generator Instructions\n\n"
            "This tool helps you generate PDFs for printing on wide-format paper:\n\n"
            "1. Load an image or a directory of images using the File menu\n"
            "2. Navigate between images using the Previous/Next buttons or arrow keys\n"
            "3. Use mouse wheel or +/- keys to zoom the image for better visibility\n"
            "4. Enter the height in meters (width is fixed at 1.0m)\n"
            "5. Enter a name for the object (optional)\n"
            "6. Click 'Generate PDFs for both paper sizes' to create files\n\n"
            "The tool will automatically generate PDFs for both 42\" and 44\" paper\n"
            "in separate folders, with a metadata block in the top-left corner."
        )
        messagebox.showinfo("Instructions", instructions)
    
    def show_about(self):
        about_text = (
            "PDF Metadata Generator v2.1\n\n"
            "A tool for creating PDFs from orthographic renderings\n"
            "to be printed on 42-inch or 44-inch wide format paper.\n\n"
            "Features:\n"
            "- Fixed width of 1.0m for consistency\n"
            "- Automatically creates PDFs for both 42\" and 44\" paper\n"
            "- Organizes PDFs in separate folders by paper size\n"
            "- Adds metadata block to the top-left corner of each PDF\n\n"
            "Created with Python, Tkinter, OpenCV, and ReportLab."
        )
        messagebox.showinfo("About", about_text)

def main():
    root = tk.Tk()
    app = PDFMetadataApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 