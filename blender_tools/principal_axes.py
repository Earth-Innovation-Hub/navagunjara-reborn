import bpy
import numpy as np
from mathutils import Matrix, Vector, kdtree
import bmesh
import math


def convert_to_mesh(obj, target_collection=None):
    """Convert an object to mesh if possible.
    
    Args:
        obj: The object to convert
        target_collection: Collection to add the converted object to (defaults to obj's collection)
        
    Returns:
        The converted mesh object, or the original if already a mesh, or None if conversion failed
    """
    # If object is already a mesh, return it directly
    if obj.type == 'MESH':
        return obj
    
    if obj.type in {'CURVE', 'SURFACE', 'META', 'FONT'}:
        try:
            # Determine target collection (use object's collection if not specified)
            if target_collection is None:
                # Use the first collection the object is in (there should be at least one)
                if obj.users_collection:
                    target_collection = obj.users_collection[0]
                else:
                    # Fallback to scene collection if no collection found
                    target_collection = bpy.context.scene.collection
            
            # Create a copy of the original object
            obj_copy = obj.copy()
            obj_copy.data = obj.data.copy()
            
            # Link the copy to the target collection
            target_collection.objects.link(obj_copy)
            
            # Select only the copy
            bpy.ops.object.select_all(action='DESELECT')
            obj_copy.select_set(True)
            bpy.context.view_layer.objects.active = obj_copy
            
            # Convert to mesh
            bpy.ops.object.convert(target='MESH')
            
            return obj_copy
            
        except Exception as e:
            print(f"  Error converting {obj.name} to mesh: {e}")
            # Clean up partial objects if creation failed
            if 'obj_copy' in locals() and obj_copy:
                bpy.data.objects.remove(obj_copy, do_unlink=True)
            return None
    
    return None  # Object can't be converted to mesh


def get_mesh_volume(obj):
    """Calculate the volume of a mesh object."""
    # Create a new bmesh
    bm = bmesh.new()
    
    # Fill bmesh with mesh data (in local space)
    bm.from_mesh(obj.data)
    
    # Transform bmesh to world space
    bm.transform(obj.matrix_world)
    
    # Calculate volume
    volume = abs(bm.calc_volume())
    
    # Free the bmesh
    bm.free()
    
    return volume


def create_volume_fiducial(name, location, volume, target_collection):
    """Create a spherical marker at the given location with size proportional to volume."""
    # Calculate radius based on volume (using cube root for proportional scaling)
    # Use a scale factor to make the sphere a reasonable size relative to the object
    scale_factor = 0.1
    radius = scale_factor * math.pow(volume, 1/3)
    
    # Create UV sphere - Using only parameters compatible with Blender 4.4
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=radius, 
        segments=16, 
        location=location
    )
    
    # Get the created sphere
    sphere = bpy.context.active_object
    sphere.name = name
    
    # Add a material to make it stand out
    mat = bpy.data.materials.new(f"{name}_material")
    mat.diffuse_color = (1.0, 0.3, 0.3, 0.7)  # Red, semi-transparent
    mat.blend_method = 'BLEND'
    
    if sphere.data.materials:
        sphere.data.materials[0] = mat
    else:
        sphere.data.materials.append(mat)
    
    # Move object to target collection
    move_to_collection(sphere, target_collection)
    
    return sphere


def tetrahedron_volume(v1, v2, v3, v4):
    """Calculate the volume of a tetrahedron formed by 4 vertices."""
    return abs(np.dot(np.cross(v2 - v1, v3 - v1), v4 - v1)) / 6.0


def get_density_weights(bm, method='vertex_edge', radius=0.1):
    """Calculate density weights for vertices based on vertex/edge concentrations.
    
    Args:
        bm: BMesh object to analyze
        method: Weighting method ('vertex_edge', 'vertex', or 'edge')
        radius: Radius for local density sampling
        
    Returns:
        List of weights for each vertex
    """
    weights = []
    
    # Create a KDTree for vertex spatial lookup
    size = len(bm.verts)
    kd = kdtree.KDTree(size)
    
    # Insert vertices
    for i, v in enumerate(bm.verts):
        kd.insert(v.co, i)
    kd.balance()
    
    # Calculate edge density if needed
    edge_counts = None
    if method in ['vertex_edge', 'edge']:
        # Count number of edges connected to each vertex
        edge_counts = [len(v.link_edges) for v in bm.verts]
        
        if method == 'edge':
            return edge_counts
    
    # Calculate vertex density and combine with edge density
    for i, v in enumerate(bm.verts):
        # Find vertices within radius
        nearby_verts = [index for (co, index, dist) in kd.find_range(v.co, radius)]
        
        if method == 'vertex':
            # Pure vertex density - just count nearby vertices
            weights.append(len(nearby_verts))
        elif method == 'vertex_edge':
            # Combined vertex and edge density
            edge_factor = edge_counts[i] if edge_counts else 1
            weights.append(len(nearby_verts) * edge_factor)
    
    # Normalize weights to have mean of 1.0
    if weights:
        avg_weight = sum(weights) / len(weights)
        if avg_weight > 0:
            weights = [w / avg_weight for w in weights]
    
    return weights


