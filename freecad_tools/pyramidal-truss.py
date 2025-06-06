import FreeCAD as App
import Part
import ObjectsFem
import Fem
from FreeCAD import Base
import math

# Open a new document
doc = App.newDocument("PyramidalTrussAnalysis")

# =========== Parameters ===========
base_side_length = 1.0
height = 2.3
beam_radius = 0.05
tolerance = 1e-5
reinforcement_heights = [height/3, 2*height/3]

# =========== Create a pyramidal truss structure directly in FreeCAD ===========
lines = []
base_points = []

# Define the triangular base vertices
for i in range(3):
    angle = i * 2 * math.pi / 3
    x = base_side_length * math.cos(angle)
    y = base_side_length * math.sin(angle)
    base_points.append(Base.Vector(x, y, 0))

# Create the base triangle edges
for i in range(3):
    lines.append(Part.makePolygon([base_points[i], base_points[(i+1)%3]]))

# Define the apex of the pyramid
apex = Base.Vector(0, 0, height)

# Create lines from base to apex
for i in range(3):
    lines.append(Part.makePolygon([base_points[i], apex]))

# Create reinforcement levels
for h in reinforcement_heights:
    reinforcement_points = []
    scale_factor = 1 - (h / height)

    for i in range(3):
        angle = i * 2 * math.pi / 3
        x = scale_factor * base_side_length * math.cos(angle)
        y = scale_factor * base_side_length * math.sin(angle)
        reinforcement_points.append(Base.Vector(x, y, h))

    for i in range(3):
        lines.append(Part.makePolygon([reinforcement_points[i], reinforcement_points[(i+1)%3]]))

    if h == reinforcement_heights[0]:
        for i in range(3):
            lines.append(Part.makePolygon([base_points[i], reinforcement_points[i]]))
        for i in range(3):
            next_level_point = Base.Vector(
                (1 - reinforcement_heights[1]/height) * base_side_length * math.cos(i * 2 * math.pi / 3),
                (1 - reinforcement_heights[1]/height) * base_side_length * math.sin(i * 2 * math.pi / 3),
                reinforcement_heights[1]
            )
            lines.append(Part.makePolygon([reinforcement_points[i], next_level_point]))
    else:
        for i in range(3):
            lines.append(Part.makePolygon([reinforcement_points[i], apex]))

    for i in range(3):
        if h == reinforcement_heights[0]:
            lines.append(Part.makePolygon([base_points[i], reinforcement_points[(i+1)%3]]))
        else:
            prev_level_point = Base.Vector(
                (1 - reinforcement_heights[0]/height) * base_side_length * math.cos(i * 2 * math.pi / 3),
                (1 - reinforcement_heights[0]/height) * base_side_length * math.sin(i * 2 * math.pi / 3),
                reinforcement_heights[0]
            )
            lines.append(Part.makePolygon([prev_level_point, reinforcement_points[(i+1)%3]]))

# Create the truss structure
truss_structure = Part.makeCompound(lines)

# Create solid beams for the truss
solid_beams = []
for edge in truss_structure.Edges:
    circle = Part.makeCircle(beam_radius, edge.valueAt(0), edge.tangentAt(0))
    circle_face = Part.Face(Part.Wire(circle))
    beam = circle_face.extrude(edge.valueAt(edge.LastParameter) - edge.valueAt(0))
    solid_beams.append(beam)

if solid_beams:
    truss_solid = solid_beams[0].multiFuse(solid_beams[1:])
    truss_obj = doc.addObject("Part::Feature", "PyramidalTruss")
    truss_obj.Shape = truss_solid
    doc.recompute()
else:
    App.Console.PrintError("Error: No beams were created\n")

# =========== Set up FEM analysis ===========
analysis = ObjectsFem.makeAnalysis(doc, "Analysis")
solver = ObjectsFem.makeSolverCalculix(doc, "SolverCalculix")

