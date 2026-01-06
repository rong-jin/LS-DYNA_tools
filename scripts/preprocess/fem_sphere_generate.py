import math
import os

# ================= Configuration Section =================
output_filename = "fem_sphere.k"

# Geometry Parameters (Matches PrePost "Sphere Solid")
radius = 0.25
cx, cy, cz = 0.0, 0.0, 0.251

# Mesh Density (Matches "Density" in PrePost)
# Defines the number of element divisions along the RADIUS.
# Total elements along diameter will be roughly 2 * density.
density = 10 

# ID Settings
part_id = 1
start_nid = 1
start_eid = 1

# ================= Helper Functions =================

def chdir_to_script_dir():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        if os.path.isdir(script_dir):
            os.chdir(script_dir)
    except:
        pass

# ================= Generation Logic =================

def generate_hex_sphere():
    # 1. Define Logical Grid Size
    # We create a cube spanning [-1, 1] in normalized coordinates.
    # The grid has (2 * density) elements along each axis.
    N = density
    elements_per_side = 2 * N
    nodes_per_side = elements_per_side + 1
    
    print(f"--- FEM Sphere Generation ---")
    print(f"Radius: {radius}, Center: ({cx}, {cy}, {cz})")
    print(f"Density: {density} (Grid: {elements_per_side}x{elements_per_side}x{elements_per_side})")
    
    nodes = {}    # Map: (i, j, k) -> NodeID
    elements = [] # List of tuples: (eid, pid, n1, n2, n3, n4, n5, n6, n7, n8)
    
    current_nid = start_nid
    
    # 2. Generate Nodes
    # Loop through logical grid points
    for i in range(nodes_per_side):
        for j in range(nodes_per_side):
            for k in range(nodes_per_side):
                
                # Normalize coordinates to range [-1, 1]
                u = (i - N) / N
                v = (j - N) / N
                w = (k - N) / N
                
                # --- Cubed-Sphere Mapping Formula ---
                # This maps a cube to a sphere while maintaining good element quality.
                # Formula: x' = x * sqrt(1 - y^2/2 - z^2/2 + y^2*z^2/3) ...
                
                x_s = u * math.sqrt(1.0 - (v**2)/2.0 - (w**2)/2.0 + (v**2 * w**2)/3.0)
                y_s = v * math.sqrt(1.0 - (u**2)/2.0 - (w**2)/2.0 + (u**2 * w**2)/3.0)
                z_s = w * math.sqrt(1.0 - (u**2)/2.0 - (v**2)/2.0 + (u**2 * v**2)/3.0)
                
                # Scale by Radius and Shift to Center
                x_real = cx + x_s * radius
                y_real = cy + y_s * radius
                z_real = cz + z_s * radius
                
                # Store node data
                nodes[(i, j, k)] = current_nid
                
                # (Optional) We could write to file immediately to save memory, 
                # but storing IDs in a dict is easier for connectivity.
                
                current_nid += 1
                
    # 3. Generate Elements (Hexahedrons)
    current_eid = start_eid
    
    for i in range(elements_per_side):
        for j in range(elements_per_side):
            for k in range(elements_per_side):
                # Define the 8 nodes of the hex element
                # LS-DYNA Node Ordering: Bottom Face (1-2-3-4), Top Face (5-6-7-8)
                
                n1 = nodes[(i,   j,   k)]
                n2 = nodes[(i+1, j,   k)]
                n3 = nodes[(i+1, j+1, k)]
                n4 = nodes[(i,   j+1, k)]
                
                n5 = nodes[(i,   j,   k+1)]
                n6 = nodes[(i+1, j,   k+1)]
                n7 = nodes[(i+1, j+1, k+1)]
                n8 = nodes[(i,   j+1, k+1)]
                
                elements.append((current_eid, part_id, n1, n2, n3, n4, n5, n6, n7, n8))
                current_eid += 1
                
    print(f"Generated {len(nodes)} Nodes and {len(elements)} Solid Elements.")

    # 4. Write to File
    with open(output_filename, 'w') as f:
        f.write("*KEYWORD\n")
        
        # Write Nodes
        f.write("*NODE\n")
        # Need to re-iterate or store coords. Let's recalculate coords to save memory if huge,
        # or just use the logic above. For simplicity, we regenerate coords here 
        # based on the ID map logic, or better: write inside the loop.
        # To keep code clean, let's just loop indices again for writing.
        
        nid_counter = start_nid
        for i in range(nodes_per_side):
            for j in range(nodes_per_side):
                for k in range(nodes_per_side):
                    u = (i - N) / N
                    v = (j - N) / N
                    w = (k - N) / N
                    
                    x_s = u * math.sqrt(1.0 - (v**2)/2.0 - (w**2)/2.0 + (v**2 * w**2)/3.0)
                    y_s = v * math.sqrt(1.0 - (u**2)/2.0 - (w**2)/2.0 + (u**2 * w**2)/3.0)
                    z_s = w * math.sqrt(1.0 - (u**2)/2.0 - (v**2)/2.0 + (u**2 * v**2)/3.0)
                    
                    x = cx + x_s * radius
                    y = cy + y_s * radius
                    z = cz + z_s * radius
                    
                    f.write(f"{nid_counter:8d}{x:16.6f}{y:16.6f}{z:16.6f}\n")
                    nid_counter += 1

        # Write Elements
        f.write("*ELEMENT_SOLID\n")
        for eid, pid, n1, n2, n3, n4, n5, n6, n7, n8 in elements:
            # Standard Format: EID, PID, N1, N2, N3, N4, N5, N6, N7, N8
            f.write(f"{eid:8d}{pid:8d}{n1:8d}{n2:8d}{n3:8d}{n4:8d}{n5:8d}{n6:8d}{n7:8d}{n8:8d}\n")
            
        f.write("*END\n")
        
    print(f"Done! File saved to: {output_filename}")

if __name__ == "__main__":
    chdir_to_script_dir()
    generate_hex_sphere()