def get_principal_axes_density_weighted(obj, density_method='vertex_edge', radius_factor=0.05):
    """Calculate principal axes using vertex and edge density weighting.
    
    Args:
        obj: The mesh object to analyze
        density_method: Method for density calculation ('vertex_edge', 'vertex', or 'edge')
        radius_factor: Relative radius for density sampling, as a fraction of object size
        
    Returns:
        Tuple of (center_of_mass, rotation_matrix) or (None, None) if calculation fails
    """
    # Create bmesh
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    
    # Transform bmesh to world space
    bm.transform(obj.matrix_world)
    
    # Ensure triangulated faces
    bmesh.ops.triangulate(bm, faces=bm.faces)
    
    if len(bm.verts) == 0:
        bm.free()
        return None, None
    
    # Determine an appropriate radius for density calculation
    # Get object dimensions
    verts = np.array([[v.co.x, v.co.y, v.co.z] for v in bm.verts])
    min_coords = np.min(verts, axis=0)
    max_coords = np.max(verts, axis=0)
    dimensions = max_coords - min_coords
    object_size = np.linalg.norm(dimensions)
    
    # Set radius as a fraction of object size
    radius = object_size * radius_factor
    
    # Calculate density weights
    print(f"  Calculating {density_method} density with radius {radius:.3f}")
    weights = get_density_weights(bm, method=density_method, radius=radius)
    
    # Calculate weighted center of mass
    total_weight = sum(weights)
    if total_weight > 0:
        center_of_mass = np.zeros(3)
        for i, v in enumerate(bm.verts):
            center_of_mass += np.array([v.co.x, v.co.y, v.co.z]) * weights[i]
        center_of_mass /= total_weight
    else:
        # Fallback to simple average if weighting fails
        center_of_mass = np.mean(verts, axis=0)
    
    # Calculate weighted covariance matrix
    covariance_matrix = np.zeros((3, 3))
    
    if total_weight > 0:
        for i, v in enumerate(bm.verts):
            # Vector from center of mass to vertex
            d = np.array([v.co.x, v.co.y, v.co.z]) - center_of_mass
            
            # Weighted contribution to covariance matrix
            covariance_matrix += weights[i] * np.outer(d, d)
        
        # Normalize
        covariance_matrix /= total_weight
    
    # Handle potential numerical issues
    if np.isnan(covariance_matrix).any() or np.isinf(covariance_matrix).any():
        print("  Warning: Numerical issues in density-weighted calculation. Falling back to volume method.")
        bm.free()
        return get_principal_axes_volume(obj)
    
    try:
        # Get eigenvalues and eigenvectors
        eigenvalues, eigenvectors = np.linalg.eigh(covariance_matrix)
        
        # Sort eigenvectors by eigenvalues in descending order (largest variance first)
        idx = eigenvalues.argsort()[::-1]
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx]
        
        # Reorder eigenvectors to align:
        # Z axis with longest dimension (highest eigenvalue) - eigenvectors[:,0]
        # X axis with middle dimension (middle eigenvalue) - eigenvectors[:,1]
        # Y axis with shortest dimension (lowest eigenvalue) - eigenvectors[:,2]
        reordered_eigenvectors = np.column_stack([
            eigenvectors[:, 1],  # X axis = middle eigenvector
            eigenvectors[:, 2],  # Y axis = smallest eigenvector
            eigenvectors[:, 0]   # Z axis = largest eigenvector
        ])
        
        # Ensure right-handed coordinate system
        if np.linalg.det(reordered_eigenvectors) < 0:
            # Flip Y axis to maintain right-handed system
            reordered_eigenvectors[:, 1] = -reordered_eigenvectors[:, 1]
        
        # Clean up
        bm.free()
        
        return Vector(center_of_mass), Matrix(reordered_eigenvectors.T).to_4x4()
    
    except np.linalg.LinAlgError:
        print("  Warning: Linear algebra error in density method. Falling back to volume method.")
        bm.free()
        return get_principal_axes_volume(obj)


