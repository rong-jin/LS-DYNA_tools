import gmsh
import sys

# 初始化
gmsh.initialize()
gmsh.model.add("structured_butterfly_mesh")

# 【重要】使用内置 Geo 内核 (而非 OCC)
# Geo 内核允许我们完全手动控制点线的拓扑连接，保证网格绝对结构化
geo = gmsh.model.geo
mesh = gmsh.model.geo.mesh

# ==========================================
# 1. 参数设置 (对应你的 .geo 变量)
# ==========================================
# 几何尺寸
Lx = 5.08
Ly = 5.08
t  = 0.635   # 厚度
ax = 1.5    # 核心半长 (core half-size)
ay = 1.5    # 核心半宽

# 网格控制参数
NxCore = 100   # 核心区域 X 方向【单元数】 (原代码是节点数，这里我习惯写单元数)
NyCore = 100   # 核心区域 Y 方向【单元数】
NLayers = 15  # 从核心到边缘的过渡【单元数】
Nz = 21        # 厚度方向【单元数】
rGrad = 1.05   # 渐变比率 (越往外越稀疏)

# Gmsh 的 TransfiniteCurve 需要的是【节点数】 = 单元数 + 1
n_core_x = NxCore + 1
n_core_y = NyCore + 1
n_layers = NLayers + 1
n_z = Nz + 1

# ==========================================
# 2. 定义几何点 (Points)
# ==========================================
# 外部矩形 (A, B, C, D)
pA = geo.addPoint(-Lx/2, -Ly/2, 0)
pB = geo.addPoint( Lx/2, -Ly/2, 0)
pC = geo.addPoint( Lx/2,  Ly/2, 0)
pD = geo.addPoint(-Lx/2,  Ly/2, 0)

# 内部核心矩形 (I, J, K, L)
pI = geo.addPoint(-ax, -ay, 0)
pJ = geo.addPoint( ax, -ay, 0)
pK = geo.addPoint( ax,  ay, 0)
pL = geo.addPoint(-ax,  ay, 0)

# ==========================================
# 3. 定义线 (Lines) - 构建 5 个区域
# ==========================================
# --- 核心回环 ---
lIJ = geo.addLine(pI, pJ)
lJK = geo.addLine(pJ, pK)
lKL = geo.addLine(pK, pL)
lLI = geo.addLine(pL, pI)

# --- 外部回环 ---
lAB = geo.addLine(pA, pB)
lBC = geo.addLine(pB, pC)
lCD = geo.addLine(pC, pD)
lDA = geo.addLine(pD, pA)

# --- 连接线 (Spokes) ---
mAI = geo.addLine(pA, pI)
mBJ = geo.addLine(pB, pJ)
mCK = geo.addLine(pC, pK)
mDL = geo.addLine(pD, pL)

# ==========================================
# 4. Transfinite 网格控制 (关键步骤)
# ==========================================

# 1. 核心区域边 (均匀分布)
for line in [lIJ, lKL, lAB, lCD]:
    mesh.setTransfiniteCurve(line, n_core_x)

for line in [lJK, lLI, lBC, lDA]:
    mesh.setTransfiniteCurve(line, n_core_y)

# 2. 径向连接线 (渐变分布)
# setTransfiniteCurve(tag, numNodes, meshType, coeff)
# "Progression" 1.3 表示每一个网格比前一个大 1.3 倍 (由密变稀)
# 注意：方向很重要。线是从 外->内 还是 内->外 定义的？
# mAI 是 A(-5)->I(-2)，是从外向内。
# 如果我们要“中间密，周围稀”，且线是从外向内画的，那么靠近 I 的网格应该小。
# Progression > 1 表示后一个比前一个大。
# 所以我们需要 Progression < 1 (比如 1/1.3) 或者反转系数。
prog_val = 1.0 / rGrad 

for line in [mAI, mBJ, mCK, mDL]:
    mesh.setTransfiniteCurve(line, n_layers, "Progression", prog_val)

# ==========================================
# 5. 定义面 (Surfaces) 并强制结构化
# ==========================================
# 定义一个辅助函数来简化操作
def make_patch(lines, corners):
    cl = geo.addCurveLoop(lines)
    s = geo.addPlaneSurface([cl])
    # 强制设为结构化面 (Transfinite)
    mesh.setTransfiniteSurface(s, cornerTags=corners)
    # 强制合并为四边形 (Recombine)
    mesh.setRecombine(2, s)
    return s

# 1. Core Patch (中间)
s_core = make_patch([lIJ, lJK, lKL, lLI], [pI, pJ, pK, pL])

# 2. South Patch (下) - 注意线的方向必须首尾相接
s_s = make_patch([lAB, mBJ, -lIJ, -mAI], [pA, pB, pJ, pI])

# 3. East Patch (右)
s_e = make_patch([lBC, mCK, -lJK, -mBJ], [pB, pC, pK, pJ])

# 4. North Patch (上)
s_n = make_patch([lCD, mDL, -lKL, -mCK], [pC, pD, pL, pK])

# 5. West Patch (左)
s_w = make_patch([lDA, mAI, -lLI, -mDL], [pD, pA, pI, pL])

# 同步几何数据
geo.synchronize()

# ==========================================
# 6. 拉伸为 3D (Extrude) 并区分 Part
# ==========================================

# 为了给 LS-DYNA 不同的 PID，我们分开拉伸
# 拉伸参数: (dim, tag), x, y, z, numElements, heights, recombine
# recombine=True 确保生成六面体

# Part 1: Core
ext_core = geo.extrude([(2, s_core)], 0, 0, t, numElements=[Nz], recombine=True)
vol_core = ext_core[1][1] # 获取生成的 Volume Tag

# Part 2: Outer (四个面一起拉伸)
outer_surfaces = [(2, s_s), (2, s_e), (2, s_n), (2, s_w)]
ext_outer = geo.extrude(outer_surfaces, 0, 0, t, numElements=[Nz], recombine=True)
# 提取所有生成的 Volume Tag (每组结果中 index 1 是 volume)
vols_outer = [item[1] for item in ext_outer if item[0] == 3]

geo.synchronize()

# ==========================================
# 7. 定义 Physical Groups (LS-DYNA Parts)
# ==========================================
# 这里的 Tag 1 和 2 就是 LS-DYNA 里的 Part ID
gmsh.model.addPhysicalGroup(3, [vol_core], 1, name="Center_Fine")
gmsh.model.addPhysicalGroup(3, vols_outer, 2, name="Outer_Coarse")

# ==========================================
# 8. 导出
# ==========================================
gmsh.model.mesh.generate(3)

# 使用 .key 后缀确保格式正确
output_file = "Structured_Butterfly_mesh.key"
gmsh.write(output_file)

print(f"完成！已生成结构化网格: {output_file}")
print("包含 Part 1 (中间) 和 Part 2 (周围)")

gmsh.finalize()