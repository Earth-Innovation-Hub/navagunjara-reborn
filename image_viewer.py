#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk, ImageFilter
import os
import re
import numpy as np
import math
import cv2  # OpenCV for image processing
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import landscape
import tempfile

class ImageViewerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Image Viewer with Grid")
        self.geometry("1000x700")
        self.minsize(800, 600)
        
        # Try to set application icon if available
        try:
            self.iconbitmap('icon.ico')
        except:
            pass
        
        # State variables
        self.current_image = None
        self.image_list = []
        self.current_index = 0
        self.display_image = None
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        
        # Grid variables
        self.show_grid = True
        self.grid_size = 0.1  # Default grid size in meters
        self.image_height_m = 1.0  # Default height in meters
        self.image_width_m = 1.0  # Fixed width in meters
        self.grid_color = "#444444"  # Dark gray for grid lines (changed from cyan)
        
        # Content detection variables
        self.content_bbox = None  # Bounding box for detected content (x1, y1, x2, y2)
        self.show_content_bbox = False  # Whether to show the content bounding box
        self.content_bbox_color = "#FF4444"  # Red color for content bounding box
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready. Open a folder to begin. Use mouse wheel or +/- keys to zoom.")
        
        # Initialize variables 
        self.filename_var = tk.StringVar()
        self.dimensions_var = tk.StringVar(value="1.00m × 1.00m")
        self.grid_size_var = tk.StringVar(value=f"{self.grid_size}m")
        
        # Create main frame to contain all widgets
        self.main_frame = tk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=1)
        
        # Create frame for canvas
        self.canvas_frame = tk.Frame(self.main_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=1)
        
        # Create canvas for displaying images
        self.canvas = tk.Canvas(self.canvas_frame, bg="gray")
        self.canvas.pack(fill=tk.BOTH, expand=1)
        
        # Create scrollbars for canvas
        self.v_scrollbar = tk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.h_scrollbar = tk.Scrollbar(self.canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)
        
        self.v_scrollbar.pack(side="right", fill="y")
        self.h_scrollbar.pack(side="bottom", fill="x")
        
        # Set up canvas mouse events
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_press)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)  # Windows
        self.canvas.bind("<Button-4>", self.on_mousewheel)  # Linux scroll up
        self.canvas.bind("<Button-5>", self.on_mousewheel)  # Linux scroll down
        
        # Create status bar
        self.status_bar = tk.Label(self.main_frame, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Create info frame (for image counter, filename)
        self.info_frame = tk.Frame(self.main_frame)
        self.info_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Create image counter
        self.image_counter = tk.Label(self.info_frame, text="No images loaded")
        self.image_counter.pack(side=tk.LEFT, padx=5, pady=3)
        
        # Create filename label
        tk.Label(self.info_frame, text="File:").pack(side=tk.LEFT, padx=(15, 2), pady=3)
        tk.Label(self.info_frame, textvariable=self.filename_var).pack(side=tk.LEFT, padx=2, pady=3)
        
        # Create dimensions label
        tk.Label(self.info_frame, text="Dimensions:").pack(side=tk.LEFT, padx=(15, 2), pady=3)
        tk.Label(self.info_frame, textvariable=self.dimensions_var).pack(side=tk.LEFT, padx=2, pady=3)
        
        # Create grid size label
        tk.Label(self.info_frame, text="Grid:").pack(side=tk.LEFT, padx=(15, 2), pady=3)
        tk.Label(self.info_frame, textvariable=self.grid_size_var).pack(side=tk.LEFT, padx=2, pady=3)
        
        # Create zoom indicator
        zoom_frame = tk.Frame(self.info_frame)
        zoom_frame.pack(side=tk.RIGHT, padx=5, pady=3)
        
        tk.Label(zoom_frame, text="Zoom:").pack(side=tk.LEFT)
        self.zoom_label = tk.Label(zoom_frame, text="100%", width=6)
        self.zoom_label.pack(side=tk.LEFT, padx=2)
        
        # Create control frame
        self.control_frame = tk.Frame(self.main_frame)
        self.control_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Create buttons
        self.prev_btn = tk.Button(self.control_frame, text="Previous", command=self.prev_image)
        self.prev_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.next_btn = tk.Button(self.control_frame, text="Next", command=self.next_image)
        self.next_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.open_folder_btn = tk.Button(self.control_frame, text="Open Folder", command=self.open_folder)
        self.open_folder_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Add grid controls
        self.set_height_btn = tk.Button(self.control_frame, text="Set Height", command=self.set_image_height)
        self.set_height_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.toggle_grid_btn = tk.Button(self.control_frame, text="Toggle Grid", command=self.toggle_grid)
        self.toggle_grid_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.adjust_grid_btn = tk.Button(self.control_frame, text="Adjust Grid Size", command=self.adjust_grid_size)
        self.adjust_grid_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Add content detection button
        self.detect_content_btn = tk.Button(self.control_frame, text="Detect Content", command=self.detect_content)
        self.detect_content_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Add PDF export controls
        self.export_pdf_42_btn = tk.Button(self.control_frame, text="Export 42\" PDF", command=lambda: self.export_to_pdf(42))
        self.export_pdf_42_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.export_pdf_44_btn = tk.Button(self.control_frame, text="Export 44\" PDF", command=lambda: self.export_to_pdf(44))
        self.export_pdf_44_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Create menu
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)
        
        # File menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Open Folder", command=self.open_folder)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Export to PDF (42\")", command=lambda: self.export_to_pdf(42))
        self.file_menu.add_command(label="Export to PDF (44\")", command=lambda: self.export_to_pdf(44))
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.quit)
        
        # View menu
        self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="View", menu=self.view_menu)
        self.view_menu.add_command(label="Zoom In", command=self.zoom_in)
        self.view_menu.add_command(label="Zoom Out", command=self.zoom_out)
        self.view_menu.add_command(label="Reset Zoom", command=self.reset_zoom)
        self.view_menu.add_separator()
        self.view_menu.add_checkbutton(label="Show Grid", command=self.toggle_grid, variable=tk.BooleanVar(value=self.show_grid))
        self.view_menu.add_command(label="Set Image Height", command=self.set_image_height)
        self.view_menu.add_command(label="Adjust Grid Size", command=self.adjust_grid_size)
        self.view_menu.add_separator()
        self.view_menu.add_command(label="Detect Content", command=self.detect_content)
        self.view_menu.add_checkbutton(label="Show Content Box", command=self.toggle_content_bbox, variable=tk.BooleanVar(value=self.show_content_bbox))
        
        # Help menu
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)
        self.help_menu.add_command(label="About", command=self.show_about)
        
        # Variables for canvas dragging
        self.drag_data = {"x": 0, "y": 0, "dragging": False}
        
        # Variables for image display
        self.image_item = None
        
        # Set initial button states
        self.update_ui_state()
        
        # Bind keyboard shortcuts
        self.bind("<Left>", lambda event: self.prev_image())
        self.bind("<Right>", lambda event: self.next_image())
        self.bind("+", lambda event: self.zoom_in())
        self.bind("-", lambda event: self.zoom_out())
        self.bind("r", lambda event: self.reset_zoom())
        self.bind("g", lambda event: self.toggle_grid())
        self.bind("h", lambda event: self.set_image_height())
        self.bind("s", lambda event: self.adjust_grid_size())
        self.bind("4", lambda event: self.export_to_pdf(42))  # 42" paper with Ctrl+4
        self.bind("5", lambda event: self.export_to_pdf(44))  # 44" paper with Ctrl+5
        self.bind("d", lambda event: self.detect_content())  # Detect content with 'd'
        self.bind("b", lambda event: self.toggle_content_bbox())
    
    def on_canvas_press(self, event):
        """Handle mouse button press on canvas"""
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        self.drag_data["dragging"] = True
    
    def on_canvas_drag(self, event):
        """Handle mouse drag on canvas for panning"""
        if self.drag_data["dragging"]:
            dx = event.x - self.drag_data["x"]
            dy = event.y - self.drag_data["y"]
            self.canvas.scan_dragto(event.x, event.y, gain=1)
            self.canvas.scan_mark(self.drag_data["x"], self.drag_data["y"])
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y
    
    def on_canvas_release(self, event):
        """Handle mouse button release on canvas"""
        self.drag_data["dragging"] = False
    
    def on_mousewheel(self, event):
        """Handle mouse wheel events for zooming"""
        if hasattr(self, 'original_pil_image'):
            # Determine scroll direction based on platform
            if hasattr(event, 'num') and event.num == 5 or hasattr(event, 'delta') and event.delta < 0:  # Scroll down
                self.zoom_out()
            elif hasattr(event, 'num') and event.num == 4 or hasattr(event, 'delta') and event.delta > 0:  # Scroll up
                self.zoom_in()
    
    def open_folder(self):
        # Open directory dialog
        directory = filedialog.askdirectory(title="Select Directory with Images")
        
        if directory:
            # Find all image files in the directory
            all_files = os.listdir(directory)
            image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff')
            self.image_list = [
                os.path.join(directory, f) for f in all_files 
                if f.lower().endswith(image_extensions) and os.path.isfile(os.path.join(directory, f))
            ]
            
            # Sort files alphabetically
            self.image_list.sort()
            
            if self.image_list:
                self.current_index = 0
                self.load_current_image()
                self.status_var.set(f"Loaded {len(self.image_list)} images from directory")
            else:
                messagebox.showinfo("No Images", "No image files found in the selected directory")
                self.status_var.set("No images found in directory")
    
    def load_current_image(self):
        if 0 <= self.current_index < len(self.image_list):
            self.current_image = self.image_list[self.current_index]
            
            try:
                # Load the image
                img = Image.open(self.current_image)
                self.original_pil_image = img
                
                # Reset zoom when loading a new image
                self.zoom_factor = 1.0
                self.update_zoom_label()
                
                # Display the image
                self.update_display_image()
                
                # Update counter and info
                self.image_counter.config(text=f"Image {self.current_index + 1} of {len(self.image_list)}")
                self.filename_var.set(os.path.basename(self.current_image))
                
                # Update status
                self.status_var.set(f"Loaded: {os.path.basename(self.current_image)}")
                
                # Update UI state
                self.update_ui_state()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {self.current_image}\n\nError: {str(e)}")
                import traceback
                traceback.print_exc()
    
    def update_display_image(self):
        """Update the displayed image with current zoom settings"""
        if hasattr(self, 'original_pil_image'):
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
            
            # Apply zoom factor to base scale
            final_scale = base_scale * self.zoom_factor
            
            # Calculate new dimensions
            new_width = int(img_width * final_scale)
            new_height = int(img_height * final_scale)
            
            # Resize image
            resized_img = self.original_pil_image.resize((new_width, new_height), Image.LANCZOS)
            
            # Convert to PhotoImage for display
            self.display_image = ImageTk.PhotoImage(resized_img)
            
            # Display the image
            self.show_image()
    
    def show_image(self, render_grid=True):
        if not hasattr(self, 'original_pil_image'):
            return

        # Get current canvas width & height
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # Calculate the size to fit in view
        img_width, img_height = self.original_pil_image.size
        scale = min(canvas_width / img_width, canvas_height / img_height)
        
        # Scale image
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)

        # Clear old image and grid
        self.canvas.delete("all")

        # Create and save the photo image
        resized_img = self.original_pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.displayed_img = ImageTk.PhotoImage(resized_img)
        
        # Calculate position to center the image
        x_position = (canvas_width - new_width) // 2
        y_position = (canvas_height - new_height) // 2
        
        # Draw the image on canvas
        self.img_id = self.canvas.create_image(x_position, y_position, anchor=tk.NW, image=self.displayed_img)
        
        # Draw grid on top if enabled
        if render_grid and self.show_grid:
            self.draw_grid(x_position, y_position, new_width, new_height, scale)
        
        # Draw content bounding box if enabled
        if hasattr(self, 'show_content_bbox') and self.show_content_bbox and self.content_bbox:
            x_min, y_min, x_max, y_max = self.content_bbox
            # Scale to match current display
            x1 = x_position + x_min * scale
            y1 = y_position + y_min * scale
            x2 = x_position + x_max * scale
            y2 = y_position + y_max * scale
            
            # Draw bounding box with a 3-pixel wide line
            self.canvas.create_rectangle(
                x1, y1, x2, y2, 
                outline=self.content_bbox_color, 
                width=3,
                dash=(10, 5)  # Dashed line pattern
            )
            
            # Draw dimensions text
            content_width_m = (x_max - x_min) / img_width * self.image_width_m
            content_height_m = (y_max - y_min) / img_height * self.image_height_m
            
            # Convert meters to feet and inches
            content_width_feet = content_width_m * 3.28084  # 1 meter = 3.28084 feet
            content_height_feet = content_height_m * 3.28084
            
            # Convert to feet and inches format
            width_feet = int(content_width_feet)
            width_inches = int((content_width_feet - width_feet) * 12)
            height_feet = int(content_height_feet)
            height_inches = int((content_height_feet - height_feet) * 12)
            
            # Format the imperial dimensions string
            width_imperial = f"{width_feet}'{width_inches}\""
            height_imperial = f"{height_feet}'{height_inches}\""
            
            # Put dimensions text above the box with both metric and imperial units
            self.canvas.create_text(
                (x1 + x2) / 2, y1 - 10,
                text=f"{content_width_m:.2f}m × {content_height_m:.2f}m ({width_imperial} × {height_imperial})",
                fill=self.content_bbox_color,
                font=('Helvetica', 12, 'bold'),
                anchor=tk.S
            )
        
        # Update status with image dimensions
        physical_width = self.image_width_m
        physical_height = physical_width * (img_height / img_width)
        self.status_var.set(f"Image dimensions: {physical_width:.2f}m × {physical_height:.2f}m | Scale: {self.grid_size:.2f}m grid")
        
        # Make the status label visible if it's hidden
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def zoom_in(self):
        """Increase zoom level"""
        if hasattr(self, 'original_pil_image'):
            self.zoom_factor = min(self.max_zoom, self.zoom_factor * 1.2)
            self.update_zoom_label()
            self.update_display_image()
    
    def zoom_out(self):
        """Decrease zoom level"""
        if hasattr(self, 'original_pil_image'):
            self.zoom_factor = max(self.min_zoom, self.zoom_factor / 1.2)
            self.update_zoom_label()
            self.update_display_image()
    
    def reset_zoom(self):
        """Reset zoom to 100%"""
        if hasattr(self, 'original_pil_image'):
            self.zoom_factor = 1.0
            self.update_zoom_label()
            self.update_display_image()
    
    def update_zoom_label(self):
        """Update the zoom percentage label"""
        zoom_percent = int(self.zoom_factor * 100)
        self.zoom_label.config(text=f"{zoom_percent}%")
    
    def prev_image(self):
        if self.image_list and self.current_index > 0:
            self.current_index -= 1
            self.load_current_image()
    
    def next_image(self):
        if self.image_list and self.current_index < len(self.image_list) - 1:
            self.current_index += 1
            self.load_current_image()
    
    def update_ui_state(self):
        """Enable/disable buttons based on current state"""
        has_images = len(self.image_list) > 0
        has_prev = self.current_index > 0
        has_next = self.current_index < len(self.image_list) - 1
        
        self.prev_btn.config(state=tk.NORMAL if has_prev else tk.DISABLED)
        self.next_btn.config(state=tk.NORMAL if has_next else tk.DISABLED)
    
    def show_about(self):
        about_text = (
            "Image Viewer with Grid v1.2\n\n"
            "A simple application for viewing images in a folder with grid measurement support "
            "and PDF export capabilities.\n\n"
            "Features:\n"
            "- Browse through all images in a folder\n"
            "- Zoom in/out and pan around images\n"
            "- Keyboard shortcuts for navigation\n"
            "- Support for common image formats\n"
            "- Overlay grid with customizable size\n"
            "- Set image height for accurate measurements (width fixed at 1m)\n"
            "- Export to PDF with 42\" or 44\" paper width\n\n"
            "Keyboard Shortcuts:\n"
            "- Left/Right arrows: Navigate images\n"
            "- +/-: Zoom in/out\n"
            "- r: Reset zoom\n"
            "- g: Toggle grid\n"
            "- h: Set image height\n"
            "- s: Adjust grid size\n"
            "- 4: Export to PDF (42\")\n"
            "- 5: Export to PDF (44\")\n"
            "- d: Detect content\n"
            "- b: Toggle content bounding box\n\n"
            "Created with Python and Tkinter."
        )
        messagebox.showinfo("About", about_text)
    
    def set_image_height(self):
        """Set the height of the image in meters (width is fixed at 1m)"""
        if not hasattr(self, 'original_pil_image'):
            messagebox.showinfo("No Image", "Please load an image first")
            return
            
        current_height = self.image_height_m
        new_height = simpledialog.askfloat(
            "Set Image Height", 
            "Enter image height in meters (width is fixed at 1m):",
            initialvalue=current_height,
            minvalue=0.1,
            maxvalue=10.0
        )
        
        if new_height and new_height != current_height:
            self.image_height_m = new_height
            self.dimensions_var.set(f"1.00m × {self.image_height_m:.2f}m")
            self.status_var.set(f"Image dimensions set to 1.00m × {self.image_height_m:.2f}m")
            
            # Refresh the display
            if self.show_grid:
                self.show_image()
    
    def toggle_grid(self):
        """Toggle grid visibility"""
        self.show_grid = not self.show_grid
        self.show_image()
        self.status_var.set(f"Grid {('visible' if self.show_grid else 'hidden')}. Grid size: {self.grid_size:.2f}m")
    
    def adjust_grid_size(self):
        """Open dialog to adjust grid size"""
        if not hasattr(self, 'original_pil_image'):
            messagebox.showinfo("No Image", "Please load an image first")
            return
            
        current_size = self.grid_size
        new_size = simpledialog.askfloat(
            "Adjust Grid Size", 
            "Enter grid size in meters (e.g., 0.1 for 10cm):",
            initialvalue=current_size,
            minvalue=0.01,
            maxvalue=1.0
        )
        
        if new_size and new_size != current_size:
            self.grid_size = new_size
            self.grid_size_var.set(f"{self.grid_size:.2f}m")
            self.status_var.set(f"Grid size updated to {self.grid_size:.2f}m")
            
            # Refresh the display
            if self.show_grid:
                self.show_image()
    
    def draw_grid(self, x_position, y_position, img_width, img_height, scale):
        """Draw a grid overlay on the canvas using the physical dimensions"""
        # Calculate grid spacing in pixels (convert from meters)
        # For width: 1m wide image
        grid_spacing_x = (img_width / self.image_width_m) * self.grid_size
        # For height: based on specified height
        grid_spacing_y = (img_height / self.image_height_m) * self.grid_size
        
        # Ensure minimum grid spacing for visibility (at least 5 pixels)
        if grid_spacing_x < 5:
            grid_spacing_x = 5
        if grid_spacing_y < 5:
            grid_spacing_y = 5
        
        # Draw vertical grid lines
        x = x_position
        line_count = 0
        while x <= x_position + img_width:
            # Make the 0.5m and 1.0m lines more visible
            if abs(line_count * self.grid_size % 0.5) < 0.001:  # Every 0.5m
                width = 3  # Make thicker
                fill_color = self.grid_color
            elif abs(line_count * self.grid_size % 0.1) < 0.001:  # Every 0.1m
                width = 1.5  # Make thicker
                fill_color = self.grid_color
            else:
                width = 1  # Make thicker
                fill_color = "#888888"  # Light gray for minor grid lines
                
            self.canvas.create_line(
                x, y_position, 
                x, y_position + img_height, 
                fill=fill_color, 
                width=width, 
                dash=(4, 4) if width < 3 else None
            )
            
            # Add label every 0.5m with larger font
            if abs(line_count * self.grid_size % 0.5) < 0.001:
                self.canvas.create_text(
                    x, y_position - 10,
                    text=f"{line_count * self.grid_size:.1f}m",
                    anchor=tk.S,
                    fill=self.grid_color,
                    font=('Arial', 12, 'bold')  # Larger, bold font
                )
            
            x += grid_spacing_x
            line_count += 1
        
        # Draw horizontal grid lines
        y = y_position
        line_count = 0
        while y <= y_position + img_height:
            # Make the 0.5m and 1.0m lines more visible
            if abs(line_count * self.grid_size % 0.5) < 0.001:  # Every 0.5m
                width = 3  # Make thicker
                fill_color = self.grid_color
            elif abs(line_count * self.grid_size % 0.1) < 0.001:  # Every 0.1m
                width = 1.5  # Make thicker
                fill_color = self.grid_color
            else:
                width = 1  # Make thicker
                fill_color = "#888888"  # Light gray for minor grid lines
                
            self.canvas.create_line(
                x_position, y, 
                x_position + img_width, y, 
                fill=fill_color, 
                width=width, 
                dash=(4, 4) if width < 3 else None
            )
            
            # Add label every 0.5m with larger font
            if abs(line_count * self.grid_size % 0.5) < 0.001:
                self.canvas.create_text(
                    x_position - 10, y,
                    text=f"{line_count * self.grid_size:.1f}m",
                    anchor=tk.E,
                    fill=self.grid_color,
                    font=('Arial', 12, 'bold')  # Larger, bold font
                )
            
            y += grid_spacing_y
            line_count += 1
            
        # Draw 10cm scale bar in the top left corner
        scale_bar_length = grid_spacing_x  # 10cm in pixels
        scale_bar_x = x_position + 40  # Offset from left edge
        scale_bar_y = y_position + 40  # Offset from top edge
        
        # Draw white outline for the scale bar (for visibility)
        self.canvas.create_line(
            scale_bar_x, scale_bar_y, 
            scale_bar_x + scale_bar_length, scale_bar_y, 
            fill="#FFFFFF",  # White outline for visibility
            width=7
        )
        self.canvas.create_line(
            scale_bar_x, scale_bar_y, 
            scale_bar_x, scale_bar_y + scale_bar_length, 
            fill="#FFFFFF",  # White outline for visibility
            width=7
        )
        
        # Draw the actual scale bar
        self.canvas.create_line(
            scale_bar_x, scale_bar_y, 
            scale_bar_x + scale_bar_length, scale_bar_y, 
            fill=self.grid_color,
            width=5
        )
        self.canvas.create_line(
            scale_bar_x, scale_bar_y, 
            scale_bar_x, scale_bar_y + scale_bar_length, 
            fill=self.grid_color,
            width=5
        )
        
        # Add scale bar labels with white outline effect
        # First draw white outline for horizontal label
        self.canvas.create_text(
            scale_bar_x + scale_bar_length/2, scale_bar_y - 15,
            text="10 cm",
            anchor=tk.S,
            fill="#FFFFFF",  # White outline for visibility
            font=('Arial', 14, 'bold')
        )
        
        # Draw horizontal label
        self.canvas.create_text(
            scale_bar_x + scale_bar_length/2, scale_bar_y - 15,
            text="10 cm",
            anchor=tk.S,
            fill=self.grid_color,
            font=('Arial', 14, 'bold')
        )
        
        # First draw white outline for vertical label
        self.canvas.create_text(
            scale_bar_x - 15, scale_bar_y + scale_bar_length/2,
            text="10 cm",
            anchor=tk.E,
            angle=90,  # Rotate text for vertical label
            fill="#FFFFFF",  # White outline for visibility
            font=('Arial', 14, 'bold')
        )
        
        # Draw vertical label
        self.canvas.create_text(
            scale_bar_x - 15, scale_bar_y + scale_bar_length/2,
            text="10 cm",
            anchor=tk.E,
            angle=90,  # Rotate text for vertical label
            fill=self.grid_color,
            font=('Arial', 14, 'bold')
        )

    def export_to_pdf(self, paper_width_inches):
        """Export current image to PDF with specified paper width"""
        if not hasattr(self, 'original_pil_image'):
            messagebox.showinfo("No Image", "Please load an image first")
            return
        
        # Ask user for save location
        output_file = filedialog.asksaveasfilename(
            title="Save PDF",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if not output_file:
            return  # User cancelled
        
        try:
            # Calculate dimensions
            # Convert paper width from inches to meters
            paper_width_m = (paper_width_inches * 2.54) / 100
            
            # Calculate the aspect ratio of the image
            img_width, img_height = self.original_pil_image.size
            aspect_ratio = img_height / img_width
            
            # Calculate paper height in inches based on aspect ratio and fixed 1m width
            # We keep the width at 1m in our model, so scale paper height accordingly
            paper_height_inches = paper_width_inches * (self.image_height_m / self.image_width_m)
            
            # Create a PDF with the specified paper size
            c = canvas.Canvas(output_file, pagesize=(paper_width_inches * inch, paper_height_inches * inch))
            
            # Save original image to a temporary file
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                temp_filename = temp_file.name
                self.original_pil_image.save(temp_filename, format="PNG")
            
            # Draw the image on the PDF, scaling to fit the page
            # No padding beyond what's needed for metric correctness
            c.drawImage(
                temp_filename, 
                0,  # x position (no padding)
                0,  # y position (no padding)
                width=paper_width_inches * inch,
                height=paper_height_inches * inch,
                preserveAspectRatio=True
            )
            
            # Add grid if enabled
            if self.show_grid:
                # Calculate grid spacing in points (1/72 of an inch)
                grid_spacing_x = (paper_width_inches * inch) / (self.image_width_m / self.grid_size)
                grid_spacing_y = (paper_height_inches * inch) / (self.image_height_m / self.grid_size)
                
                # Set grid line color and width
                c.setStrokeColorRGB(0.27, 0.27, 0.27)  # Dark gray (equivalent to #444444)
                
                # Draw vertical grid lines
                for x in range(0, int(paper_width_inches * inch) + 1, int(grid_spacing_x)):
                    # Thicker lines for major grid lines (0.5m and 1.0m)
                    x_meters = (x / (paper_width_inches * inch)) * self.image_width_m
                    
                    if abs(x_meters % 0.5) < 0.01:
                        c.setLineWidth(2.5)  # Thicker line for major grid lines
                    else:
                        c.setLineWidth(1.0)  # Thicker line for minor grid lines
                        
                    c.line(x, 0, x, paper_height_inches * inch)
                    
                    # Add labels for major grid lines with larger font
                    if abs(x_meters % 0.5) < 0.01:
                        c.setFont("Helvetica-Bold", 12)  # Larger, bold font
                        c.drawString(x + 4, 12, f"{x_meters:.1f}m")
                
                # Draw horizontal grid lines
                for y in range(0, int(paper_height_inches * inch) + 1, int(grid_spacing_y)):
                    # Thicker lines for major grid lines (0.5m and 1.0m)
                    y_meters = (y / (paper_height_inches * inch)) * self.image_height_m
                    
                    if abs(y_meters % 0.5) < 0.01:
                        c.setLineWidth(2.5)  # Thicker line for major grid lines
                    else:
                        c.setLineWidth(1.0)  # Thicker line for minor grid lines
                        
                    c.line(0, y, paper_width_inches * inch, y)
                    
                    # Add labels for major grid lines with larger font
                    if abs(y_meters % 0.5) < 0.01:
                        c.setFont("Helvetica-Bold", 12)  # Larger, bold font
                        c.drawString(4, y + 14, f"{y_meters:.1f}m")
                
                # Draw 10cm scale bar in the top left corner
                scale_bar_length = grid_spacing_x  # 10cm in pixels
                scale_bar_x = 50  # Offset from left edge
                scale_bar_y = 50  # Offset from top edge
                
                # Draw white outline for the scale bar (for visibility)
                c.setStrokeColorRGB(1, 1, 1)  # White
                c.setLineWidth(7)
                
                # Horizontal and vertical white outline
                c.line(scale_bar_x, scale_bar_y, scale_bar_x + scale_bar_length, scale_bar_y)
                c.line(scale_bar_x, scale_bar_y, scale_bar_x, scale_bar_y + scale_bar_length)
                
                # Draw the actual scale bar
                c.setStrokeColorRGB(0.27, 0.27, 0.27)  # Dark gray
                c.setLineWidth(5)
                
                # Horizontal and vertical lines
                c.line(scale_bar_x, scale_bar_y, scale_bar_x + scale_bar_length, scale_bar_y)
                c.line(scale_bar_x, scale_bar_y, scale_bar_x, scale_bar_y + scale_bar_length)
                
                # Add scale bar labels with white outline effect
                # First draw white outline for horizontal label
                c.setFillColorRGB(1, 1, 1)  # White
                c.setFont("Helvetica-Bold", 14)
                for offset_x, offset_y in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    c.drawString(scale_bar_x + scale_bar_length/2 - 20 + offset_x, 
                                scale_bar_y - 18 + offset_y, "10 cm")
                
                # Draw horizontal label
                c.setFillColorRGB(0.27, 0.27, 0.27)  # Dark gray
                c.setFont("Helvetica-Bold", 14)
                c.drawString(scale_bar_x + scale_bar_length/2 - 20, scale_bar_y - 18, "10 cm")
                
                # First draw white outline for vertical label
                c.setFillColorRGB(1, 1, 1)  # White
                c.saveState()
                c.translate(scale_bar_x - 18, scale_bar_y + scale_bar_length/2)
                c.rotate(90)
                for offset_x, offset_y in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    c.drawString(offset_x, offset_y, "10 cm")
                c.restoreState()
                
                # Draw vertical label
                c.setFillColorRGB(0.27, 0.27, 0.27)  # Dark gray
                c.saveState()
                c.translate(scale_bar_x - 18, scale_bar_y + scale_bar_length/2)
                c.rotate(90)
                c.drawString(0, 0, "10 cm")
                c.restoreState()
            
            # Add metadata to the PDF
            c.setTitle(f"Image: {os.path.basename(self.current_image)}")
            c.setAuthor("Image Viewer with Grid")
            c.setSubject(f"Dimensions: 1.00m × {self.image_height_m:.2f}m, Paper: {paper_width_inches}\" wide")
            
            # Save the PDF
            c.showPage()
            c.save()
            
            # Delete temporary file
            os.unlink(temp_filename)
            
            # Update status
            self.status_var.set(f"PDF exported successfully to {output_file} with {paper_width_inches}\" paper width")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Error creating PDF: {str(e)}")
            import traceback
            traceback.print_exc()

    def detect_content(self):
        """Detect the main content in the image using OpenCV image processing"""
        if not hasattr(self, 'original_pil_image'):
            messagebox.showinfo("No Image", "Please load an image first")
            return
            
        try:
            # Convert PIL image to OpenCV format
            img_np = np.array(self.original_pil_image)
            if len(img_np.shape) == 3 and img_np.shape[2] == 4:  # Has alpha channel
                # Convert RGBA to RGB
                img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGBA2RGB)
            else:
                img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            
            # Create a grayscale version for processing
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            
            # Apply GaussianBlur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Apply threshold to create binary image
            if np.mean(gray) > 127:  # Light background
                # Use inverse threshold for light backgrounds
                _, binary = cv2.threshold(blurred, 240, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            else:  # Dark background
                # Use regular threshold for dark backgrounds
                _, binary = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                
            # Apply morphological operations to clean up the binary image
            kernel = np.ones((5, 5), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
            
            # Find contours in the binary image
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                messagebox.showinfo("Detection Result", "No content detected in the image")
                return
                
            # Filter out small contours (noise)
            img_area = gray.shape[0] * gray.shape[1]
            min_contour_area = img_area * 0.01  # Minimum 1% of image area
            significant_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_contour_area]
            
            if not significant_contours:
                messagebox.showinfo("Detection Result", "No significant content detected in the image")
                return
                
            # Find the bounding box that encompasses all significant content
            x_min, y_min = float('inf'), float('inf')
            x_max, y_max = 0, 0
            
            for contour in significant_contours:
                x, y, w, h = cv2.boundingRect(contour)
                x_min = min(x_min, x)
                y_min = min(y_min, y)
                x_max = max(x_max, x + w)
                y_max = max(y_max, y + h)
            
            # Store the bounding box
            self.content_bbox = (x_min, y_min, x_max, y_max)
            
            # Calculate content dimensions in meters
            img_width, img_height = self.original_pil_image.size
            content_width_m = (x_max - x_min) / img_width * self.image_width_m
            content_height_m = (y_max - y_min) / img_height * self.image_height_m
            
            # Convert meters to feet and inches
            content_width_feet = content_width_m * 3.28084  # 1 meter = 3.28084 feet
            content_height_feet = content_height_m * 3.28084
            
            # Convert to feet and inches format
            width_feet = int(content_width_feet)
            width_inches = int((content_width_feet - width_feet) * 12)
            height_feet = int(content_height_feet)
            height_inches = int((content_height_feet - height_feet) * 12)
            
            # Format the imperial dimensions string
            width_imperial = f"{width_feet}'{width_inches}\""
            height_imperial = f"{height_feet}'{height_inches}\""
            
            # Enable the bounding box display
            self.show_content_bbox = True
            
            # Update the display
            self.show_image()
            
            # Show success message with content dimensions
            messagebox.showinfo(
                "Content Detected", 
                f"Content bounding box detected!\n\n"
                f"Metric: {content_width_m:.2f}m × {content_height_m:.2f}m\n"
                f"Imperial: {width_imperial} × {height_imperial}"
            )
            
            self.status_var.set(f"Content detected: {content_width_m:.2f}m × {content_height_m:.2f}m ({width_imperial} × {height_imperial})")
            
        except Exception as e:
            messagebox.showerror("Detection Error", f"Error during content detection: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def toggle_content_bbox(self):
        """Toggle visibility of the content bounding box"""
        if self.content_bbox is None:
            messagebox.showinfo("No Content Box", "Please detect content first")
            return
            
        self.show_content_bbox = not self.show_content_bbox
        self.show_image()
        self.status_var.set(f"Content bounding box {'visible' if self.show_content_bbox else 'hidden'}")

def main():
    app = ImageViewerApp()
    app.mainloop()

if __name__ == "__main__":
    main() 