def get_principal_axes_volume(obj):
    """Calculate principal axes based on volume distribution using tetrahedron method.
    This is more accurate for solid objects than surface-based methods."""
    # Create bmesh
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    
    # Transform bmesh to world space
    bm.transform(obj.matrix_world)
    
    # Ensure triangulated faces
    bmesh.ops.triangulate(bm, faces=bm.faces)
    
    # First pass: Calculate approximate center of mass
    # This is used as a reference point for tetrahedra
    simple_center = Vector((0, 0, 0))
    for v in bm.verts:
        simple_center += v.co
    
    if len(bm.verts) > 0:
        simple_center /= len(bm.verts)
    else:
        bm.free()
        return None, None
        
    # Second pass: Calculate center of mass and inertia tensor using tetrahedron method
    total_volume = 0.0
    center_of_mass = np.zeros(3)
    inertia_tensor = np.zeros((3, 3))
    
    # Process each triangular face
    for face in bm.faces:
        if len(face.verts) != 3:
            continue  # Skip non-triangular faces (should be none after triangulation)
        
        # Get vertices as numpy arrays
        v1 = np.array([face.verts[0].co[0], face.verts[0].co[1], face.verts[0].co[2]])
        v2 = np.array([face.verts[1].co[0], face.verts[1].co[1], face.verts[1].co[2]])
        v3 = np.array([face.verts[2].co[0], face.verts[2].co[1], face.verts[2].co[2]])
        v0 = np.array([simple_center[0], simple_center[1], simple_center[2]])
        
        # Calculate tetrahedron volume
        vol = tetrahedron_volume(v0, v1, v2, v3)
        
        if vol > 0:
            # Tetrahedron centroid (average of the 4 vertices)
            tetra_center = (v0 + v1 + v2 + v3) / 4.0
            
            # Accumulate weighted center
            center_of_mass += tetra_center * vol
            total_volume += vol
            
            # Compute contribution to inertia tensor
            # For each vertex in the tetrahedron
            for v in [v0, v1, v2, v3]:
                # Distance from approximated center of mass
                dx = v - tetra_center
                
                # Contribution to the inertia tensor (diagonal and off-diagonal terms)
                # This is a simplified inertia tensor calculation that works for PCA
                sq_dist = np.sum(dx**2)
                inertia_tensor[0, 0] += (sq_dist - dx[0]**2) * vol / 4.0
                inertia_tensor[1, 1] += (sq_dist - dx[1]**2) * vol / 4.0
                inertia_tensor[2, 2] += (sq_dist - dx[2]**2) * vol / 4.0
                
                inertia_tensor[0, 1] -= dx[0] * dx[1] * vol / 4.0
                inertia_tensor[0, 2] -= dx[0] * dx[2] * vol / 4.0
                inertia_tensor[1, 2] -= dx[1] * dx[2] * vol / 4.0
    
    # Mirror the off-diagonal terms (the tensor is symmetric)
    inertia_tensor[1, 0] = inertia_tensor[0, 1]
    inertia_tensor[2, 0] = inertia_tensor[0, 2]
    inertia_tensor[2, 1] = inertia_tensor[1, 2]
    
    # Finalize center of mass
    if total_volume > 0:
        center_of_mass /= total_volume
    else:
        # Fallback if volume calculation failed
        print("  Warning: Volume calculation failed. Using simple vertex average.")
        center_of_mass = np.array([simple_center[0], simple_center[1], simple_center[2]])
    
    # Handle potential numerical issues
    if np.isnan(inertia_tensor).any() or np.isinf(inertia_tensor).any() or total_volume <= 0:
        print("  Warning: Numerical issues in inertia tensor calculation. Falling back to simpler method.")
        bm.free()
        return get_principal_axes_improved(obj)
    
    try:
        # Get eigenvalues and eigenvectors of the inertia tensor
        eigenvalues, eigenvectors = np.linalg.eigh(inertia_tensor)
        
        # Sort eigenvectors by eigenvalues in ascending order
        # For inertia tensor, smaller eigenvalues correspond to axes with larger spatial extent
        idx = eigenvalues.argsort()
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx]
        
        # Reorder eigenvectors to align:
        # Z axis with longest dimension (smallest eigenvalue in inertia tensor) - eigenvectors[:,0]
        # X axis with middle dimension - eigenvectors[:,1]
        # Y axis with shortest dimension - eigenvectors[:,2]
        reordered_eigenvectors = np.column_stack([
            eigenvectors[:, 1],  # X axis = middle eigenvector
            eigenvectors[:, 2],  # Y axis = smallest eigenvector (largest eigenvalue)
            eigenvectors[:, 0]   # Z axis = largest eigenvector (smallest eigenvalue)
        ])
        
        # Ensure right-handed coordinate system
        if np.linalg.det(reordered_eigenvectors) < 0:
            # Flip Y axis to maintain right-handed system
            reordered_eigenvectors[:, 1] = -reordered_eigenvectors[:, 1]
        
        # Clean up
        bm.free()
        
        return Vector(center_of_mass), Matrix(reordered_eigenvectors.T).to_4x4()
    
    except np.linalg.LinAlgError:
        print("  Warning: Linear algebra error in volume-based method. Falling back to area-based method.")
        bm.free()
        return get_principal_axes_improved(obj)