try:
    if hasattr(solver, "SolverType"):
        solver.SolverType = "static"
    if hasattr(solver, "GeometricalNonlinearity"):
        solver.GeometricalNonlinearity = "linear"
    if hasattr(solver, "ThermoMechSteadyState"):
        solver.ThermoMechSteadyState = False
    if hasattr(solver, "MaterialNonlinearity"):
        solver.MaterialNonlinearity = "none"
    if hasattr(solver, "IterationsControlParameterTimeUse"):
        solver.IterationsControlParameterTimeUse = False
except:
    print("Note: Some solver properties couldn't be set - using defaults")

analysis.addObject(solver)

# Define material properties
material = ObjectsFem.makeMaterialSolid(doc, "Material")
mat = material.Material
mat['Name'] = "Steel"
mat['YoungsModulus'] = "210000 MPa"
mat['PoissonRatio'] = "0.30"
mat['Density'] = "7900 kg/m^3"
material.Material = mat
analysis.addObject(material)

# Create and add FEM mesh
try:
    mesh = ObjectsFem.makeMeshGmsh(doc, "FEMMeshGmsh")
    mesh.Part = truss_obj
    mesh.CharacteristicLengthMax = 0.1
    mesh.CharacteristicLengthMin = 0.001
    mesh.Algorithm3D = "Delaunay"
    doc.recompute()
    analysis.addObject(mesh)
except Exception as e:
    App.Console.PrintError(f"Gmsh mesher creation failed: {e}\n")

# Set material references
try:
    solid_refs = [f"Solid{i+1}" for i, solid in enumerate(truss_obj.Shape.Solids)]
    if solid_refs:
        material.References = [(truss_obj, solid_refs)]
    else:
        App.Console.PrintError("No solids found in the truss object\n")
        print("Note: Material assignment should be done manually in GUI")
except Exception as e:
    App.Console.PrintError(f"Could not set material references: {e}\n")
    print("Note: Material assignment should be done manually in GUI")

# =========== Constraints ===========
# Fixed constraint
fixed_constraint = ObjectsFem.makeConstraintFixed(doc, "FixedConstraint")
fixed_vertex_names = []

for point in base_points:
    for i, vertex in enumerate(truss_obj.Shape.Vertexes):
        if (point - vertex.Point).Length < tolerance:
            fixed_vertex_names.append(f"Vertex{i+1}")
            break

fixed_constraint.References = [(truss_obj, name) for name in fixed_vertex_names]
analysis.addObject(fixed_constraint)

# Force constraint
force_constraint = ObjectsFem.makeConstraintForce(doc, "ForceConstraint")
force_vertex_name = None
for i, vertex in enumerate(truss_obj.Shape.Vertexes):
    if (apex - vertex.Point).Length < tolerance:
        force_vertex_name = f"Vertex{i+1}"
        break

if force_vertex_name:
    force_constraint.References = [(truss_obj, force_vertex_name)]
    try:
        # For newer FreeCAD versions
        force_constraint.Direction = (0, 0, -1)  # As a tuple instead of Vector
        force_constraint.Force = int(5000.0)  # Cast to int
    except Exception as e:
        try:
            # Alternative approach for some FreeCAD versions
            force_constraint.DirectionVector = (0, 0, -1)
            force_constraint.Force = int(5000.0)  # Cast to int
        except Exception as e2:
            App.Console.PrintError(f"Could not set force constraint properties: {e2}\n")
            print("Note: Force constraint may need to be set manually in GUI")
    analysis.addObject(force_constraint)

doc.recompute()

print("FEM analysis setup complete!")
print("To run the analysis in FreeCAD 1.0.0:")
print("1. Select the analysis object in the tree view")
print("2. Use the 'Solve' button in the task panel or menu")
print("3. After solving, right-click on 'SolverCalculix' and select 'Show result'")

# Save the document
doc.saveAs("/tmp/pyramidal_truss_analysis.FCStd")
