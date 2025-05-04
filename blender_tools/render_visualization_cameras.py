import bpy
import os
import bmesh
from mathutils import Vector

# Include the list_collections_detailed function directly in this file
def list_collections_detailed():
    """
    List all collections in the current Blender scene with detailed information,
    create bounding boxes around each collection, and add orthographic cameras
    for each axis.
    """
    scene = bpy.context.scene
    
    print("\n=== COLLECTIONS IN SCENE ===")
    
    # Get the master collection
    master_collection = scene.collection
    print(f"Master collection: {master_collection.name} with {len(master_collection.objects)} direct objects")
    print(f"Master collection has {len(master_collection.children)} child collections")
    
    # Create or get the visualization collection
    if "Collection_Visualization" not in bpy.data.collections:
        viz_collection = bpy.data.collections.new("Collection_Visualization")
        bpy.context.scene.collection.children.link(viz_collection)
        print("Created new Collection_Visualization")
    else:
        viz_collection = bpy.data.collections["Collection_Visualization"]
        print("Using existing Collection_Visualization")
    
    # Create or get the bounding boxes collection
    if "BoundingBoxes" not in bpy.data.collections:
        bbox_collection = bpy.data.collections.new("BoundingBoxes")
        viz_collection.children.link(bbox_collection)
        print("Created new BoundingBoxes collection")
    else:
        bbox_collection = bpy.data.collections["BoundingBoxes"]
        print("Using existing BoundingBoxes collection")
    
    # Create or get the cameras collection
    if "OrthoCameras" not in bpy.data.collections:
        camera_collection = bpy.data.collections.new("OrthoCameras")
        viz_collection.children.link(camera_collection)
        print("Created new OrthoCameras collection")
    else:
        camera_collection = bpy.data.collections["OrthoCameras"]
        print("Using existing OrthoCameras collection")
    
    # Function to recursively print collections with details
    def print_collection_details(collection, indent=0):
        prefix = "  " * indent
        print(f"{prefix}Collection: {collection.name}")
        print(f"{prefix}  - Objects: {len(collection.objects)}")
        print(f"{prefix}  - Visible: {'Yes' if not collection.hide_viewport else 'No'}")
        print(f"{prefix}  - Renderable: {'Yes' if not collection.hide_render else 'No'}")
        
        # Create bounding box and cameras for this collection
        bbox_obj = create_bounding_box(collection, bbox_collection)
        
        # If a bounding box was created, add cameras
        if bbox_obj:
            create_orthographic_cameras(collection, bbox_obj, camera_collection)
        
        # List objects in this collection
        if len(collection.objects) > 0:
            print(f"{prefix}  - Object list:")
            for obj in collection.objects:
                print(f"{prefix}    • {obj.name} ({obj.type})")
        
        # Process child collections
        for child in collection.children:
            print_collection_details(child, indent + 1)
    
    # Print the hierarchy with details
    print_collection_details(master_collection)