def get_principal_axes_improved(obj):
    """Calculate principal axes for a mesh object using geometrically correct PCA.
    This method accounts for face areas when computing the covariance matrix."""
    # Create bmesh
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    
    # Transform bmesh to world space
    bm.transform(obj.matrix_world)
    
    # Ensure triangulated faces
    bmesh.ops.triangulate(bm, faces=bm.faces)
    
    # Calculate center of mass weighted by face areas
    total_area = 0.0
    weighted_center = np.zeros(3)
    
    for face in bm.faces:
        # Get vertices in world space
        vertices = [v.co for v in face.verts]
        
        # Calculate face area
        if len(vertices) >= 3:
            # For triangle, get area directly
            area = face.calc_area()
            
            # Calculate face center
            face_center = sum((v.co for v in face.verts), Vector((0,0,0))) / len(face.verts)
            
            # Accumulate weighted center
            weighted_center += np.array([face_center[0], face_center[1], face_center[2]]) * area
            total_area += area
    
    if total_area > 0:
        center_of_mass = weighted_center / total_area
    else:
        # Fallback to simple mean if no faces with area
        verts = np.array([[v.co.x, v.co.y, v.co.z] for v in bm.verts])
        center_of_mass = np.mean(verts, axis=0)
    
    # Create covariance matrix using triangular faces
    covariance_matrix = np.zeros((3, 3))
    
    for face in bm.faces:
        if len(face.verts) >= 3:
            # Get vertices as numpy arrays
            verts = [np.array([v.co[0], v.co[1], v.co[2]]) for v in face.verts]
            
            # Calculate centroid of the face
            face_center = sum(verts) / len(verts)
            
            # Calculate face area
            area = face.calc_area()
            
            # Contribution to covariance matrix - weighted by face area
            for v in verts:
                # Vector from center of mass to vertex
                d = v - center_of_mass
                
                # Outer product contribution weighted by area/nvertices
                weight = area / len(verts)
                covariance_matrix += weight * np.outer(d, d)
    
    # Handle potential numerical issues
    if np.isnan(covariance_matrix).any() or np.isinf(covariance_matrix).any():
        print("  Warning: Numerical issues in covariance calculation. Falling back to simpler method.")
        bm.free()
        return get_principal_axes_simple(obj)
    
    try:
        # Get eigenvalues and eigenvectors
        eigenvalues, eigenvectors = np.linalg.eigh(covariance_matrix)
        
        # Sort eigenvectors by eigenvalues in descending order
        idx = eigenvalues.argsort()[::-1]
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx]
        
        # Reorder eigenvectors to align:
        # Z axis with longest dimension (highest eigenvalue) - eigenvectors[:,0]
        # X axis with middle dimension (middle eigenvalue) - eigenvectors[:,1]
        # Y axis with shortest dimension (lowest eigenvalue) - eigenvectors[:,2]
        
        # Create reordered matrix: [middle, smallest, largest]
        # so that Z = largest, X = middle, Y = smallest
        reordered_eigenvectors = np.column_stack([
            eigenvectors[:, 1],  # X axis = middle eigenvector
            eigenvectors[:, 2],  # Y axis = smallest eigenvector
            eigenvectors[:, 0]   # Z axis = largest eigenvector
        ])
        
        # Ensure right-handed coordinate system
        if np.linalg.det(reordered_eigenvectors) < 0:
            # Flip Y axis to maintain right-handed system
            reordered_eigenvectors[:, 1] = -reordered_eigenvectors[:, 1]
        
        # Clean up
        bm.free()
        
        return Vector(center_of_mass), Matrix(reordered_eigenvectors.T).to_4x4()
    
    except np.linalg.LinAlgError:
        print("  Warning: Linear algebra error. Falling back to simpler method.")
        bm.free()
        return get_principal_axes_simple(obj)


