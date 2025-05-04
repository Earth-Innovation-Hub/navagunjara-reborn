import bpy
import bmesh
from mathutils import Vector

def list_collections():
    """
    List all collections in the current Blender scene and
    create bounding boxes around each collection.
    """
    scene = bpy.context.scene
    
    print("\n=== COLLECTIONS IN SCENE ===")
    
    # Get the master collection (scene collection)
    master_collection = scene.collection
    
    # Print the master collection
    print(f"Master Collection: {master_collection.name}")
    
    # Function to recursively print collections with proper indentation
    def print_collection_hierarchy(collection, indent=1):
        for child in collection.children:
            print("  " * indent + f"├─ {child.name}")
            create_bounding_box(child)
            print_collection_hierarchy(child, indent + 1)
    
    # Print the hierarchy
    print_collection_hierarchy(master_collection)
    
    # Also print a flat list of all collections
    print("\n=== FLAT LIST OF ALL COLLECTIONS ===")
    for collection in bpy.data.collections:
        print(f"- {collection.name}")

def create_bounding_box(collection):
    """Create a wireframe bounding box around all objects in the collection."""
    if not collection.objects:
        return  # Skip empty collections
    
    # Calculate bounds
    min_co = Vector((float('inf'), float('inf'), float('inf')))
    max_co = Vector((float('-inf'), float('-inf'), float('-inf')))
    
    # Check if collection has any visible objects
    has_visible_objects = False
    
    for obj in collection.objects:
        if obj.type == 'MESH' and not obj.hide_viewport:
            has_visible_objects = True
            
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
        return
    
    # Create bounding box mesh
    bbox_name = f"BBox_{collection.name}"
    
    # Remove existing bounding box if it exists
    if bbox_name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[bbox_name])
    
    # Create new mesh and object
    mesh = bpy.data.meshes.new(bbox_name)
    bbox_obj = bpy.data.objects.new(bbox_name, mesh)
    
    # Link to scene
    bpy.context.scene.collection.objects.link(bbox_obj)
    
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
    
    # Create a material for the bounding box
    if f"BBox_Material_{collection.name}" not in bpy.data.materials:
        mat = bpy.data.materials.new(f"BBox_Material_{collection.name}")
        mat.diffuse_color = (1.0, 0.0, 0.0, 1.0)  # Red color
        bbox_obj.data.materials.append(mat)
    else:
        bbox_obj.data.materials.append(bpy.data.materials[f"BBox_Material_{collection.name}"])
    
    print(f"  Created bounding box for collection: {collection.name}")

# Run the function
list_collections() 