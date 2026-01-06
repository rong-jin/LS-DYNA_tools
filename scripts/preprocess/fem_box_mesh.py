import os

# ================= Configuration Section =================
output_filename = "fem_box_solid.k"

# 1. Geometry (Matches Shape Mesher PMin/PMax)
x_min, x_max = -2.54, 2.54
y_min, y_max = -2.54, 2.54
z_min, z_max = -0.635, 0.0

# 2. Mesh Density Settings
# In FEM, we define the Number of ELEMENTS (not particles).
# Note: Number of Nodes = Number of Elements + 1
# To match your SPH density of 111 particles, we usually use 110 elements (resulting in 111 nodes).
num_elem_x = 202
num_elem_y = 202
num_elem_z = 25

# Option: Calculate by Size (Uncomment lines below to use "Size" mode like the screenshot)
# target_size = 0.025
# num_elem_x = int((x_max - x_min) / target_size)
# num_elem_y = int((y_max - y_min) / target_size)
# num_elem_z = int((z_max - z_min) / target_size)

# 3. ID Settings
part_id = 1000001
start_nid = 1000001
start_eid = 1000001

# ================= Helper Functions =================

def chdir_to_script_dir(verbose: bool = True) -> str:
    """Sets CWD to script location."""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        if os.path.isdir(script_dir):
            os.chdir(script_dir)
            if verbose: print(f"[info] CWD set to: {script_dir}")
    except:
        pass

# ================= Main Logic =================

def generate_fem_box():
    # 1. Calculate Node Grid Dimensions
    # Nodes exist at the corners of elements
    num_node_x = num_elem_x + 1
    num_node_y = num_elem_y + 1
    num_node_z = num_elem_z + 1
    
    # Calculate Element Size (dx, dy, dz)
    dx = (x_max - x_min) / num_elem_x
    dy = (y_max - y_min) / num_elem_y
    dz = (z_max - z_min) / num_elem_z
    
    print(f"--- FEM Box Generation ---")
    print(f"Geometry: [{x_min}, {x_max}] x [{y_min}, {y_max}] x [{z_min}, {z_max}]")
    print(f"Elements: {num_elem_x} x {num_elem_y} x {num_elem_z} (Total Elems: {num_elem_x*num_elem_y*num_elem_z})")
    print(f"Nodes:    {num_node_x} x {num_node_y} x {num_node_z} (Total Nodes: {num_node_x*num_node_y*num_node_z})")
    
    # 2. Generate Nodes & Map IDs
    # We use a 3D dictionary/array to store Node IDs so elements can find them later.
    # Mapping: node_map[(i, j, k)] = NodeID
    node_map = {}
    
    current_nid = start_nid
    
    # Use lists to buffer output for speed
    node_lines = []
    element_lines = []
    
    print("Generating Nodes (Column-First: X->Y->Z)...")
    
    # Loop Order: X (Outer) -> Y (Middle) -> Z (Inner)
    # This creates nodes column by column (Z-fastest), matching your SPH preference.
    for i in range(num_node_x):
        x_pos = x_min + i * dx
        for j in range(num_node_y):
            y_pos = y_min + j * dy
            for k in range(num_node_z):
                z_pos = z_min + k * dz
                
                # Store coordinates and ID
                # Standard Format: NID, X, Y, Z (Large Format 16 chars usually safer for small floats)
                node_lines.append(f"{current_nid:8d}{x_pos:16.6f}{y_pos:16.6f}{z_pos:16.6f}\n")
                
                # Map logical grid index to real Node ID
                node_map[(i, j, k)] = current_nid
                current_nid += 1

    # 3. Generate Solid Elements
    print("Generating Solid Elements...")
    current_eid = start_eid
    
    # Loop through ELEMENTS (stop before the last node index)
    for i in range(num_elem_x):
        for j in range(num_elem_y):
            for k in range(num_elem_z):
                # Identify the 8 corners of the hexahedron
                # LS-DYNA connectivity: Bottom Face (n1-n4) -> Top Face (n5-n8)
                # Counter-Clockwise numbering
                
                # Bottom Face (k)
                n1 = node_map[(i,   j,   k)]
                n2 = node_map[(i,   j+1, k)] # Note: Order depends on local coord system, usually standard is:
                                             # 1(0,0,0), 2(1,0,0), 3(1,1,0), 4(0,1,0) - this varies by solver convention
                                             # Let's use the robust standard right-hand rule order:
                
                # Correct Standard Hex Order:
                # n1(i, j, k)   -> n2(i+1, j, k)   -> n3(i+1, j+1, k) -> n4(i, j+1, k)
                # n5(i, j, k+1) -> n6(i+1, j, k+1) -> n7(i+1, j+1, k+1) -> n8(i, j+1, k+1)
                
                # WAIT: Because we generate nodes X->Y->Z (Column First), we must simply lookup indices correctly.
                
                # Vertices coordinates in grid:
                p1 = (i,   j,   k)
                p2 = (i+1, j,   k) # +X
                p3 = (i+1, j+1, k) # +X +Y
                p4 = (i,   j+1, k) # +Y
                
                p5 = (i,   j,   k+1) # Above p1
                p6 = (i+1, j,   k+1) # Above p2
                p7 = (i+1, j+1, k+1) # Above p3
                p8 = (i,   j+1, k+1) # Above p4
                
                # Get IDs
                n1, n2, n3, n4 = node_map[p1], node_map[p2], node_map[p3], node_map[p4]
                n5, n6, n7, n8 = node_map[p5], node_map[p6], node_map[p7], node_map[p8]
                
                # *ELEMENT_SOLID format: EID, PID, N1, N2, N3, N4, N5, N6, N7, N8
                element_lines.append(f"{current_eid:8d}{part_id:8d}{n1:8d}{n2:8d}{n3:8d}{n4:8d}{n5:8d}{n6:8d}{n7:8d}{n8:8d}\n")
                current_eid += 1

    # 4. Write to File
    with open(output_filename, 'w') as f:
        f.write("*KEYWORD\n")
        
        # Write Nodes
        f.write("*NODE\n")
        f.writelines(node_lines)
        
        # Write Elements
        f.write("*ELEMENT_SOLID\n")
        f.writelines(element_lines)
        
        f.write("*END\n")
        
    print(f"Done! File saved to: {output_filename}")

if __name__ == "__main__":
    chdir_to_script_dir()
    generate_fem_box()