def get_principal_axes_simple(obj):
    """Calculate principal axes using a simpler vertex-based method as fallback."""
    # Get mesh data
    mesh = obj.data
    
    # Get vertices in world space
    vertices = [obj.matrix_world @ v.co for v in mesh.vertices]
    if not vertices:
        return None, None
    
    # Convert to numpy array
    points = np.array(vertices)
    
    # Calculate center of mass
    center_of_mass = np.mean(points, axis=0)
    
    # Center the points
    centered_points = points - center_of_mass
    
    # Calculate covariance matrix
    cov_matrix = np.cov(centered_points, rowvar=False)
    
    # Calculate eigenvectors and eigenvalues
    if np.isnan(cov_matrix).any() or np.isinf(cov_matrix).any():
        return None, None
    
    try:
        eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)
    except np.linalg.LinAlgError:
        return None, None
    
    # Sort eigenvectors by eigenvalues in descending order
    idx = eigenvalues.argsort()[::-1]
    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]
    
    # Reorder eigenvectors to align:
    # Z axis with longest dimension (highest eigenvalue) - eigenvectors[:,0]
    # X axis with middle dimension (middle eigenvalue) - eigenvectors[:,1]
    # Y axis with shortest dimension (lowest eigenvalue) - eigenvectors[:,2]
    
    # Create reordered matrix: [middle, smallest, largest]
    # so that Z = largest, X = middle, Y = smallest
    reordered_eigenvectors = np.column_stack([
        eigenvectors[:, 1],  # X axis = middle eigenvector
        eigenvectors[:, 2],  # Y axis = smallest eigenvector
        eigenvectors[:, 0]   # Z axis = largest eigenvector
    ])
    
    # Ensure the coordinate system is right-handed
    if np.linalg.det(reordered_eigenvectors) < 0:
        # Flip Y axis to maintain right-handed system
        reordered_eigenvectors[:, 1] = -reordered_eigenvectors[:, 1]
    
    return Vector(center_of_mass), Matrix(reordered_eigenvectors.T).to_4x4()


def create_coordinate_frame(name, location, rotation, target_collection):
    """Create an empty object with displayed axes."""
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = 'ARROWS'
    empty.empty_display_size = 1.0
    empty.location = location
    empty.rotation_mode = 'QUATERNION'
    
    # Set rotation from the given matrix
    empty.rotation_quaternion = rotation.to_quaternion()
    
    # Link to the specified collection
    target_collection.objects.link(empty)
    
    return empty


def get_or_create_collection(name, parent=None):
    """Get a collection by name, or create it if it doesn't exist."""
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    
    # Create new collection
    collection = bpy.data.collections.new(name)
    
    # Link the collection to the parent or to the scene
    if parent:
        parent.children.link(collection)
    else:
        bpy.context.scene.collection.children.link(collection)
    
    return collection


def move_to_collection(obj, collection):
    """Move an object to a specific collection, removing it from all others."""
    # Unlink from all current collections
    for coll in obj.users_collection:
        coll.objects.unlink(obj)
    
    # Link to the target collection
    collection.objects.link(obj)


def join_meshes(objects, target_name, target_collection):
    """Join multiple mesh objects into one and place in target collection.
    
    Args:
        objects: List of objects to join
        target_name: Name for the joined result
        target_collection: Collection to place the result in
        
    Returns:
        The joined object or None if joining failed
    """
    if not objects:
        return None
    
    # Ensure we have meshes to join
    if len(objects) == 0:
        return None
    
    # If only one object, no need to join
    if len(objects) == 1:
        obj = objects[0]
        obj.name = target_name
        move_to_collection(obj, target_collection)
        return obj
    
    # Select objects for joining
    bpy.ops.object.select_all(action='DESELECT')
    
    for obj in objects:
        obj.select_set(True)
    
    # Set active object
    bpy.context.view_layer.objects.active = objects[0]
    
    # Join objects
    bpy.ops.object.join()
    
    # Get the joined result
    joined_obj = bpy.context.view_layer.objects.active
    joined_obj.name = target_name
    
    # Move to target collection
    move_to_collection(joined_obj, target_collection)
    
    return joined_obj