def create_bounding_box(collection, bbox_collection):
    """Create a wireframe bounding box around all objects in the collection."""
    print(f"Attempting to create bounding box for collection: {collection.name}")
    print(f"  Collection has {len(collection.objects)} objects")
    
    if not collection.objects:
        print(f"  Skipping empty collection: {collection.name}")
        return None  # Skip empty collections
    
    # Calculate bounds
    min_co = Vector((float('inf'), float('inf'), float('inf')))
    max_co = Vector((float('-inf'), float('-inf'), float('-inf')))
    
    # Check if collection has any visible objects
    has_visible_objects = False
    
    for obj in collection.objects:
        if obj.type == 'MESH' and not obj.hide_viewport:
            has_visible_objects = True
            print(f"  Found visible mesh: {obj.name}")
            
            # Get object's world matrix
            world_matrix = obj.matrix_world
            
            # Get object's bounding box in world space
            for v in obj.bound_box:
                world_v = world_matrix @ Vector(v)
                
                # Update min and max coordinates
                min_co.x = min(min_co.x, world_v.x)
                min_co.y = min(min_co.y, world_v.y)
                min_co.z = min(min_co.z, world_v.z)
                
                max_co.x = max(max_co.x, world_v.x)
                max_co.y = max(max_co.y, world_v.y)
                max_co.z = max(max_co.z, world_v.z)
    
    if not has_visible_objects:
        print(f"  No visible mesh objects in collection: {collection.name}")
        return None
    
    # Create bounding box mesh
    bbox_name = f"BBox_{collection.name}"
    
    # Remove existing bounding box if it exists
    if bbox_name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[bbox_name])
    
    # Create new mesh and object
    mesh = bpy.data.meshes.new(bbox_name)
    bbox_obj = bpy.data.objects.new(bbox_name, mesh)
    
    # Link to scene and then to the bounding box collection
    bpy.context.scene.collection.objects.link(bbox_obj)
    bpy.context.scene.collection.objects.unlink(bbox_obj)
    bbox_collection.objects.link(bbox_obj)
    
    # Create bmesh
    bm = bmesh.new()
    
    # Create vertices
    v1 = bm.verts.new((min_co.x, min_co.y, min_co.z))
    v2 = bm.verts.new((max_co.x, min_co.y, min_co.z))
    v3 = bm.verts.new((max_co.x, max_co.y, min_co.z))
    v4 = bm.verts.new((min_co.x, max_co.y, min_co.z))
    v5 = bm.verts.new((min_co.x, min_co.y, max_co.z))
    v6 = bm.verts.new((max_co.x, min_co.y, max_co.z))
    v7 = bm.verts.new((max_co.x, max_co.y, max_co.z))
    v8 = bm.verts.new((min_co.x, max_co.y, max_co.z))
    
    # Create edges
    bm.edges.new((v1, v2))
    bm.edges.new((v2, v3))
    bm.edges.new((v3, v4))
    bm.edges.new((v4, v1))
    
    bm.edges.new((v5, v6))
    bm.edges.new((v6, v7))
    bm.edges.new((v7, v8))
    bm.edges.new((v8, v5))
    
    bm.edges.new((v1, v5))
    bm.edges.new((v2, v6))
    bm.edges.new((v3, v7))
    bm.edges.new((v4, v8))
    
    # Update mesh
    bm.to_mesh(mesh)
    bm.free()
    
    # Set display properties
    bbox_obj.display_type = 'WIRE'
    bbox_obj.show_in_front = True
    
    # Create a material for the bounding box with a unique color based on collection name
    if f"BBox_Material_{collection.name}" not in bpy.data.materials:
        mat = bpy.data.materials.new(f"BBox_Material_{collection.name}")
        
        # Generate a unique color based on collection name hash
        import hashlib
        hash_val = int(hashlib.md5(collection.name.encode()).hexdigest(), 16)
        r = ((hash_val & 0xFF0000) >> 16) / 255.0
        g = ((hash_val & 0x00FF00) >> 8) / 255.0
        b = (hash_val & 0x0000FF) / 255.0
        
        mat.diffuse_color = (r, g, b, 1.0)
        bbox_obj.data.materials.append(mat)
    else:
        bbox_obj.data.materials.append(bpy.data.materials[f"BBox_Material_{collection.name}"])
    
    # Store the bounding box dimensions as custom properties
    bbox_obj["min_x"] = min_co.x
    bbox_obj["min_y"] = min_co.y
    bbox_obj["min_z"] = min_co.z
    bbox_obj["max_x"] = max_co.x
    bbox_obj["max_y"] = max_co.y
    bbox_obj["max_z"] = max_co.z
    bbox_obj["center_x"] = (min_co.x + max_co.x) / 2
    bbox_obj["center_y"] = (min_co.y + max_co.y) / 2
    bbox_obj["center_z"] = (min_co.z + max_co.z) / 2
    bbox_obj["width"] = max_co.x - min_co.x
    bbox_obj["height"] = max_co.y - min_co.y
    bbox_obj["depth"] = max_co.z - min_co.z
    
    print(f"  Created bounding box for collection: {collection.name}")
    return bbox_obj

