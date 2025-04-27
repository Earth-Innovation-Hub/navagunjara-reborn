#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import os
import re
import numpy as np
import math

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
        self.show_grid = False
        self.grid_size = 0.1  # Default grid size in meters (10cm)
        self.image_height_m = 1.0  # Default height in meters
        self.image_width_m = 1.0  # Fixed width in meters
        self.grid_color = "#00FFFF"  # Cyan for grid lines
        
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
        
        # Create menu
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)
        
        # File menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Open Folder", command=self.open_folder)
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
    
    def show_image(self):
        """Display the current image on the canvas"""
        # Clear previous content
        self.canvas.delete("all")
        
        if hasattr(self, 'display_image'):
            # Center image on canvas
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            x_position = max(0, (canvas_width - self.display_image.width()) // 2)
            y_position = max(0, (canvas_height - self.display_image.height()) // 2)
            
            # Show image
            self.image_id = self.canvas.create_image(x_position, y_position, anchor=tk.NW, image=self.display_image)
            
            # Draw grid if enabled
            if self.show_grid:
                self.draw_grid()
            
            # Display image dimensions and grid info in bottom-right corner
            info_text = f"Dimensions: 1.00m × {self.image_height_m:.2f}m | "
            info_text += f"Grid: {self.grid_size:.2f}m | "
            info_text += f"Grid: {'On' if self.show_grid else 'Off'} | "
            info_text += f"Zoom: {int(self.zoom_factor * 100)}%"
            
            self.canvas.create_text(
                canvas_width - 10, canvas_height - 10,
                text=info_text,
                anchor=tk.SE,
                fill="#00FFFF",
                font=('Arial', 10, 'bold')
            )
            
            # Configure scrollbars for the image
            self.canvas.config(scrollregion=(0, 0, x_position * 2 + self.display_image.width(), 
                                           y_position * 2 + self.display_image.height()))
    
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
            "Image Viewer with Grid v1.1\n\n"
            "A simple application for viewing images in a folder with grid measurement support.\n\n"
            "Features:\n"
            "- Browse through all images in a folder\n"
            "- Zoom in/out and pan around images\n"
            "- Keyboard shortcuts for navigation\n"
            "- Support for common image formats\n"
            "- Overlay grid with customizable size\n"
            "- Set image height for accurate measurements (width fixed at 1m)\n\n"
            "Keyboard Shortcuts:\n"
            "- Left/Right arrows: Navigate images\n"
            "- +/-: Zoom in/out\n"
            "- r: Reset zoom\n"
            "- g: Toggle grid\n"
            "- h: Set image height\n"
            "- s: Adjust grid size\n\n"
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
    
    def draw_grid(self):
        """Draw a grid overlay on the canvas using the physical dimensions"""
        if not hasattr(self, 'display_image'):
            return
            
        # Get image dimensions on canvas
        img_width = self.display_image.width()
        img_height = self.display_image.height()
        
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
        
        # Get canvas position of image
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        x_position = max(0, (canvas_width - img_width) // 2)
        y_position = max(0, (canvas_height - img_height) // 2)
        
        # Draw vertical grid lines
        x = x_position
        line_count = 0
        while x <= x_position + img_width:
            # Make the 0.5m and 1.0m lines more visible
            if abs(line_count * self.grid_size % 0.5) < 0.001:  # Every 0.5m
                width = 2
                fill_color = self.grid_color
            elif abs(line_count * self.grid_size % 0.1) < 0.001:  # Every 0.1m
                width = 1
                fill_color = self.grid_color
            else:
                width = 0.5
                fill_color = "#AAAAAA"  # Light gray
                
            self.canvas.create_line(
                x, y_position, 
                x, y_position + img_height, 
                fill=fill_color, 
                width=width, 
                dash=(4, 4) if width < 2 else None
            )
            
            # Add label every 0.5m
            if abs(line_count * self.grid_size % 0.5) < 0.001:
                self.canvas.create_text(
                    x, y_position - 5,
                    text=f"{line_count * self.grid_size:.1f}m",
                    anchor=tk.S,
                    fill=self.grid_color,
                    font=('Arial', 8)
                )
            
            x += grid_spacing_x
            line_count += 1
        
        # Draw horizontal grid lines
        y = y_position
        line_count = 0
        while y <= y_position + img_height:
            # Make the 0.5m and 1.0m lines more visible
            if abs(line_count * self.grid_size % 0.5) < 0.001:  # Every 0.5m
                width = 2
                fill_color = self.grid_color
            elif abs(line_count * self.grid_size % 0.1) < 0.001:  # Every 0.1m
                width = 1
                fill_color = self.grid_color
            else:
                width = 0.5
                fill_color = "#AAAAAA"  # Light gray
                
            self.canvas.create_line(
                x_position, y, 
                x_position + img_width, y, 
                fill=fill_color, 
                width=width, 
                dash=(4, 4) if width < 2 else None
            )
            
            # Add label every 0.5m
            if abs(line_count * self.grid_size % 0.5) < 0.001:
                self.canvas.create_text(
                    x_position - 5, y,
                    text=f"{line_count * self.grid_size:.1f}m",
                    anchor=tk.E,
                    fill=self.grid_color,
                    font=('Arial', 8)
                )
            
            y += grid_spacing_y
            line_count += 1

def main():
    app = ImageViewerApp()
    app.mainloop()

if __name__ == "__main__":
    main() 