def is_valid_object(obj):
    """Check if an object is valid (not deleted) and can be accessed safely."""
    try:
        # Try to access a property that would raise an exception if the object is invalid
        _ = obj.name
        return True
    except ReferenceError:
        return False


def process_collections():
    """Process all collections, join meshes, and display principal axes."""
    # Store original selection and active object
    original_selected_names = [obj.name for obj in bpy.context.selected_objects]
    original_active_name = bpy.context.view_layer.objects.active.name if bpy.context.view_layer.objects.active else None
    
    # Create output collections
    joined_models_collection = get_or_create_collection("Joined Models")
    visualization_collection = get_or_create_collection("Axes and Fiducials")
    
    # Process each collection
    for collection in bpy.data.collections:
        # Skip our output collections
        if collection.name in ["Joined Models", "Axes and Fiducials"]:
            continue
            
        print(f"Processing collection: {collection.name}")
        
        # Get convertible objects
        mesh_objects = []
        original_object_names = []  # Store names instead of references
        temp_objects = []  # Track temporary objects for cleanup in case of errors
        
        for obj in collection.objects:
            # Skip already processed objects
            if obj.name.endswith("_joined"):
                continue
                
            original_object_names.append(obj.name)
            
            if obj.type == 'MESH':
                # Mesh objects can be used directly
                mesh_objects.append(obj)
            elif obj.type in {'CURVE', 'SURFACE', 'META', 'FONT'}:
                # Convert non-mesh objects to mesh
                mesh_obj = convert_to_mesh(obj, collection)  # Keep in same collection temporarily
                if mesh_obj:
                    mesh_objects.append(mesh_obj)
                    temp_objects.append(mesh_obj)  # Track for cleanup if needed
                    print(f"  Converted {obj.name} to mesh")
        
        if len(mesh_objects) < 1:
            print(f"  No suitable objects in collection {collection.name}")
            continue
        
        try:
            # Join the meshes
            joined_name = f"{collection.name}_joined"
            joined_obj = join_meshes(mesh_objects, joined_name, joined_models_collection)
            
            if not joined_obj:
                print(f"  Failed to join objects in {collection.name}")
                continue
                
            print(f"  Created joined mesh: {joined_obj.name}")
            
            # Hide original objects - Use object names to look up objects again
            # This avoids issues with stale references
            for obj_name in original_object_names:
                if obj_name in bpy.data.objects:
                    obj = bpy.data.objects[obj_name]
                    if obj.type != 'MESH' or obj.name not in [mo.name for mo in mesh_objects]:
                        obj.hide_set(True)
                        obj.hide_render = True
            
            # Use density-weighted PCA first, then fallback to volume-based if it fails
            print(f"  Computing density-weighted principal axes for {joined_obj.name}")
            center, rotation_matrix = get_principal_axes_density_weighted(joined_obj, density_method='vertex_edge')
            
            if center is None or rotation_matrix is None:
                print(f"  Could not calculate principal axes for {joined_obj.name}")
                continue
            
            # Create coordinate frame in the visualization collection
            frame_name = f"{collection.name}_axes"
            create_coordinate_frame(frame_name, center, rotation_matrix, visualization_collection)
            print(f"  Created coordinate frame: {frame_name}")
            
            # Calculate volume and create a fiducial sphere in the visualization collection
            volume = get_mesh_volume(joined_obj)
            fiducial_name = f"{collection.name}_fiducial"
            create_volume_fiducial(fiducial_name, center, volume, visualization_collection)
            print(f"  Created volume fiducial: {fiducial_name} (volume: {volume:.3f})")
        
        except ReferenceError as e:
            # Handle the case where an object has been removed
            print(f"  Error: Reference to an object was lost during processing ({e})")
            # Clean up any temporary objects we created
            for temp_obj in temp_objects:
                if is_valid_object(temp_obj):
                    bpy.data.objects.remove(temp_obj, do_unlink=True)
            continue
    
    # Restore original selection using object names
    bpy.ops.object.select_all(action='DESELECT')
    for name in original_selected_names:
        if name in bpy.data.objects:
            obj = bpy.data.objects[name]
            obj.select_set(True)
    
    # Restore active object
    if original_active_name and original_active_name in bpy.data.objects:
        bpy.context.view_layer.objects.active = bpy.data.objects[original_active_name]


if __name__ == "__main__":
    process_collections()
    print("Principal axes analysis complete!") 