def create_orthographic_cameras(collection, bbox_obj, camera_collection):
    """Create orthographic cameras for X, Y, and Z views of the bounding box."""
    # Get bounding box dimensions
    min_x = bbox_obj["min_x"]
    min_y = bbox_obj["min_y"]
    min_z = bbox_obj["min_z"]
    max_x = bbox_obj["max_x"]
    max_y = bbox_obj["max_y"]
    max_z = bbox_obj["max_z"]
    center_x = bbox_obj["center_x"]
    center_y = bbox_obj["center_y"]
    center_z = bbox_obj["center_z"]
    width = bbox_obj["width"]
    height = bbox_obj["height"]
    depth = bbox_obj["depth"]
    
    # Calculate camera distance (add some padding)
    padding = 1.2  # 20% padding
    max_dimension = max(width, height, depth) * padding
    
    # Create a collection for this collection's cameras
    camera_group_name = f"Cameras_{collection.name}"
    if camera_group_name in bpy.data.collections:
        camera_group = bpy.data.collections[camera_group_name]
    else:
        camera_group = bpy.data.collections.new(camera_group_name)
        camera_collection.children.link(camera_group)
    
    # Create X-axis camera (looking from +X to -X)
    create_camera(
        f"Camera_X_{collection.name}",
        (max_x + max_dimension, center_y, center_z),
        (center_x, center_y, center_z),
        max(height, depth),
        camera_group
    )
    
    # Create Y-axis camera (looking from +Y to -Y)
    create_camera(
        f"Camera_Y_{collection.name}",
        (center_x, max_y + max_dimension, center_z),
        (center_x, center_y, center_z),
        max(width, depth),
        camera_group
    )
    
    # Create Z-axis camera (looking from +Z to -Z)
    create_camera(
        f"Camera_Z_{collection.name}",
        (center_x, center_y, max_z + max_dimension),
        (center_x, center_y, center_z),
        max(width, height),
        camera_group
    )
    
    print(f"  Created orthographic cameras for collection: {collection.name}")

def create_camera(name, location, target, ortho_scale, collection):
    """Create an orthographic camera at the specified location, looking at the target."""
    # Remove existing camera if it exists
    if name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[name])
    
    # Create camera data
    cam_data = bpy.data.cameras.new(name)
    cam_data.type = 'ORTHO'  # Set to orthographic
    cam_data.ortho_scale = ortho_scale  # Set the orthographic scale
    
    # Create camera object
    cam_obj = bpy.data.objects.new(name, cam_data)
    cam_obj.location = location
    
    # Point camera at target
    direction = Vector(target) - Vector(location)
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()
    
    # Link to scene temporarily and then to the collection
    bpy.context.scene.collection.objects.link(cam_obj)
    bpy.context.scene.collection.objects.unlink(cam_obj)
    collection.objects.link(cam_obj)
    
    return cam_obj

