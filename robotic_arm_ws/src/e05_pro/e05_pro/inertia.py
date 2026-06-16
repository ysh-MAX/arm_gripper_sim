import numpy as np
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import os

def validate_inertia(mass, ixx, iyy, izz, ixy=0, ixz=0, iyz=0):
    inertia = np.array([[ixx, ixy, ixz],
                        [ixy, iyy, iyz],
                        [ixz, iyz, izz]])
    eigenvalues = np.linalg.eigvals(inertia)
    warn = False
    # 极小阈值防止浮点误差误报
    if any(e <= 1e-12 for e in eigenvalues):
        print(f"  ❌ 惯性矩阵不正定，特征值：{eigenvalues.round(6)}")
        warn = True
    # 惯性三角不等式校验
    cond1 = (ixx + iyy) < izz - 1e-12
    cond2 = (ixx + izz) < iyy - 1e-12
    cond3 = (iyy + izz) < ixx - 1e-12
    if cond1 or cond2 or cond3:
        print(f"  ❌ 不满足惯性三角不等式 | ixx={ixx:.6f}, iyy={iyy:.6f}, izz={izz:.6f}")
        warn = True
    if not warn:
        print("  ✅ 惯性参数完全合法")
    return not warn

def check_single_xacro(xacro_path):
    if not os.path.exists(xacro_path):
        print(f"\n❌ 文件不存在：{xacro_path}")
        return
    print(f"\n==================== 开始检测文件：{xacro_path} ====================")
    # xacro编译生成临时urdf
    with tempfile.NamedTemporaryFile(mode='w', suffix='.urdf', delete=False) as tmp_urdf:
        subprocess.run(["xacro", xacro_path], stdout=tmp_urdf, check=True)
        tmp_path = tmp_urdf.name
    try:
        tree = ET.parse(tmp_path)
        root = tree.getroot()
        link_list = root.findall("link")
        print(f"检测到连杆总数：{len(link_list)}")
        for link in link_list:
            link_name = link.attrib["name"]
            inertial = link.find("inertial")
            if inertial is None:
                print(f"\n【{link_name}】无 inertial 惯性标签")
                continue
            mass_elem = inertial.find("mass")
            inertia_elem = inertial.find("inertia")
            if mass_elem is None or inertia_elem is None:
                print(f"\n【{link_name}】惯性标签内容缺失")
                continue
            # 提取数值
            mass = float(mass_elem.attrib["value"])
            ixx = float(inertia_elem.attrib["ixx"])
            iyy = float(inertia_elem.attrib["iyy"])
            izz = float(inertia_elem.attrib["izz"])
            ixy = float(inertia_elem.attrib.get("ixy", 0))
            ixz = float(inertia_elem.attrib.get("ixz", 0))
            iyz = float(inertia_elem.attrib.get("iyz", 0))
            print(f"\n==== 连杆：{link_name} | 质量 = {mass:.4f} kg ====")
            validate_inertia(mass, ixx, iyy, izz, ixy, ixz, iyz)
    finally:
        os.unlink(tmp_path)

if __name__ == "__main__":
    # ====================== 在这里修改你自己的文件路径 ======================
    # 1. 机械臂主模型
    arm_xacro = "/home/yu/Desktop/robotic_arm_ws/src/e05_pro/urdf/E05_Pro.urdf.xacro"
    # 2. 抓手模型（一并检测）
    gripper_xacro = "/home/yu/Desktop/robotic_arm_ws/src/robotiq_2f_85_gripper_visualization/urdf/robotiq_arg2f_85_macro.xacro"

    gripp = "/home/yu/Desktop/robotic_arm_ws/src/robotiq_85_description/urdf/robotiq_85_gripper.urdf.xacro"

    # 批量检测两个文件
    check_single_xacro(arm_xacro)
    check_single_xacro(gripper_xacro)
    check_single_xacro(gripp)
    print("\n==================== 全部检测完成 ====================")