def render_visualization_cameras(output_dir=None, clear_existing=True):
    """
    Render images from all cameras in the Collection_Visualization collection.
    Ignores collections with 'base' in their name.
    
    Args:
        output_dir (str, optional): Directory to save rendered images.
                                    If None, uses the default Blender output path.
        clear_existing (bool): Whether to remove all existing cameras and bounding boxes before rendering.
    """
    # Clear existing cameras and bounding boxes if requested
    if clear_existing:
        # First, try to remove the entire Collection_Visualization if it exists
        if "Collection_Visualization" in bpy.data.collections:
            viz_collection = bpy.data.collections["Collection_Visualization"]
            
            # Recursively remove all objects from the collection and its children
            def remove_objects_from_collection(collection):
                # Remove all objects in this collection
                for obj in list(collection.objects):  # Create a copy of the list to avoid modification during iteration
                    bpy.data.objects.remove(obj, do_unlink=True)
                
                # Process child collections
                for child in list(collection.children):  # Create a copy of the list
                    remove_objects_from_collection(child)
                    # After removing all objects, remove the child collection
                    bpy.data.collections.remove(child)
            
            # Remove all objects and child collections
            remove_objects_from_collection(viz_collection)
            
            # Now remove the visualization collection itself
            bpy.data.collections.remove(viz_collection)
            print("Removed Collection_Visualization and all its contents")
        
        # As a fallback, also look for any stray bounding boxes or cameras that might not be in the collection
        # Remove bounding boxes (objects with names starting with "BBox_")
        bbox_to_remove = [obj for obj in bpy.data.objects if obj.name.startswith("BBox_")]
        for bbox in bbox_to_remove:
            print(f"Removing stray bounding box: {bbox.name}")
            bpy.data.objects.remove(bbox, do_unlink=True)
        
        # Remove cameras
        cameras_to_remove = [obj for obj in bpy.data.objects if obj.type == 'CAMERA' and obj.name.startswith(("Camera_X_", "Camera_Y_", "Camera_Z_"))]
        for camera in cameras_to_remove:
            print(f"Removing stray camera: {camera.name}")
            bpy.data.objects.remove(camera, do_unlink=True)
        
        # Clean up camera data blocks
        for camera in list(bpy.data.cameras):
            if camera.name.startswith(("Camera_X_", "Camera_Y_", "Camera_Z_")):
                bpy.data.cameras.remove(camera)
        
        # Clean up materials created for bounding boxes
        for material in list(bpy.data.materials):
            if material.name.startswith("BBox_Material_"):
                bpy.data.materials.remove(material)
        
        print(f"Cleanup complete: removed {len(bbox_to_remove)} stray bounding boxes and {len(cameras_to_remove)} stray cameras")
    
    # Create visualization collection structure
    print("\nCreating visualization collection structure...")
    
    # Create or get the visualization collection
    if "Collection_Visualization" not in bpy.data.collections:
        viz_collection = bpy.data.collections.new("Collection_Visualization")
        bpy.context.scene.collection.children.link(viz_collection)
    else:
        viz_collection = bpy.data.collections["Collection_Visualization"]
    
    # Create or get the bounding boxes collection
    if "BoundingBoxes" not in bpy.data.collections:
        bbox_collection = bpy.data.collections.new("BoundingBoxes")
        viz_collection.children.link(bbox_collection)
    else:
        bbox_collection = bpy.data.collections["BoundingBoxes"]
    
    # Create or get the cameras collection
    if "OrthoCameras" not in bpy.data.collections:
        camera_collection = bpy.data.collections.new("OrthoCameras")
        viz_collection.children.link(camera_collection)
    else:
        camera_collection = bpy.data.collections["OrthoCameras"]
    
    # Create bounding boxes for all collections with mesh objects
    print("Creating bounding boxes for collections...")
    created_bboxes = []
    
    def process_collection_for_bbox(collection):
        # Skip collections with 'base' in their name
        if 'base' in collection.name.lower():
            print(f"Skipping collection: {collection.name} (contains 'base')")
            return
        
        # Create bounding box for this collection
        bbox_obj = create_bounding_box(collection, bbox_collection)
        if bbox_obj:
            created_bboxes.append((collection, bbox_obj))
        
        # Process child collections
        for child in collection.children:
            process_collection_for_bbox(child)
    
    # Process all collections starting from the scene collection
    process_collection_for_bbox(bpy.context.scene.collection)
    
    print(f"Created {len(created_bboxes)} bounding boxes")
    
    # Create cameras for each bounding box
    print("Creating cameras for bounding boxes...")
    for collection, bbox_obj in created_bboxes:
        # Create a collection for this collection's cameras
        camera_group_name = f"Cameras_{collection.name}"
        if camera_group_name in bpy.data.collections:
            camera_group = bpy.data.collections[camera_group_name]
        else:
            camera_group = bpy.data.collections.new(camera_group_name)
            camera_collection.children.link(camera_group)
        
        # Get bounding box dimensions
        min_x = bbox_obj["min_x"]
        min_y = bbox_obj["min_y"]
        min_z = bbox_obj["min_z"]
        max_x = bbox_obj["max_x"]
        max_y = bbox_obj["max_y"]
        max_z = bbox_obj["max_z"]
        center_x = bbox_obj["center_x"]
        center_y = bbox_obj["center_y"]
        center_z = bbox_obj["center_z"]
        width = bbox_obj["width"]
        height = bbox_obj["height"]
        depth = bbox_obj["depth"]
        
        # Calculate camera distance (add some padding)
        padding = 1.2  # 20% padding
        max_dimension = max(width, height, depth) * padding
        
        # Create X-axis camera (looking from +X to -X)
        create_camera(
            f"Camera_X_{collection.name}",
            (max_x + max_dimension, center_y, center_z),
            (center_x, center_y, center_z),
            max(height, depth),
            camera_group
        )
        
        # Create Y-axis camera (looking from +Y to -Y)
        create_camera(
            f"Camera_Y_{collection.name}",
            (center_x, max_y + max_dimension, center_z),
            (center_x, center_y, center_z),
            max(width, depth),
            camera_group
        )
        
        # Create Z-axis camera (looking from +Z to -Z)
        create_camera(
            f"Camera_Z_{collection.name}",
            (center_x, center_y, max_z + max_dimension),
            (center_x, center_y, center_z),
            max(width, height),
            camera_group
        )
        
        print(f"Created cameras for collection: {collection.name}")
    
    # Find all cameras in the visualization collection and its children
    cameras = []
    
    def find_cameras_in_collection(collection):
        # Skip collections with 'base' in their name
        if 'base' in collection.name.lower():
            return
            
        # Add cameras directly in this collection
        for obj in collection.objects:
            if obj.type == 'CAMERA':
                cameras.append(obj)
                print(f"Found camera: {obj.name} in collection: {collection.name}")
        
        # Recursively check child collections
        for child in collection.children:
            find_cameras_in_collection(child)
    
    find_cameras_in_collection(viz_collection)
    
    if not cameras:
        print("No cameras found in Collection_Visualization or its child collections")
        return
    
    print(f"Found {len(cameras)} cameras to render")
    
    # Set up output directory
    if output_dir is None:
        output_dir = bpy.context.scene.render.filepath
    else:
        # Ensure the directory exists
        os.makedirs(output_dir, exist_ok=True)
    
    # Store original render settings
    original_filepath = bpy.context.scene.render.filepath
    original_camera = bpy.context.scene.camera
    
    # Render each camera
    for i, camera in enumerate(cameras):
        print(f"Rendering camera {i+1}/{len(cameras)}: {camera.name}")
        
        # Set the active camera
        bpy.context.scene.camera = camera
        
        # Set output path for this camera
        camera_filename = f"{camera.name}.png"
        bpy.context.scene.render.filepath = os.path.join(output_dir, camera_filename)
        
        # Render the image
        bpy.ops.render.render(write_still=True)
    
    # Restore original settings
    bpy.context.scene.render.filepath = original_filepath
    bpy.context.scene.camera = original_camera
    
    print(f"Rendering complete. {len(cameras)} images saved to {output_dir}")

if __name__ == "__main__":
    # Example usage: Render to a specific directory
    # Change this path to your desired output location
    output_directory = "//renders/visualization_cameras/"
    render_visualization_cameras(output_directory, clear_existing=True) 